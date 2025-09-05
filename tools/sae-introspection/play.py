import time
from datetime import timedelta

import pybase64
from visionapi.analytics_pb2 import DetectionCountMessage
from visionapi.sae_pb2 import PositionMessage, SaeMessage
from visionlib.pipeline.publisher import RedisPublisher
from visionlib.saedump import DumpMeta, Event, message_splitter

from common import (InternalMessageType, default_arg_parser,
                    determine_message_type, register_stop_handler)


def time_until_record_time(playback_start_time: float, record_start_time: float, record_target_time: float):
    current_time = time.time()
    playback_delta = current_time - playback_start_time
    target_delta = record_target_time - record_start_time
    return max(0, target_delta - playback_delta)

def time_until_interval(prev_message_time: float, target_interval: timedelta):
    current_time = time.time()
    target_time = prev_message_time + target_interval.total_seconds()
    sleep_time = target_time - current_time
    return max(0, sleep_time)

def set_frame_timestamp_to_now(proto_bytes: str):
    msg_type = determine_message_type(proto_bytes)

    match msg_type:
        case InternalMessageType.SAE:
            msg = SaeMessage()
            msg.ParseFromString(proto_bytes)

            msg.frame.timestamp_utc_ms = time.time_ns() // 1000000
            return msg.SerializeToString()
        case InternalMessageType.POSITION:
            msg = PositionMessage()
            msg.ParseFromString(proto_bytes)

            msg.timestamp_utc_ms = time.time_ns() // 1000000
            return msg.SerializeToString()
        case InternalMessageType.DETECTION_COUNT:
            msg = DetectionCountMessage()
            msg.ParseFromString(proto_bytes)

            msg.timestamp_utc_ms = time.time_ns() // 1000000
            return msg.SerializeToString()


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
        while not stop_event.is_set():
            message_iter = message_splitter(input_file)

            playback_start_ts = time.time()
            prev_message_ts = 0
            start_message = next(message_iter)
            dump_meta = DumpMeta.model_validate_json(start_message)
            print(f'Starting playback from file {args.dumpfile} containing streams {dump_meta.recorded_streams}')

            for message in message_iter:
                event = Event.model_validate_json(message)
                proto_bytes = pybase64.standard_b64decode(event.data_b64)

                if args.fixed_interval is not None:
                    stop_event.wait(time_until_interval(prev_message_ts, args.fixed_interval))
                else:
                    stop_event.wait(time_until_record_time(playback_start_ts, dump_meta.start_time, event.meta.record_time))

                if args.adjust_timestamps:
                    proto_bytes = set_frame_timestamp_to_now(proto_bytes)

                publish(event.meta.source_stream, proto_bytes)

                prev_message_ts = time.time()

                if stop_event.is_set():
                    break
            
            if not args.loop:
                break
            else:
                input_file.seek(0)
