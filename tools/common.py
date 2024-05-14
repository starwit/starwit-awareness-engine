from typing import List

from pydantic import BaseModel
from simple_term_menu import TerminalMenu

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


def choose_stream(redis_client):
    available_streams = sorted(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM')[1]))
    menu = TerminalMenu(available_streams, title='Choose Redis stream to attach to:', show_search_hint=True)
    selected_idx = menu.show()
    if selected_idx is None:
        print('No stream chosen. Exiting.')
        exit(0)
    return available_streams[selected_idx]

def choose_streams(redis_client):
    available_streams = sorted(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM')[1]))
    menu = TerminalMenu(
        available_streams, 
        title='Choose Redis streams to attach to:', 
        show_search_hint=True,
        multi_select=True,
        multi_select_empty_ok=True,
        multi_select_select_on_accept=False,
        show_multi_select_hint=True,
    )
    selected_idx_list = menu.show()
    if selected_idx_list is None:
        print('No stream chosen. Exiting.')
        exit(0)
    return [available_streams[idx] for idx in selected_idx_list]