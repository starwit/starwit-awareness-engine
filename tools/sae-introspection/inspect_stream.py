import base64
import time

from common import choose_stream, default_arg_parser, register_stop_handler
from redis import Redis
from visionapi.messages_pb2 import SaeMessage


def get_timestamp(sae_message_bytes):
    decoded_message = base64.b64decode(sae_message_bytes)

    sae_msg = SaeMessage()
    sae_msg.ParseFromString(decoded_message)

    return sae_msg.frame.timestamp_utc_ms

if __name__ == '__main__':

    arg_parser = default_arg_parser()
    arg_parser.add_argument('-s', '--stream', type=str)
    arg_parser.add_argument('-i', '--image-file', type=str, default=None)
    args = arg_parser.parse_args()

    STREAM_KEY = args.stream
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_KEY is None:
        redis_client = Redis(REDIS_HOST, REDIS_PORT)
        STREAM_KEY = choose_stream(redis_client)
    
    stop_event = register_stop_handler()

    redis = Redis(REDIS_HOST, REDIS_PORT)

    while True:
        if stop_event.is_set():
            break

        stream_tail = redis.xrange(STREAM_KEY, count=1)
        stream_head = redis.xrevrange(STREAM_KEY, count=1)
        stream_length = redis.xlen(STREAM_KEY)

        if stream_tail is not None and stream_head is not None:
            tail_timestamp_epoch = get_timestamp(stream_tail[0][1][b"proto_data_b64"]) / 1000
            head_timestamp_epoch = get_timestamp(stream_head[0][1][b"proto_data_b64"]) / 1000
            tail_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tail_timestamp_epoch))
            head_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(head_timestamp_epoch))
            now = time.time()
            print(f'{tail_timestamp}/lag={round(now - tail_timestamp_epoch, 2)}s -> {head_timestamp}/lag={round(now - head_timestamp_epoch, 2)}s ({stream_length} messages; {round(head_timestamp_epoch - tail_timestamp_epoch, 2)} s)')

        time.sleep(1)