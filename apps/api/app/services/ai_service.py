"""AI Service — OpenAI integration for PRD generation, task extraction, and chat completion.

Uses OpenAI SDK v1.x with streaming support.
"""
import json
import os
import re
from typing import AsyncIterator, Optional, List, Dict, Any, Literal

from openai import AsyncOpenAI, APIError, RateLimitError
from pydantic import BaseModel, Field

from app.config import settings

# ────────────────────────────────
# OpenAI client
# ────────────────────────────────

_openai_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """Lazy initialization of OpenAI async client."""
    global _openai_client
    if _openai_client is None:
        api_key = getattr(settings, "openai_api_key", None) or os.environ.get("OPENAI_API_KEY")
        base_url = getattr(settings, "openai_base_url", None) or os.environ.get("OPENAI_BASE_URL")
        if not api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in environment or settings."
            )
        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        _openai_client = AsyncOpenAI(**client_kwargs)
    return _openai_client


# ────────────────────────────────
# Prompt Templates
# ────────────────────────────────

PRD_GENERATION_SYSTEM_PROMPT = """You are an expert product manager and technical writer. 
Your task is to generate a comprehensive, well-structured Product Requirements Document (PRD) 
from the provided brief. The PRD should be written in Markdown format and include all necessary 
sections for a development team to understand and implement the product.

Requirements:
- Use clear, professional language
- Include technical specifications where relevant
- Define acceptance criteria precisely
- Consider edge cases and constraints
- Structure the PRD with proper Markdown headings
- Output ONLY the PRD markdown content, no additional commentary"""

PRD_GENERATION_USER_TEMPLATE = """Please generate a complete PRD based on the following brief:

## Brief Information

**Title:** {title}

**Background:**
{background}

**Problem Statement:**
{problem_statement}

**Target Users:**
{target_users}

**Goals:**
{goals}

**Non-Goals:**
{non_goals}

**Scope:**
{scope}

**User Stories:**
{user_stories}

**Acceptance Criteria:**
{acceptance_criteria}

**Constraints:**
{constraints}

{extra_context_section}

Please generate a comprehensive PRD in Markdown format."""

TASK_EXTRACTION_SYSTEM_PROMPT = """You are a technical project manager specializing in task decomposition.
Your task is to analyze a PRD (Product Requirements Document) and extract a structured list of 
development tasks. Each task should be actionable, specific, and include relevant metadata.

Requirements:
- Break down the PRD into atomic, implementable tasks
- Assign appropriate priority levels (low, medium, high, critical)
- Identify dependencies between tasks
- Include test strategy hints where relevant
- Output ONLY valid JSON, no markdown formatting or commentary

Output format: A JSON array of task objects with these fields:
- title (string, required): Concise task title
- description (string, required): Detailed task description
- details (string, optional): Implementation details
- test_strategy (string, optional): Testing approach
- priority (string, enum: low|medium|high|critical): Task priority
- complexity_score (integer, 1-10): Estimated complexity
- dependencies (array of strings): Titles of tasks this depends on"""

TASK_EXTRACTION_USER_TEMPLATE = """Please extract structured tasks from the following PRD:

{prd_content}

Extract all development tasks and return them as a JSON array."""

CHAT_SYSTEM_PROMPT = """You are Resoft AI, an expert software development assistant integrated into 
the Resoft AI Delivery Studio platform. You help teams with product development, technical decisions, 
code review, architecture design, and project management.

Guidelines:
- Be concise but thorough
- Provide actionable advice
- Use technical terminology appropriately
- Consider best practices and industry standards
- When unsure, ask clarifying questions"""


# ────────────────────────────────
# Schemas
# ────────────────────────────────

class GeneratedTask(BaseModel):
    """Schema for a task extracted from PRD content."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    dependencies: List[str] = Field(default_factory=list)


class PRDGenerationResult(BaseModel):
    """Result of PRD generation."""
    content_markdown: str
    model: str
    tokens_used: Optional[int] = None


class TaskGenerationResult(BaseModel):
    """Result of task generation from PRD."""
    tasks: List[GeneratedTask]
    model: str
    count: int


class ChatMessage(BaseModel):
    """A single chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionResult(BaseModel):
    """Result of chat completion."""
    content: str
    model: str
    tokens_used: Optional[int] = None


# ────────────────────────────────
# Helper functions
# ────────────────────────────────

def _format_list(items: Optional[List[str]], default: str = "N/A") -> str:
    """Format a list of strings for prompt inclusion."""
    if not items:
        return default
    return "\n".join(f"- {item}" for item in items)


def _build_prd_generation_prompt(
    title: str,
    background: Optional[str] = None,
    problem_statement: Optional[str] = None,
    target_users: Optional[str] = None,
    goals: Optional[List[str]] = None,
    non_goals: Optional[List[str]] = None,
    scope: Optional[str] = None,
    user_stories: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    constraints: Optional[str] = None,
    extra_context: Optional[str] = None,
) -> str:
    """Build the user prompt for PRD generation."""
    extra_context_section = ""
    if extra_context:
        extra_context_section = f"\n**Extra Context:**\n{extra_context}\n"

    return PRD_GENERATION_USER_TEMPLATE.format(
        title=title or "Untitled",
        background=background or "N/A",
        problem_statement=problem_statement or "N/A",
        target_users=target_users or "N/A",
        goals=_format_list(goals),
        non_goals=_format_list(non_goals),
        scope=scope or "N/A",
        user_stories=_format_list(user_stories),
        acceptance_criteria=_format_list(acceptance_criteria),
        constraints=constraints or "N/A",
        extra_context_section=extra_context_section,
    )


def _extract_json_from_markdown(text: str) -> str:
    """Extract JSON content from markdown code blocks or raw text."""
    # Try to find JSON in code blocks
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block_match:
        return code_block_match.group(1).strip()
    # Try to find JSON array directly
    array_match = re.search(r"(\[\s*\{[\s\S]*\}\s*\])", text)
    if array_match:
        return array_match.group(1).strip()
    return text.strip()


# ────────────────────────────────
# Core AI functions
# ────────────────────────────────

async def generate_prd_from_brief(
    title: str,
    background: Optional[str] = None,
    problem_statement: Optional[str] = None,
    target_users: Optional[str] = None,
    goals: Optional[List[str]] = None,
    non_goals: Optional[List[str]] = None,
    scope: Optional[str] = None,
    user_stories: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    constraints: Optional[str] = None,
    extra_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: Optional[int] = 8000,
) -> PRDGenerationResult:
    """Generate a PRD from brief content using OpenAI.
    
    Args:
        title: Brief title
        background: Background information
        problem_statement: Problem to solve
        target_users: Target user personas
        goals: List of goals
        non_goals: List of non-goals
        scope: Scope description
        user_stories: List of user stories
        acceptance_criteria: List of acceptance criteria
        constraints: Constraints and limitations
        extra_context: Additional context for the AI
        model: OpenAI model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        PRDGenerationResult with generated markdown content
        
    Raises:
        RuntimeError: If OpenAI client is not configured
        APIError: If OpenAI API call fails
    """
    client = get_openai_client()
    user_prompt = _build_prd_generation_prompt(
        title=title,
        background=background,
        problem_statement=problem_statement,
        target_users=target_users,
        goals=goals,
        non_goals=non_goals,
        scope=scope,
        user_stories=user_stories,
        acceptance_criteria=acceptance_criteria,
        constraints=constraints,
        extra_context=extra_context,
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PRD_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content or ""
    # Clean up any potential wrapper text
    content = content.strip()
    
    return PRDGenerationResult(
        content_markdown=content,
        model=model,
        tokens_used=response.usage.total_tokens if response.usage else None,
    )


async def generate_prd_from_brief_stream(
    title: str,
    background: Optional[str] = None,
    problem_statement: Optional[str] = None,
    target_users: Optional[str] = None,
    goals: Optional[List[str]] = None,
    non_goals: Optional[List[str]] = None,
    scope: Optional[str] = None,
    user_stories: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    constraints: Optional[str] = None,
    extra_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: Optional[int] = 8000,
) -> AsyncIterator[str]:
    """Stream-generate a PRD from brief content using OpenAI SSE.
    
    Yields chunks of markdown content as they are generated.
    """
    client = get_openai_client()
    user_prompt = _build_prd_generation_prompt(
        title=title,
        background=background,
        problem_statement=problem_statement,
        target_users=target_users,
        goals=goals,
        non_goals=non_goals,
        scope=scope,
        user_stories=user_stories,
        acceptance_criteria=acceptance_criteria,
        constraints=constraints,
        extra_context=extra_context,
    )

    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PRD_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def generate_tasks_from_prd(
    prd_content: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
    max_tokens: Optional[int] = 4000,
) -> TaskGenerationResult:
    """Generate structured tasks from PRD content using OpenAI.
    
    Args:
        prd_content: The PRD markdown content
        model: OpenAI model to use
        temperature: Sampling temperature (lower for more deterministic output)
        max_tokens: Maximum tokens to generate
        
    Returns:
        TaskGenerationResult with list of structured tasks
        
    Raises:
        RuntimeError: If OpenAI client is not configured
        APIError: If OpenAI API call fails
        ValueError: If response cannot be parsed as valid JSON
    """
    client = get_openai_client()
    user_prompt = TASK_EXTRACTION_USER_TEMPLATE.format(prd_content=prd_content)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": TASK_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    
    # Extract JSON from response
    json_str = _extract_json_from_markdown(content)
    
    try:
        data = json.loads(json_str)
        # Handle both { "tasks": [...] } and direct array
        if isinstance(data, dict):
            tasks_data = data.get("tasks", data.get("items", []))
        elif isinstance(data, list):
            tasks_data = data
        else:
            tasks_data = []
        
        tasks = [GeneratedTask.model_validate(t) for t in tasks_data]
    except (json.JSONDecodeError, Exception) as e:
        raise ValueError(f"Failed to parse AI response as tasks: {e}. Raw: {content[:500]}")

    return TaskGenerationResult(
        tasks=tasks,
        model=model,
        count=len(tasks),
    )


async def chat_completion(
    messages: List[ChatMessage],
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: Optional[int] = 4000,
    stream: bool = False,
) -> ChatCompletionResult | AsyncIterator[str]:
    """General chat completion with the AI assistant.
    
    Args:
        messages: List of chat messages
        model: OpenAI model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stream: Whether to stream the response
        
    Returns:
        ChatCompletionResult if stream=False, AsyncIterator[str] if stream=True
    """
    client = get_openai_client()
    
    # Prepend system message if not present
    chat_messages = []
    has_system = any(m.role == "system" for m in messages)
    if not has_system:
        chat_messages.append({"role": "system", "content": CHAT_SYSTEM_PROMPT})
    
    for msg in messages:
        chat_messages.append({"role": msg.role, "content": msg.content})

    if stream:
        stream_response = await client.chat.completions.create(
            model=model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async def _stream_generator():
            async for chunk in stream_response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        
        return _stream_generator()
    else:
        response = await client.chat.completions.create(
            model=model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content or ""
        return ChatCompletionResult(
            content=content,
            model=model,
            tokens_used=response.usage.total_tokens if response.usage else None,
        )


# ────────────────────────────────
# Health check
# ────────────────────────────────

async def check_ai_health() -> Dict[str, Any]:
    """Check if AI service is properly configured and reachable."""
    try:
        client = get_openai_client()
        # Try a simple models list call
        models = await client.models.list()
        return {
            "status": "ok",
            "configured": True,
            "available_models": len(models.data),
        }
    except Exception as e:
        return {
            "status": "error",
            "configured": False,
            "error": str(e),
        }
