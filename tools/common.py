from pydantic import BaseModel
from typing import List

MESSAGE_SEPARATOR = ';'


class EventMeta(BaseModel):
    record_time: float
    source_stream: str
    
class Event(BaseModel):
    meta: EventMeta
    data_b64: str

class DumpMeta(BaseModel):
    start_time: float
    recorded_streams: List[str]