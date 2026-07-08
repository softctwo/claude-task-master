from celery import shared_task


@shared_task(bind=True)
def parse_prd_task(self, project_id: str, prd_content: str):
    """调用 Taskmaster 解析 PRD 生成任务"""
    # TODO: 调用 Taskmaster Adapter
    return {"status": "completed", "project_id": project_id}


@shared_task(bind=True)
def expand_task_task(self, project_id: str, task_id: str):
    """调用 Taskmaster 拆解任务"""
    # TODO: 调用 Taskmaster Adapter
    return {"status": "completed", "task_id": task_id}


@shared_task(bind=True)
def analyze_complexity_task(self, project_id: str):
    """分析任务复杂度"""
    # TODO: 调用 Taskmaster Adapter
    return {"status": "completed", "project_id": project_id}


@shared_task(bind=True)
def sync_taskmaster_task(self, project_id: str):
    """同步 Taskmaster 任务数据"""
    # TODO: 调用 Taskmaster Adapter
    return {"status": "completed", "project_id": project_id}
