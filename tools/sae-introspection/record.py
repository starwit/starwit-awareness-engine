import time
from typing import TextIO

import cv2
import pybase64
import redis
from turbojpeg import TurboJPEG
from visionapi.sae_pb2 import SaeMessage
from visionlib.pipeline.consumer import RedisConsumer
from visionlib.pipeline.tools import get_raw_frame_data
from visionlib.saedump import MESSAGE_SEPARATOR, DumpMeta, Event, EventMeta

from common import (InternalMessageType, choose_streams, default_arg_parser,
                    determine_message_type, register_stop_handler)

jpeg = TurboJPEG()

def write_meta(file: TextIO, start_time: float, stream_keys: list[str]):
    meta = DumpMeta(
        start_time=start_time,
        recorded_streams=stream_keys
    )
    file.write(meta.model_dump_json())
    file.write(MESSAGE_SEPARATOR)

def write_event(file: TextIO, stream_key: str, proto_data: bytes):
    bytes_to_write = proto_data
    
    event = Event(
        meta=EventMeta(
            record_time=time.time(),
            source_stream=stream_key
        ),
        data_b64=pybase64.standard_b64encode(bytes_to_write)
    )

    file.write(event.model_dump_json())
    file.write(MESSAGE_SEPARATOR)

def process_sae_message(proto_data: bytes, is_remove_frame=False, scale_width=0, scale_quality=85) -> bytes:
    msg = SaeMessage()
    msg.ParseFromString(proto_data)

    if is_remove_frame:
        remove_frame(msg)

    if scale_width > 0:
        resize_frame(msg, scale_width, scale_quality)

    return msg.SerializeToString()

def remove_frame(msg: SaeMessage):
    msg.frame.ClearField('frame_data')
    msg.frame.ClearField('frame_data_jpeg')

def resize_frame(msg: SaeMessage, scale_width=0, quality=85):
    frame = get_raw_frame_data(msg.frame)

    if frame is None:
        return

    original_width = frame.shape[1]
    scale_factor = scale_width / original_width
    frame = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)

    msg.frame.frame_data_jpeg = jpeg.encode(frame, quality)


if __name__ == '__main__':

    arg_parser = default_arg_parser()
    arg_parser.add_argument('-s', '--streams', type=str, nargs='*', metavar='STREAM')
    arg_parser.add_argument('-o', '--output-file', type=str, default=f'./{time.strftime("%Y-%m-%dT%H-%M-%S%z")}.saedump', metavar='FILE')
    arg_parser.add_argument('-t', '--time-limit', type='natural_timedelta', help='Stop recording after TIME_LIMIT (default "60s")', default='60s')
    arg_parser.add_argument('-r', '--remove-frame', action='store_true', help='Remove frame data from messages (reduces size significantly)')
    arg_parser.add_argument('-d', '--downscale-frames', default=0, type=int, help='Downscale frames to given width (preserving aspect ratio)', metavar='WIDTH')
    arg_parser.add_argument('-q', '--downscale-jpeg-quality', default=85, type=int, help='JPEG quality for downscaling frames (0-100, sane values 80-95)', metavar='QUALITY')
    args = arg_parser.parse_args()

    STREAM_KEYS = args.streams
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_KEYS is None:
        redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
        STREAM_KEYS = choose_streams(redis_client)

    print(f'Recording streams {STREAM_KEYS} for {args.time_limit} into {args.output_file}')

    stop_event = register_stop_handler()

    consume = RedisConsumer(REDIS_HOST, REDIS_PORT, STREAM_KEYS, block=200, start_at_head=args.start_at_head)

    start_time = time.time()

    with consume, open(args.output_file, 'x') as output_file:
        
        write_meta(output_file, start_time, STREAM_KEYS)

        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if time.time() - start_time > args.time_limit.total_seconds():
                print(f'Reached configured time limit of {args.time_limit}')
                break

            if stream_key is None:
                continue

            if determine_message_type(proto_data) == InternalMessageType.SAE:
                proto_data = process_sae_message(proto_data, args.remove_frame, args.downscale_frames, args.downscale_jpeg_quality)

            write_event(output_file, stream_key, proto_data)