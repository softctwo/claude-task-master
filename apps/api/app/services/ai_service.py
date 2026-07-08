"""AI Service - OpenAI API 调用封装

提供：
- 从 Brief 生成 PRD
- 从 PRD 生成 Taskmaster 任务
- 通用 Chat Completion
"""
import json
import os
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI

from app.config import settings


# ────────────────────────────────
# OpenAI Client Setup
# ────────────────────────────────

_openai_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """获取或创建 OpenAI 异步客户端（单例）"""
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        _openai_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    return _openai_client


# ────────────────────────────────
# Pydantic Schemas
# ────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "gpt-4o"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BriefInput(BaseModel):
    title: str
    background: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users: Optional[str] = None
    goals: Optional[List[str]] = None
    non_goals: Optional[List[str]] = None
    scope: Optional[str] = None
    user_stories: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    constraints: Optional[str] = None
    related_docs: Optional[List[str]] = None
    related_code: Optional[List[str]] = None


class PRDOutput(BaseModel):
    content_markdown: str
    title: str
    summary: str
    sections: List[str]
    estimated_effort: Optional[str] = None
    risk_areas: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class TaskItem(BaseModel):
    title: str
    description: Optional[str] = None
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    dependencies: Optional[List[str]] = None


class TaskGenerationOutput(BaseModel):
    tasks: List[TaskItem]
    total_count: int
    estimated_total_effort: Optional[str] = None
    critical_path: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class StreamingChunk(BaseModel):
    content: str
    is_finished: bool = False


# ────────────────────────────────
# Prompt Templates
# ────────────────────────────────

PRD_GENERATION_PROMPT = """你是一位资深产品经理和架构师。请根据以下 Brief 内容生成一份专业的 PRD（Product Requirements Document）。

要求：
1. 使用 Markdown 格式
2. 包含以下章节：
   - 产品概述
   - 背景与问题陈述
   - 目标用户
   - 产品目标
   - 非目标（明确不做的事）
   - 功能需求（按优先级排序）
   - 用户故事
   - 验收标准
   - 技术约束与假设
   - 风险与缓解策略
   - 成功指标
3. 语言：中文
4. 输出应详细、具体、可执行

Brief 内容如下：
"""

TASK_GENERATION_PROMPT = """你是一位技术负责人和任务拆解专家。请根据以下 PRD 内容生成详细的开发任务列表。

要求：
1. 每个任务必须包含：标题、详细描述、测试策略、优先级（low/medium/high/critical）、复杂度评分（1-10）
2. 任务之间需要标注依赖关系
3. 识别关键路径
4. 估算总体工作量
5. 输出格式为 JSON

PRD 内容如下：
"""


# ────────────────────────────────
# Service Functions
# ────────────────────────────────

async def generate_prd_from_brief(
    brief: BriefInput,
    model: str = "gpt-4o",
    temperature: float = 0.5,
) -> PRDOutput:
    """从 Brief 生成 PRD

    Args:
        brief: Brief 输入数据
        model: 使用的 OpenAI 模型
        temperature: 温度参数

    Returns:
        PRDOutput: 生成的 PRD 内容
    """
    client = get_openai_client()

    # Build brief content
    brief_parts = [f"# {brief.title}\n"]
    if brief.background:
        brief_parts.append(f"## 背景\n{brief.background}\n")
    if brief.problem_statement:
        brief_parts.append(f"## 问题陈述\n{brief.problem_statement}\n")
    if brief.target_users:
        brief_parts.append(f"## 目标用户\n{brief.target_users}\n")
    if brief.goals:
        brief_parts.append(f"## 目标\n" + "\n".join(f"- {g}" for g in brief.goals) + "\n")
    if brief.non_goals:
        brief_parts.append(f"## 非目标\n" + "\n".join(f"- {g}" for g in brief.non_goals) + "\n")
    if brief.scope:
        brief_parts.append(f"## 范围\n{brief.scope}\n")
    if brief.user_stories:
        brief_parts.append(f"## 用户故事\n" + "\n".join(f"- {s}" for s in brief.user_stories) + "\n")
    if brief.acceptance_criteria:
        brief_parts.append(f"## 验收标准\n" + "\n".join(f"- {c}" for c in brief.acceptance_criteria) + "\n")
    if brief.constraints:
        brief_parts.append(f"## 约束\n{brief.constraints}\n")
    if brief.related_docs:
        brief_parts.append(f"## 相关文档\n" + "\n".join(f"- {d}" for d in brief.related_docs) + "\n")
    if brief.related_code:
        brief_parts.append(f"## 相关代码\n" + "\n".join(f"- {c}" for c in brief.related_code) + "\n")

    brief_content = "\n".join(brief_parts)

    messages = [
        ChatMessage(role="system", content=PRD_GENERATION_PROMPT),
        ChatMessage(role="user", content=brief_content),
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=[m.model_dump(exclude_none=True) for m in messages],
        temperature=temperature,
        max_tokens=8000,
    )

    content = response.choices[0].message.content or ""

    # Extract sections from markdown
    sections = []
    for line in content.split("\n"):
        if line.startswith("## ") or line.startswith("### "):
            sections.append(line.lstrip("# ").strip())

    # Extract summary (first paragraph after title)
    summary = ""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    summary = lines[j].strip()
                    break
            break

    # Extract risk areas
    risk_areas = []
    in_risk_section = False
    for line in content.split("\n"):
        if "风险" in line and line.startswith("##"):
            in_risk_section = True
            continue
        if in_risk_section and line.startswith("##"):
            break
        if in_risk_section and line.strip().startswith("-"):
            risk_areas.append(line.strip().lstrip("- ").strip())

    return PRDOutput(
        content_markdown=content,
        title=brief.title,
        summary=summary,
        sections=sections,
        estimated_effort=None,  # Could be extracted with more parsing
        risk_areas=risk_areas if risk_areas else None,
    )


async def generate_tasks_from_prd(
    prd_content: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> TaskGenerationOutput:
    """从 PRD 生成 Taskmaster 任务列表

    Args:
        prd_content: PRD Markdown 内容
        model: 使用的 OpenAI 模型
        temperature: 温度参数

    Returns:
        TaskGenerationOutput: 生成的任务列表
    """
    client = get_openai_client()

    system_prompt = TASK_GENERATION_PROMPT + """

请严格按照以下 JSON 格式输出：
{
    "tasks": [
        {
            "title": "任务标题",
            "description": "详细描述",
            "details": "实现细节",
            "test_strategy": "测试策略",
            "priority": "high",
            "complexity_score": 5,
            "dependencies": ["依赖任务标题1", "依赖任务标题2"]
        }
    ],
    "total_count": 10,
    "estimated_total_effort": "2周",
    "critical_path": ["关键路径任务1", "关键路径任务2"]
}
"""

    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=prd_content),
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=[m.model_dump(exclude_none=True) for m in messages],
        temperature=temperature,
        max_tokens=8000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from markdown code block
        import re
        json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = {}

    tasks = []
    for t in data.get("tasks", []):
        tasks.append(
            TaskItem(
                title=t.get("title", "Untitled"),
                description=t.get("description"),
                details=t.get("details"),
                test_strategy=t.get("test_strategy"),
                priority=t.get("priority", "medium"),
                complexity_score=t.get("complexity_score"),
                dependencies=t.get("dependencies"),
            )
        )

    return TaskGenerationOutput(
        tasks=tasks,
        total_count=data.get("total_count", len(tasks)),
        estimated_total_effort=data.get("estimated_total_effort"),
        critical_path=data.get("critical_path"),
    )


async def chat_completion(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse:
    """通用 Chat Completion 接口

    Args:
        request: 聊天完成请求

    Returns:
        ChatCompletionResponse: 聊天完成响应
    """
    client = get_openai_client()

    response = await client.chat.completions.create(
        model=request.model,
        messages=[m.model_dump(exclude_none=True) for m in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
        stream=request.stream,
    )

    if request.stream:
        # For streaming, we return the first chunk's content
        # In a real implementation, this would be an async generator
        content = ""
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        return ChatCompletionResponse(
            content=content,
            model=request.model,
            usage=None,
            finish_reason="stop",
        )

    content = response.choices[0].message.content or ""
    usage = None
    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return ChatCompletionResponse(
        content=content,
        model=response.model or request.model,
        usage=usage,
        finish_reason=response.choices[0].finish_reason,
    )


async def stream_chat_completion(
    request: ChatCompletionRequest,
):
    """流式 Chat Completion（异步生成器）

    Args:
        request: 聊天完成请求

    Yields:
        StreamingChunk: 流式响应块
    """
    client = get_openai_client()

    response = await client.chat.completions.create(
        model=request.model,
        messages=[m.model_dump(exclude_none=True) for m in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
        stream=True,
    )

    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield StreamingChunk(
                content=chunk.choices[0].delta.content,
                is_finished=chunk.choices[0].finish_reason is not None,
            )
        elif chunk.choices and chunk.choices[0].finish_reason:
            yield StreamingChunk(content="", is_finished=True)


async def summarize_text(
    text: str,
    model: str = "gpt-4o-mini",
    max_length: int = 200,
) -> str:
    """文本摘要

    Args:
        text: 需要摘要的文本
        model: 使用的模型
        max_length: 最大摘要长度

    Returns:
        str: 摘要文本
    """
    prompt = f"请用不超过 {max_length} 字总结以下内容：\n\n{text}"

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=prompt)],
        model=model,
        temperature=0.3,
        max_tokens=500,
    )

    response = await chat_completion(request)
    return response.content


async def analyze_code_complexity(
    code: str,
    language: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """分析代码复杂度

    Args:
        code: 代码内容
        language: 编程语言
        model: 使用的模型

    Returns:
        Dict: 复杂度分析结果
    """
    lang_hint = f"（语言：{language}）" if language else ""
    prompt = f"""请分析以下代码的复杂度{lang_hint}，并返回 JSON 格式：
{{
    "cyclomatic_complexity": "圈复杂度评估",
    "cognitive_complexity": "认知复杂度评估",
    "maintainability_score": "可维护性评分（1-10）",
    "issues": ["发现的问题列表"],
    "recommendations": ["改进建议"]
}}

代码：
```
{code}
```
"""

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=prompt)],
        model=model,
        temperature=0.2,
        max_tokens=2000,
    )

    response = await chat_completion(request)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "error": "Failed to parse analysis",
            "raw_response": response.content,
        }

    return result


async def generate_commit_message(
    diff: str,
    model: str = "gpt-4o-mini",
) -> str:
    """根据代码变更生成提交消息

    Args:
        diff: Git diff 内容
        model: 使用的模型

    Returns:
        str: 生成的提交消息
    """
    prompt = f"""请根据以下代码变更生成一个简洁、专业的 Git 提交消息（使用中文）。
格式要求：
- 标题行：不超过 50 字，使用动词开头
- 正文（可选）：详细描述变更内容

代码变更：
```diff
{diff[:4000]}  # Limit diff size
```
"""

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=prompt)],
        model=model,
        temperature=0.3,
        max_tokens=300,
    )

    response = await chat_completion(request)
    return response.content.strip()


# ────────────────────────────────
# Health Check
# ────────────────────────────────

async def check_ai_service_health() -> Dict[str, Any]:
    """检查 AI 服务健康状态"""
    try:
        client = get_openai_client()
        # Try a simple completion to verify connectivity
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        return {
            "status": "healthy",
            "model": response.model,
            "provider": "openai",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "provider": "openai",
        }
