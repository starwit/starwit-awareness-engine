import argparse
import signal
import threading

import redis
from common import choose_streams
from google.protobuf.json_format import MessageToJson
from visionapi.messages_pb2 import SaeMessage
from visionlib.pipeline.consumer import RedisConsumer


def handle_sae_message(sae_message_bytes, preserve_frame=False, output_file=None):
    sae_msg = SaeMessage()
    sae_msg.ParseFromString(sae_message_bytes)

    if not preserve_frame:
        sae_msg.frame.ClearField('frame_data')
        sae_msg.frame.ClearField('frame_data_jpeg')

    msg_json = MessageToJson(sae_msg)
    if output_file is not None:
        output_file.write(msg_json)
    else:
        print(msg_json)

if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--streams', type=str, nargs='*', metavar='STREAM')
    arg_parser.add_argument('-f', '--preserve-frame', action='store_true', help='Do not remove frame data (WARNING: large output!)')
    arg_parser.add_argument('--redis-host', type=str, default='localhost')
    arg_parser.add_argument('--redis-port', type=int, default=6379)
    args = arg_parser.parse_args()

    STREAM_KEYS = args.streams
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_KEYS is None:
        redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
        STREAM_KEYS = choose_streams(redis_client)
    
    stop_event = threading.Event()

    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    consume = RedisConsumer(REDIS_HOST, REDIS_PORT, STREAM_KEYS, block=200)

    with consume:
        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_key is None:
                continue
            
            handle_sae_message(proto_data, args.preserve_frame)