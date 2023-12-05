import argparse
import signal
import threading
import time
from typing import TextIO

import pybase64
from visionlib.pipeline.publisher import RedisPublisher

from common import MESSAGE_SEPARATOR, DumpMeta, Event


def read_messages(file: TextIO):
    buffer = ''
    while True:
        chunk = file.read(4096)
        if len(chunk) == 0:
            break
        sep_idx = chunk.find(MESSAGE_SEPARATOR)
        if sep_idx != -1:
            yield buffer + chunk[:sep_idx]
            buffer = chunk[sep_idx+1:]
        else:
            buffer += chunk

def wait_until(playback_start_time: float, record_start_time: float, record_target_time: float):
    current_time = time.time()
    playback_delta = current_time - playback_start_time
    target_delta = record_target_time - record_start_time
    if playback_delta <= target_delta:
        time.sleep(target_delta - playback_delta)
        

if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-o', '--input-file', type=str, required=True)
    arg_parser.add_argument('--redis-host', type=str, default='localhost')
    arg_parser.add_argument('--redis-port', type=int, default=6379)
    args = arg_parser.parse_args()

    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    stop_event = threading.Event()

    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    publish = RedisPublisher(REDIS_HOST, REDIS_PORT)

    start_time = time.time()

    with publish, open(args.input_file, 'r') as input_file:
        message_reader = read_messages(input_file)

        start_message = next(message_reader)
        dump_meta = DumpMeta.model_validate_json(start_message)
        print(f'Starting playback from file {args.input_file} containing streams {dump_meta.recorded_streams}')

        while not stop_event.is_set():
            for message in message_reader:
                event = Event.model_validate_json(message)

                wait_until(start_time, dump_meta.start_time, event.meta.record_time)

                publish(event.meta.source_stream, pybase64.standard_b64decode(event.data_b64))
                
            break

            