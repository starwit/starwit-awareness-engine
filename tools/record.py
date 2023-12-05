import argparse
import signal
import threading
import time
from typing import TextIO

import pybase64
import redis
from pydantic import BaseModel
from simple_term_menu import TerminalMenu
from visionapi.messages_pb2 import (Detection, DetectionOutput,
                                    TrackedDetection, TrackingOutput,
                                    VideoFrame)
from visionlib.pipeline.consumer import RedisConsumer

MESSAGE_SEPARATOR = ';'


class EventMeta(BaseModel):
    record_time: float
    source_stream: str
    
class Event(BaseModel):
    meta: EventMeta
    data_b64: str

class DumpMeta(BaseModel):
    start_time: float


def choose_streams(redis_client):
    available_streams = list(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM')[1]))
    menu = TerminalMenu(
        available_streams, 
        title='Choose Redis streams to record:', 
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

def write_meta(file: TextIO, start_time: float):
    meta = DumpMeta(start_time=start_time)
    file.write(meta.model_dump_json())
    file.write(MESSAGE_SEPARATOR)

def write_event(file: TextIO, stream_key: str, proto_data):
    stream_type = stream_key.split(':')[0]

    event = Event(
        meta=EventMeta(
            record_time=time.time(),
            source_stream=stream_key
        ),
        data_b64=get_proto_b64(stream_type, proto_data)
    )

    file.write(event.model_dump_json())
    file.write(MESSAGE_SEPARATOR)

    
def get_proto_b64(stream_type: str, proto_data):
    if stream_type == 'videosource':
        proto = VideoFrame()
        proto.ParseFromString(proto_data)
    elif stream_type == 'objectdetector':
        proto = DetectionOutput()
        proto.ParseFromString(proto_data)
    elif stream_type == 'objecttracker':
        proto = TrackingOutput()
        proto.ParseFromString(proto_data)
    return pybase64.standard_b64encode(proto_data)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--streams', type=str, nargs='*', metavar='STREAM')
    arg_parser.add_argument('-o', '--output-file', type=str, default=f'./{time.strftime("%Y-%m-%dT%H-%M-%S%z")}.saedump')
    arg_parser.add_argument('-t', '--time-limit', type=int, help='Stop recording after TIME_LIMIT seconds (default 60)', default=60)
    arg_parser.add_argument('--redis-host', type=str, default='localhost')
    arg_parser.add_argument('--redis-port', type=int, default=6379)
    args = arg_parser.parse_args()

    STREAM_IDS = args.streams
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_IDS is None:
        redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
        STREAM_IDS = choose_streams(redis_client)

    print(f'Recording streams {STREAM_IDS} into {args.output_file}')

    stop_event = threading.Event()

    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    consume = RedisConsumer(REDIS_HOST, REDIS_PORT, STREAM_IDS, block=200)

    start_time = time.time()

    with consume, open(args.output_file, 'x') as output_file:
        
        write_meta(output_file, start_time)

        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_key is None:
                continue

            if time.time() - start_time > args.time_limit:
                print(f'Reached configured time limit of {args.time_limit}s')
                break

            write_event(output_file, stream_key, proto_data)