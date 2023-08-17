import cv2
import numpy as np
import redis
from ultralytics.yolo.utils.plotting import Annotator
from visionapi.messages_pb2 import TrackingOutput
import threading


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

def output_handler(tracking):
    track_proto = deserialize_proto(tracking)
    print(f'Inference times - detection: {track_proto.metrics.detection_inference_time_us} us, tracking: {track_proto.metrics.tracking_inference_time_us} us')
    cv2.namedWindow('window', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('window', 1920, 1080)
    cv2.imshow('window', create_output_image(track_proto))
    if cv2.waitKey(1) == ord('q'):
        stop_event.set()
        cv2.destroyAllWindows()

if __name__ == '__main__':

    stop_event = threading.Event()
    last_retrieved_id = None

    redis_conn = redis.Redis(
        host='localhost',
        port=6379,
    )

    while not stop_event.is_set():
        
        input_okay = False
        while not stop_event.is_set() and not input_okay:
            result = redis_conn.xread(
                count=1,
                block=5000,
                streams={f'objecttracker:ArchWestMain': '$' if last_retrieved_id is None else last_retrieved_id}
            )
        
            if result is None or len(result) == 0:
                continue

            # These unpacking incantations are apparently necessary...
            last_retrieved_id = result[0][1][0][0].decode('utf-8')
            tracker_proto = result[0][1][0][1][b'proto_data']

            input_okay = True
        
        output_handler(tracker_proto)

        
    
