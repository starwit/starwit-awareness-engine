import argparse
import signal
import threading

import cv2
import redis
from simple_term_menu import TerminalMenu
from visionapi.messages_pb2 import (Detection, DetectionOutput,
                                    TrackedDetection, TrackingOutput,
                                    VideoFrame)
from visionlib.pipeline.consumer import RedisConsumer
from visionlib.pipeline.tools import get_raw_frame_data

ANNOTATION_COLOR = (0, 0, 255)
DEFAULT_WINDOW_SIZE = (1280, 720)

def isWindowVisible(window_name):
    try:
        windowVisibleProp = int(cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE))
        return windowVisibleProp == 1
    except:
        return False

def choose_stream(redis_client):
    available_streams = list(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM')[1]))
    menu = TerminalMenu(available_streams, title='Choose Redis stream to watch:', show_search_hint=True)
    selected_idx = menu.show()
    if selected_idx is None:
        print('No stream chosen. Exiting.')
        exit(0)
    return available_streams[selected_idx]

def annotate(image, detection: Detection, object_id: bytes = None):
    bbox_x1 = detection.bounding_box.min_x
    bbox_y1 = detection.bounding_box.min_y
    bbox_x2 = detection.bounding_box.max_x
    bbox_y2 = detection.bounding_box.max_y

    class_id = detection.class_id
    conf = detection.confidence

    label = f'{class_id} - {round(conf,2)}'

    if object_id is not None:
        object_id = object_id.hex()[:4]
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

def source_output_handler(frame_message, stream_id):
    frame_proto = VideoFrame()
    frame_proto.ParseFromString(frame_message)
    image = get_raw_frame_data(frame_proto)

    showImage(stream_id, image)

def detection_output_handler(detection_message, stream_id):
    detection_proto = DetectionOutput()
    detection_proto.ParseFromString(detection_message)
    print(f'Inference times - detection: {detection_proto.metrics.detection_inference_time_us} us')
    image = get_raw_frame_data(detection_proto.frame)

    for detection in detection_proto.detections:
        annotate(image, detection)

    showImage(stream_id, image)

def tracking_output_handler(tracking_message, stream_id):
    track_proto = TrackingOutput()
    track_proto.ParseFromString(tracking_message)
    print(f'Inference times - detection: {track_proto.metrics.detection_inference_time_us} us, tracking: {track_proto.metrics.tracking_inference_time_us} us')
    image = get_raw_frame_data(track_proto.frame)

    for tracked_det in track_proto.tracked_detections:
        annotate(image, tracked_det.detection, tracked_det.object_id)

    showImage(stream_id, image)

STREAM_TYPE_HANDLER = {
    'videosource': source_output_handler,
    'objectdetector': detection_output_handler,
    'objecttracker': tracking_output_handler,
}


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--stream', type=str)
    arg_parser.add_argument('--redis-host', type=str, default='localhost')
    arg_parser.add_argument('--redis-port', type=int, default=6379)
    args = arg_parser.parse_args()

    STREAM_ID = args.stream
    REDIS_HOST = args.redis_host
    REDIS_PORT = args.redis_port

    if STREAM_ID is None:
        redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
        STREAM_ID = choose_stream(redis_client)
    
    stop_event = threading.Event()

    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    consume = RedisConsumer(REDIS_HOST, REDIS_PORT, [STREAM_ID], block=200)

    with consume:
        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_key is None:
                continue
            
            stream_type, stream_id = stream_key.split(':')
            STREAM_TYPE_HANDLER[stream_type](proto_data, stream_id)

        

        
    
