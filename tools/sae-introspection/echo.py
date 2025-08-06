import sys

import redis
from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message
from visionapi.analytics_pb2 import DetectionCountMessage
from visionapi.sae_pb2 import PositionMessage, SaeMessage
from visionlib.pipeline.consumer import RedisConsumer

from common import (InternalMessageType, choose_streams, default_arg_parser,
                    determine_message_type, register_stop_handler)


def handle_sae_message(message_bytes: bytes, preserve_frame=False):
    msg = SaeMessage()
    msg.ParseFromString(message_bytes)

    if not preserve_frame:
        msg.frame.ClearField('frame_data')
        msg.frame.ClearField('frame_data_jpeg')

    msg_json = MessageToJson(msg, always_print_fields_with_no_presence=True)
    print(msg_json, flush=True)

def handle_generic_message(message_bytes: bytes, msg: Message) -> None:
    msg.ParseFromString(message_bytes)

    msg_json = MessageToJson(msg, always_print_fields_with_no_presence=True)
    print(msg_json, flush=True)

if __name__ == '__main__':

    arg_parser = default_arg_parser()
    arg_parser.add_argument('-s', '--streams', type=str, nargs='*', metavar='STREAM')
    arg_parser.add_argument('-f', '--preserve-frame', action='store_true', help='Do not remove frame data (WARNING: large output!)')
    args = arg_parser.parse_args()

    STREAM_KEYS = args.streams
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_KEYS is None:
        redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
        STREAM_KEYS = choose_streams(redis_client)
    
    stop_event = register_stop_handler()

    consume = RedisConsumer(REDIS_HOST, REDIS_PORT, STREAM_KEYS, block=200)

    message_type: InternalMessageType = None

    with consume:
        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_key is None:
                continue

            if message_type is None:
                message_type = determine_message_type(proto_data)
                print(f'Detected message type {message_type} on stream.', file=sys.stderr)


            if message_type == InternalMessageType.SAE:
                handle_sae_message(proto_data, args.preserve_frame)
            elif message_type == InternalMessageType.POSITION:
                handle_generic_message(proto_data, PositionMessage())
            elif message_type == InternalMessageType.DETECTION_COUNT:
                handle_generic_message(proto_data, DetectionCountMessage())
