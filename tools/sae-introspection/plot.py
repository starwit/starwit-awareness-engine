from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Generator, List, Tuple

import cv2
import numpy as np
import pybase64
import tqdm
from common import (InternalMessageType, choose_stream_from_list,
                    determine_message_type, register_stop_handler)
from palettable.colorbrewer.qualitative import Set1_9
from visionapi.sae_pb2 import SaeMessage
from visionlib.saedump import DumpMeta, Event, message_splitter

CLS_CMAP = Set1_9.colors
ALPHA = 0.80

def iter_sae_dump(file: Path) -> Generator[bytes, None, None]:
    with open(file, 'r') as input_file:
        message_iter = message_splitter(input_file)
        for message in message_iter:
            yield message

def get_contained_streams(file: Path) -> List[str]:
    message_iter = iter_sae_dump(file)
    first_message = next(message_iter)
    message_iter.close()

    dump_meta = DumpMeta.model_validate_json(first_message)
    return dump_meta.recorded_streams

def iter_sae_messages(dump_file: Path, stream_id: str) -> Generator[SaeMessage, None, None]:
    event_iter = iter_sae_dump(dump_file)

    # Skip the DumpMeta message
    _ = next(event_iter)
    
    for json_event in event_iter:
        event = Event.model_validate_json(json_event)

        if event.meta.source_stream != stream_id:
            continue

        proto_bytes = pybase64.standard_b64decode(event.data_b64)
        sae_msg = SaeMessage()
        sae_msg.ParseFromString(proto_bytes)
        
        if (msg_type := determine_message_type(proto_bytes)) != InternalMessageType.SAE:
            raise ValueError(f'Found message type {msg_type}, SAE messages needed')
        
        yield sae_msg
        
def draw_line(img, pt1: Tuple[float], pt2: Tuple[float], class_id: int):
    cv2.line(img, (int(pt1[0] * img.shape[1]), int(pt1[1] * img.shape[0])), (int(pt2[0] * img.shape[1]), int(pt2[1] * img.shape[0])), color=get_color(class_id), thickness=1, lineType=cv2.LINE_AA)

def get_color(class_id: int) -> Tuple[int]:
    c = CLS_CMAP[class_id % len(CLS_CMAP)]
    return (c[2], c[1], c[0])


if __name__ == '__main__':

    arg_parser = ArgumentParser()
    arg_parser.add_argument('dumpfile', type=Path, help='Path to SAE dump file to plot')
    arg_parser.add_argument('-i', '--image-file', help='Path to an image to plot trajectories on (grey background will be used if not specified)')
    args = arg_parser.parse_args()

    stop_event = register_stop_handler()

    streams = get_contained_streams(args.dumpfile)
    if len(streams) == 1:
        stream_id = streams[0]
    else:
        stream_id = choose_stream_from_list(streams)

    if args.image_file is not None:
        image = cv2.imread(args.image_file, cv2.IMREAD_COLOR)
    else:
        image = np.ones((1080, 1920, 3), dtype=np.uint8) * 127

    annotated_image = image.copy()

    output_file = args.dumpfile.parent / f'{args.dumpfile.stem}.jpg'

    previous_points: Dict[bytes, Tuple[float, float]] = {}

    print('Drawing trajectories from messages')

    for sae_msg in tqdm.tqdm(iter_sae_messages(args.dumpfile, stream_id)):
        if stop_event.is_set():
            break

        for det in sae_msg.detections:
            center_x = (det.bounding_box.max_x + det.bounding_box.min_x) / 2
            center_y = (det.bounding_box.max_y + det.bounding_box.min_y) / 2
            new_point = (center_x, center_y)
            obj_id = det.object_id

            if obj_id in previous_points:
                draw_line(annotated_image, pt1=previous_points[obj_id], pt2=new_point, class_id=det.class_id)

            previous_points[obj_id] = new_point

    
    output_image = cv2.addWeighted(annotated_image, ALPHA, image, 1 - ALPHA, 0)

    cv2.imwrite(output_file, output_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f'Output written to {output_file}')
        
