import sys
import os
import time

import cv2
import numpy as np
import redis
from common import choose_stream, default_arg_parser, register_stop_handler
from visionapi.messages_pb2 import Detection, SaeMessage
from visionlib.pipeline.consumer import RedisConsumer
from visionlib.pipeline.tools import get_raw_frame_data

ANNOTATION_COLOR = (0, 0, 255)
DEFAULT_WINDOW_SIZE = (1280, 720)

previous_frame_timestamp = 0
args = None

def isWindowVisible(window_name):
    try:
        windowVisibleProp = int(cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE))
        return windowVisibleProp == 1
    except:
        return False
    
def get_image(sae_msg: SaeMessage):
    if args.image_file is not None:
        image = cv2.imread(args.image_file)
        if image is None:
            raise ValueError(f'Could not read image from file {args.image_file}')
        return image
    else:
        frame = get_raw_frame_data(sae_msg.frame)
        if frame is not None:
            return frame
        else:
            # If no frame is available, return a grey image as a last resort
            return np.ones((sae_msg.frame.shape.height, sae_msg.frame.shape.width, 3), dtype=np.uint8) * 127


def annotate(image, detection: Detection):
    bbox_x1 = int(detection.bounding_box.min_x * image.shape[1])
    bbox_y1 = int(detection.bounding_box.min_y * image.shape[0])
    bbox_x2 = int(detection.bounding_box.max_x * image.shape[1])
    bbox_y2 = int(detection.bounding_box.max_y * image.shape[0])

    class_id = detection.class_id
    conf = detection.confidence

    label = f'{class_id} - {round(conf,2)}'

    if detection.object_id is not None:
        object_id = detection.object_id.hex()[:4]
        label = f'ID {object_id} - {class_id} - {round(conf,2)}'

    line_width = max(round(sum(image.shape) / 2 * 0.002), 2)

    cv2.rectangle(image, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), color=ANNOTATION_COLOR, thickness=line_width, lineType=cv2.LINE_AA)
    cv2.putText(image, label, (bbox_x1, bbox_y1 - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX, color=ANNOTATION_COLOR, thickness=round(line_width/3), fontScale=line_width/4, lineType=cv2.LINE_AA)

def showImage(stream_id, image):
    if not isWindowVisible(window_name=stream_id):
        cv2.namedWindow(stream_id, cv2.WINDOW_NORMAL + cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(stream_id, *DEFAULT_WINDOW_SIZE)
        
    cv2.imshow(stream_id, image)
    if cv2.waitKey(1) == ord('q'):
        stop_event.set()
        cv2.destroyAllWindows()

def handle_sae_message(sae_message_bytes, stream_key):
    global previous_frame_timestamp, args

    sae_msg = SaeMessage()
    sae_msg.ParseFromString(sae_message_bytes)

    frametime = sae_msg.frame.timestamp_utc_ms - previous_frame_timestamp
    previous_frame_timestamp = sae_msg.frame.timestamp_utc_ms

    log_line = f'E2E-Delay: {round(time.time() * 1000 - sae_msg.frame.timestamp_utc_ms): >8} ms, Display Frametime: {frametime: >5} ms'
    if sae_msg.HasField('metrics'):
        log_line += f', Detection: {sae_msg.metrics.detection_inference_time_us: >7} us, Tracking: {sae_msg.metrics.tracking_inference_time_us: >7} us'
    print(log_line, file=sys.stderr)

    image = get_image(sae_msg)

    for detection in sae_msg.detections:
        annotate(image, detection)
    
    if args.stdout:
        sys.stdout.buffer.write(image)
    
    showImage(stream_key, image)


if __name__ == '__main__':

    arg_parser = default_arg_parser()
    arg_parser.add_argument('-s', '--stream', type=str)
    arg_parser.add_argument('-i', '--image-file', type=str, default=None)
    arg_parser.add_argument('-o', '--stdout', action='store_true', help='Output annotated raw frames to stdout (e.g. to pipe into ffmpeg)')
    args = arg_parser.parse_args()

    if args.stdout and sys.stdout.isatty():
        print('Stdout is the terminal. Ignoring "stdout" option. Please redirect (e.g. into ffmpeg)', file=sys.stderr)
        args.stdout = False

    STREAM_KEY = args.stream
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_KEY is None:
        redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
        STREAM_KEY = choose_stream(redis_client)
    
    stop_event = register_stop_handler()

    consume = RedisConsumer(REDIS_HOST, REDIS_PORT, [STREAM_KEY], block=200)

    with consume:
        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_key is None:
                continue
            
            handle_sae_message(proto_data, stream_key)