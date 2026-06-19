from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..services.task_manager import create_task, get_task
from ..services.processor import recolor_image
from ..tasks import process_video_task
import json

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    t_min: float = Form(625.0),
    t_max: float = Form(1526.1),
    threshold: float = Form(900.0),
):
    if not file.filename.endswith('.ravi'):
        raise HTTPException(status_code=400, detail="Файл должен иметь расширение .ravi")
    contents = await file.read()
    # Создаём задачу без привязки к пользователю (user_id = 1)
    task = create_task(None, 1, file.filename, t_min, t_max, threshold)
    process_video_task.delay(task.id, contents, t_min, t_max, threshold)
    return {"task_id": task.id, "status": "pending"}

@router.get("/status/{task_id}")
def get_task_status(task_id: int):
    # Передаём user_id = 1, чтобы get_task работал
    task = get_task(None, task_id, 1)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    response = {
        "task_id": task.id,
        "status": task.status,
        "filename": task.filename,
        "t_min": task.t_min,
        "t_max": task.t_max,
        "threshold": task.threshold,
        "created_at": task.created_at.isoformat(),
    }
    if task.status == "completed":
        response["result_image"] = task.result_image
        response["shape"] = json.loads(task.shape) if task.shape else None
    if task.error_message:
        response["error"] = task.error_message
    return response

@router.post("/recolor")
def recolor_task(
    task_id: int = Form(...),
    threshold: float = Form(...),
):
    task = get_task(None, task_id, 1)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed" or not task.max_map or not task.shape:
        raise HTTPException(status_code=400, detail="Task not completed or missing data")
    shape = json.loads(task.shape)
    new_image = recolor_image(task.max_map, tuple(shape), task.t_min, task.t_max, threshold)
    task.threshold = threshold
    task.result_image = new_image
    # Здесь нужно сохранить изменения в БД – если get_task не использует сессию, это проблема
    # Временно просто вернём новую картинку без сохранения
    return {"task_id": task.id, "result_image": new_image, "threshold": threshold}