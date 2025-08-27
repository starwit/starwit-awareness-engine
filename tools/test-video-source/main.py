import argparse
from pathlib import Path
from typing import Callable, Generator, NamedTuple
from pynmeagps.nmeareader import NMEAReader
from datetime import timedelta, datetime
from numpy.typing import NDArray
import numpy as np

import cv2
from visionlib.pipeline.publisher import RedisPublisher
from visionapi.sae_pb2 import SaeMessage

class Position(NamedTuple):
    start_offset: timedelta
    lat: float
    lon: float

class Frame(NamedTuple):
    start_offset: timedelta
    data: NDArray[np.uint8]

def iter_gps_log(log_file: Path) -> Generator[int, None, None]:
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

def iter_frames(video_file: Path) -> Generator[Frame, None, None]:
    cap = cv2.VideoCapture(str(video_file))
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
        yield Frame(
            start_offset=timedelta(milliseconds=pos_msec),
            data=frame,
        )
    cap.release()

def create_sae_msg(frame: Frame, pos: Position) -> SaeMessage:
    msg = SaeMessage()
    msg.frame.camera_location.latitude = pos.lat
    msg.frame.camera_location.longitude = pos.lon
    # TODO add all fields

# TODO compress and scale frame

def play_recording(video: Path, gps_log: Path, publish: Callable[[bytes], None]) -> None:
    pass

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('--help', action='help', help='Show help message and exit')
    arg_parser.add_argument('-h', '--redis-host', type=str, default='localhost', help='Redis/Valkey host to connect to', metavar='HOST')
    arg_parser.add_argument('-p', '--redis-port', type=int, default=6379, help='Redis/Valkey port to connect to', metavar='PORT')
    arg_parser.add_argument('video', type=Path, help='Video file to play', metavar='FILE')
    arg_parser.add_argument('gps_log', type=Path, help='Corresponding gps log file', metavar='FILE')
    args = arg_parser.parse_args()

    publisher = RedisPublisher(args.redis_host, args.redis_port)

    with publisher as publish:
        pass