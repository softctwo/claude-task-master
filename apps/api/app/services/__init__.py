"""Services layer."""
from app.services.base import CRUDService
from app.models import User, Project, Brief, PRD, Task, AgentRun, KnowledgeItem, AuditLog

user_service = CRUDService(User)
project_service = CRUDService(Project)
brief_service = CRUDService(Brief)
prd_service = CRUDService(PRD)
task_service = CRUDService(Task)
agent_run_service = CRUDService(AgentRun)
knowledge_service = CRUDService(KnowledgeItem)
audit_service = CRUDService(AuditLog)
