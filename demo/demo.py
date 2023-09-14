import threading

import cv2
import numpy as np
import redis
from ultralytics.yolo.utils.plotting import Annotator
from visionapi.messages_pb2 import TrackingOutput
from visionlib.pipeline.consumer import RedisConsumer


def deserialize_proto(message):
    track_output = TrackingOutput()
    track_output.ParseFromString(message)
    return track_output

def create_output_image(track_proto: TrackingOutput):
    img_shape = track_proto.frame.shape
    img_bytes = track_proto.frame.frame_data
    img = np.frombuffer(img_bytes, dtype=np.uint8) \
        .reshape((img_shape.height, img_shape.width, img_shape.channels))

    return annotate(img, track_proto)

def annotate(image, track_proto: TrackingOutput):
    ann = Annotator(image, line_width=4)
    for detection in track_proto.tracked_detections:
        bbox_x1 = detection.detection.bounding_box.min_x
        bbox_y1 = detection.detection.bounding_box.min_y
        bbox_x2 = detection.detection.bounding_box.max_x
        bbox_y2 = detection.detection.bounding_box.max_y

        class_id = detection.detection.class_id
        conf = detection.detection.confidence
        object_id = detection.object_id.hex()[:4]

        ann.box_label((bbox_x1, bbox_y1, bbox_x2, bbox_y2), f'ID {object_id} - {class_id} - {round(conf,2)}')

    return ann.result()

def output_handler(tracking, stream_id):
    track_proto = deserialize_proto(tracking)
    print(f'Inference times - detection: {track_proto.metrics.detection_inference_time_us} us, tracking: {track_proto.metrics.tracking_inference_time_us} us')
    cv2.namedWindow(f'{stream_id}', cv2.WINDOW_NORMAL)
    cv2.resizeWindow(f'{stream_id}', 1920, 1080)
    cv2.imshow(f'{stream_id}', create_output_image(track_proto))
    if cv2.waitKey(1) == ord('q'):
        stop_event.set()
        cv2.destroyAllWindows()

if __name__ == '__main__':

    STREAM_IDS = [ 'objecttracker:video1', 'objecttracker:video2' ]

    stop_event = threading.Event()
    last_retrieved_id = None

    consume = RedisConsumer('localhost', 6379, STREAM_IDS)

    with consume:
        for stream_id, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_id is None:
                continue

            output_handler(proto_data, stream_id)

        

        
    
