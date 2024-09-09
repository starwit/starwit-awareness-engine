import argparse
import datetime as dt
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import psycopg
from palettable.colorbrewer.qualitative import Set1_9
from psycopg.rows import class_row
from tqdm import tqdm

CLS_CMAP = Set1_9.colors


@dataclass
class DetectionRow:
    detection_id: int
    capture_ts: datetime
    camera_id: str
    object_id: str
    class_id: int
    confidence: float
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    latitude: float
    longitude: float


def fetch_data(start_time: datetime, end_time: datetime, camera_id: str) -> List[DetectionRow]:
    conn_params = {
        'dbname': 'saebackend',
        'user': 'saebackend',
        'password': 'saebackend',
        'host': 'carmel-k3s',
        'port': '30003',
        'row_factory': class_row(DetectionRow)
    }

    try:
        with psycopg.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM detection WHERE capture_ts >= %s AND capture_ts <= %s AND camera_id = %s ORDER BY capture_ts ASC;"
                cur.execute(query, (start_time.isoformat(), end_time.isoformat(), camera_id))
                rows = []
                print('Loading result')
                with tqdm(unit=' rows') as pbar:
                    while (len(records := cur.fetchmany(10000)) > 0):
                        pbar.update(len(records))
                        rows += records
                return rows

    except psycopg.DatabaseError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_color(class_id: int) -> Tuple[int]:
    c = CLS_CMAP[class_id % len(CLS_CMAP)]
    return (c[2], c[1], c[0])

def get_center(row: DetectionRow):
    return ((row.min_x + row.max_x) / 2, (row.min_y + row.max_y) / 2)

def draw_trajectories(img, detections: List[DetectionRow]):
    preceding_points = {}
    for det in tqdm(detections):
        new_point = get_center(det)
        if det.object_id in preceding_points:
            draw_line(img, pt1=preceding_points[det.object_id], pt2=new_point, class_id=det.class_id)
        preceding_points[det.object_id] = new_point

def draw_line(img, pt1: Tuple[float], pt2: Tuple[float], class_id: int):
    cv2.line(img, (int(pt1[0] * img.shape[1]), int(pt1[1] * img.shape[0])), (int(pt2[0] * img.shape[1]), int(pt2[1] * img.shape[0])), color=get_color(class_id), thickness=2, lineType=cv2.LINE_AA)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-c', '--camera-id', type=str, required=True)
    arg_parser.add_argument('-i', '--image-file', type=Path)
    arg_parser.add_argument('-s', '--start-time', type=dt.datetime.fromisoformat, help='Data segment start time (in isoformat)')
    arg_parser.add_argument('-l', '--length', type=lambda s: dt.timedelta(seconds=int(s)), default=dt.timedelta(minutes=10), help='Length of data segment to load [s]')

    args = arg_parser.parse_args()

    if args.start_time is None:
        start_time = dt.datetime.now(tz=dt.UTC) - args.length
    else:
        start_time = args.start_time

    end_time = start_time + args.length

    if args.image_file is None:
        image = np.ones((1080, 1920, 3), dtype=np.uint8) * 127
    else:
        image = cv2.imread(args.image_file, cv2.IMREAD_COLOR)

    annotated_image = image.copy()

    output_file = Path('.') / f'{args.camera_id}_{start_time}_{args.length.seconds}s.jpg'

    print(f'Running query (camera: {args.camera_id}, start: {start_time.isoformat(timespec='seconds')}, length: {args.length})')
    rows = fetch_data(start_time, end_time, args.camera_id)

    print(f'Retrieved {len(rows)} data points from DB')

    print('Drawing trajectories')
    draw_trajectories(annotated_image, rows)

    if args.image_file is None:
        output_image = annotated_image
    else:
        alpha = 0.80
        output_image = cv2.addWeighted(annotated_image, alpha, image, 1 - alpha, 0)

    cv2.imwrite(output_file, output_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f'Output written to {output_file}')
    
