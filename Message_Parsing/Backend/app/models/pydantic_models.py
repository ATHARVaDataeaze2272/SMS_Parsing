from pydantic import BaseModel
from typing import List, Dict, Any, Optional



class JSONUploadRequest(BaseModel):
    file_path: str

class JSONRecord(BaseModel):
    date: Optional[str] = None
    message: str

class UploadResponse(BaseModel):
    status: str
    message: str
    records_processed: int = 0
    records_failed: int = 0

class ProcessingStatus(BaseModel):
    total: int
    processed: int
    succeeded: int
    failed: int
    status: str

class MessageResponse(BaseModel):
    message_type: str
    important_points: List[str]
    data: Optional[Dict[str, Any]] = None

class CSVUploadRequest(BaseModel):
    file_path: str
    delimiter: str = ","
    has_header: bool = True

class UploadResponse(BaseModel):
    status: str
    message: str
    records_processed: int = 0
    records_failed: int = 0

class ProcessingStatus(BaseModel):
    total: int
    processed: int
    succeeded: int
    failed: int
    status: str

class MessageResponse(BaseModel):
    message_type: str
    important_points: List[str]
    data: Optional[Dict[str, Any]] = None