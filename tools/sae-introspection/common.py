import argparse
import signal
import sys
import threading
from enum import StrEnum

from simple_term_menu import TerminalMenu
from visionapi.analytics_pb2 import DetectionCountMessage
from visionapi.sae_pb2 import SaeMessage
from visionlib.pipeline.formats import is_sae_message


class MessageType(StrEnum):
    SAE = 'SAE'
    DETECTION_COUNT = 'DETECTION_COUNT'
    

def choose_stream(redis_client):
    available_streams = sorted(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM', count=100)[1]))
    menu = TerminalMenu(available_streams, title='Choose Redis stream to attach to:', show_search_hint=True)
    selected_idx = menu.show()
    if selected_idx is None:
        print('No stream chosen. Exiting.', file=sys.stderr)
        exit(0)
    return available_streams[selected_idx]

def choose_streams(redis_client):
    available_streams = sorted(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM', count=100)[1]))
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
        print('No stream chosen. Exiting.', file=sys.stderr)
        exit(0)
    return [available_streams[idx] for idx in selected_idx_list]

def default_arg_parser():
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('--help', action='help', help='Show help message and exit')
    arg_parser.add_argument('-h', '--redis-host', type=str, default='localhost')
    arg_parser.add_argument('-p', '--redis-port', type=int, default=6379)
    return arg_parser

def register_stop_handler():
    stop_event = threading.Event()

    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...', file=sys.stderr)
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    return stop_event

def check_sae_message(message_bytes: bytes) -> bool:
    msg = SaeMessage()
    msg.ParseFromString(message_bytes)

    return is_sae_message(msg)
    
def check_detection_count_message(message_bytes: bytes) -> bool:
    msg = DetectionCountMessage()
    msg.ParseFromString(message_bytes)

    return all((
        msg.timestamp_utc_ms != 0,
    ))

def determine_message_type(message_bytes: bytes) -> MessageType:
    """
    Determines the type of a protobuf message based on parsing its content and applying some simple heuristics.

    Args:
        message_bytes (bytes): The serialized protobuf message.

    Returns:
        MessageType: The detected message type (SAE or DETECTION_COUNT).

    Raises:
        ValueError: If the message type cannot be determined.
    """
    if check_detection_count_message(message_bytes):
        return MessageType.DETECTION_COUNT
    elif check_sae_message(message_bytes):
        return MessageType.SAE
    else:
        raise ValueError('Unknown message type. Could not determine message type from the first message.')
