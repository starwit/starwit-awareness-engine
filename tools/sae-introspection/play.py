import time
from datetime import timedelta

import pybase64
from common import default_arg_parser, register_stop_handler
from visionapi.sae_pb2 import SaeMessage
from visionlib.pipeline.publisher import RedisPublisher
from visionlib.saedump import DumpMeta, Event, message_splitter


def wait_until_record_time(playback_start_time: float, record_start_time: float, record_target_time: float):
    current_time = time.time()
    playback_delta = current_time - playback_start_time
    target_delta = record_target_time - record_start_time
    if playback_delta <= target_delta:
        time.sleep(target_delta - playback_delta)

def wait_until_interval(prev_message_time: float, target_interval: timedelta):
    current_time = time.time()
    target_time = prev_message_time + target_interval.total_seconds()
    sleep_time = target_time - current_time
    print(target_time, sleep_time)
    if sleep_time > 0:
        time.sleep(sleep_time)

def set_frame_timestamp_to_now(proto_bytes: str):
    proto = SaeMessage()
    proto.ParseFromString(proto_bytes)

    proto.frame.timestamp_utc_ms = time.time_ns() // 1000000
    
    return proto.SerializeToString()


if __name__ == '__main__':

    arg_parser = default_arg_parser()
    arg_parser.add_argument('dumpfile')
    arg_parser.add_argument('-l', '--loop', action='store_true', help='Loop indefinitely (exit with Ctrl-C)')
    arg_parser.add_argument('-t', '--adjust-timestamps', action='store_true', help='Adjust message timestamps to the time in the moment of playback')
    arg_parser.add_argument('-i', '--fixed-interval', type='natural_timedelta', help='Ignore embedded timestamp and instead output messages at the given interval (natural timedelta)', metavar='INTERVAL')
    args = arg_parser.parse_args()

    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    stop_event = register_stop_handler()

    publish = RedisPublisher(REDIS_HOST, REDIS_PORT)

    with publish, open(args.dumpfile, 'r') as input_file:
        while True:
            messages = message_splitter(input_file)

            playback_start_ts = time.time()
            prev_message_ts = 0
            start_message = next(messages)
            dump_meta = DumpMeta.model_validate_json(start_message)
            print(f'Starting playback from file {args.dumpfile} containing streams {dump_meta.recorded_streams}')

            for message in messages:
                event = Event.model_validate_json(message)
                proto_bytes = pybase64.standard_b64decode(event.data_b64)

                if args.fixed_interval is not None:
                    wait_until_interval(prev_message_ts, args.fixed_interval)
                else:
                    wait_until_record_time(playback_start_ts, dump_meta.start_time, event.meta.record_time)

                if args.adjust_timestamps:
                    proto_bytes = set_frame_timestamp_to_now(proto_bytes)

                publish(event.meta.source_stream, proto_bytes)

                prev_message_ts = time.time()

                if stop_event.is_set():
                    break
            
            if not args.loop or stop_event.is_set():
                break
            else:
                input_file.seek(0)
            