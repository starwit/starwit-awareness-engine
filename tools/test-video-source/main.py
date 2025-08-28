import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Generator, NamedTuple

import cv2
import numpy as np
from numpy.typing import NDArray
from pynmeagps.nmeareader import NMEAReader
from turbojpeg import TurboJPEG
from visionapi.common_pb2 import MessageType
from visionapi.sae_pb2 import SaeMessage
from visionlib.pipeline.publisher import RedisPublisher

_jpeg_encoder = TurboJPEG()

class Position(NamedTuple):
    start_offset: timedelta
    lat: float
    lon: float

class Frame(NamedTuple):
    timestamp: datetime
    start_offset: timedelta
    data: NDArray[np.uint8]

def iter_gps_log(log_file: Path) -> Generator[Position, None, None]:
    first_timestamp = None
    with open(log_file, 'r') as f:
        while (line := f.readline()):
            iso_str, nmea_str = line.strip().split(';')
            timestamp = datetime.fromisoformat(iso_str)
            if first_timestamp is None:
                first_timestamp = timestamp
            nmea = NMEAReader.parse(nmea_str)
            if nmea.msgID != 'GGA' or nmea.quality != 1:
                continue

            yield Position(
                start_offset=timestamp-first_timestamp,
                lat=nmea.lat,
                lon=nmea.lon,
            )

def parse_timestamp_from_file(file: Path) -> datetime:
    # Parse a datetime from the given file name (assuming UTC) - sample 2025-08-15_06-27-37_...
    base_name = file.stem
    timestamp_str = '_'.join(base_name.split('_')[:2])
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
    return timestamp

def iter_frames(video_file: Path, scale_width: int = 0, target_fps: int = 0) -> Generator[Frame, None, None]:
    file_start_timestamp = parse_timestamp_from_file(video_file)

    cap = cv2.VideoCapture(str(video_file))
    video_stride = 1
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if target_fps > 0:
        video_stride = max(1, int(video_fps / target_fps))
        print(f'Effective fps: {video_fps / video_stride}')
    
    video_start_ts = time.time()
    i = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        i += 1
        if i % video_stride != 0:
            continue

        pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)

        if scale_width > 0:
            frame = scale_frame(frame, scale_width)
        
        time.sleep(max(0, (video_start_ts + pos_msec / 1000) - time.time()))
        yield Frame(
            timestamp=file_start_timestamp,
            start_offset=timedelta(milliseconds=pos_msec),
            data=frame,
        )
    cap.release()

def create_sae_msg(frame: Frame, pos: Position) -> SaeMessage:
    msg = SaeMessage()
    msg.type = MessageType.SAE
    msg.frame.source_id = 'test'
    msg.frame.timestamp_utc_ms = int(frame.timestamp.timestamp() * 1000)
    msg.frame.frame_data_jpeg = _jpeg_encoder.encode(frame.data, quality=90)
    msg.frame.shape.height = frame.data.shape[0]
    msg.frame.shape.width = frame.data.shape[1]
    msg.frame.shape.channels = frame.data.shape[2]
    msg.frame.camera_location.latitude = pos.lat
    msg.frame.camera_location.longitude = pos.lon
    return msg

def scale_frame(frame: NDArray[np.uint8], width: int) -> NDArray[np.uint8]:
    frame_width = frame.shape[1]
    scale_factor = width / frame_width
    return cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)    

def iter_recording(video: Path, gps_log: Path, scale_width: int = 0, fps: int = 0) -> Generator[SaeMessage, None, None]:
    gps_log_lines = iter_gps_log(gps_log)
    matching_position = next(gps_log_lines)
    for frame in iter_frames(video, scale_width, fps):
        while matching_position.start_offset < frame.start_offset:
            matching_position = next(gps_log_lines)
        yield create_sae_msg(frame, matching_position)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('--help', action='help', help='Show help message and exit')
    arg_parser.add_argument('-h', '--redis-host', type=str, default='localhost', help='Redis/Valkey host to connect to', metavar='HOST')
    arg_parser.add_argument('-p', '--redis-port', type=int, default=6379, help='Redis/Valkey port to connect to', metavar='PORT')
    arg_parser.add_argument('-s', '--scale-width', type=int, default=0, help='Downscale frames to width in px (preserving aspect ratio)', metavar='WIDTH')
    arg_parser.add_argument('-f', '--fps', type=int, default=0, help='Target FPS', metavar='FPS')
    arg_parser.add_argument('video', type=Path, help='Video file to play', metavar='FILE')
    arg_parser.add_argument('gps_log', type=Path, help='Corresponding gps log file', metavar='FILE')
    args = arg_parser.parse_args()

    if args.video.stem.split('_')[:2] != args.gps_log.stem.split('_')[:2]:
        print('Given files must match in timestamp prefix!')
        exit(1)

    publisher = RedisPublisher(args.redis_host, args.redis_port)

    with publisher as publish:
        for msg in iter_recording(args.video, args.gps_log, scale_width=args.scale_width, fps=args.fps):
            publish('test', msg.SerializeToString())