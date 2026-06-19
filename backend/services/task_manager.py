from sqlalchemy.orm import Session
from ..models.task import Task
from ..core.database import SessionLocal
import json

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_task(db, user_id: int, filename: str, t_min: float, t_max: float, threshold: float):
    # Если сессия не передана, создаём свою
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    task = Task(
        user_id=user_id,
        filename=filename,
        t_min=t_min,
        t_max=t_max,
        threshold=threshold,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    if close_db:
        db.close()
    return task

def update_task_status(
    task_id: int,
    status: str,
    celery_task_id: str = None,
    result_image: str = None,
    max_map: str = None,
    shape: tuple = None,
    error_message: str = None
):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        task.status = status
        if celery_task_id:
            task.celery_task_id = celery_task_id
        if result_image:
            task.result_image = result_image
        if max_map:
            task.max_map = max_map
        if shape:
            task.shape = json.dumps(shape)
        if error_message:
            task.error_message = error_message
        db.commit()
        db.refresh(task)
    finally:
        db.close()

def get_task(db, task_id: int, user_id: int):
    # Если сессия не передана, создаём свою
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if close_db:
        db.close()
    return task