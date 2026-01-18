import os
import shutil
from fastapi import UploadFile
from app.config import settings

def ensure_upload_dir():
    """Ensure upload directory exists"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

def save_task_file(task_id: int, file: UploadFile) -> str:
    """Save uploaded task file and return the file path"""
    ensure_upload_dir()
    
    # Create filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"task_{task_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def delete_task_file(file_path: str):
    """Delete task file if exists"""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)