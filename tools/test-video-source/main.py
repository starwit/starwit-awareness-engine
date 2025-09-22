import argparse
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator, List, NamedTuple, Dict, Iterable

import cv2
import numpy as np
import re
from collections import defaultdict
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

class FilePair(NamedTuple):
    video: Path
    gps_log: Path

def get_prefix(path: Path) -> str:
    """Extracts the timestamp prefix"""
    return "_".join(path.stem.split('_')[:2])

def main():
    arg_parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('--help', action='help', help='Show help message and exit')
    arg_parser.add_argument('-h', '--redis-host', type=str, default='localhost', help='Redis/Valkey host to connect to', metavar='HOST')
    arg_parser.add_argument('-p', '--redis-port', type=int, default=6379, help='Redis/Valkey port to connect to', metavar='PORT')
    arg_parser.add_argument('-s', '--scale-width', type=int, default=0, help='Downscale frames to width in px (preserving aspect ratio)', metavar='WIDTH')
    arg_parser.add_argument('-f', '--fps', type=int, default=0, help='Target FPS', metavar='FPS')
    arg_parser.add_argument('-k', '--stream-key', type=str, default='videosource:test', help='Stream output key', metavar='KEY')
    arg_parser.add_argument('-t', '--set-time-to-now', action='store_true', help='Whether to set message timestamp to now instead of recorded time.')
    arg_parser.add_argument('path', type=Path, help='Directory of video/gps_log pairs OR Video file to play (matching gps_log must be in the same directory)', metavar='FILE')
    args = arg_parser.parse_args()

    file_pairs = parse_input_path(args.path)

    publisher = RedisPublisher(args.redis_host, args.redis_port)

    with publisher as publish:
        for pair in file_pairs:
            for msg in iter_recording(pair.video, pair.gps_log, scale_width=args.scale_width, fps=args.fps):
                if args.set_time_to_now:
                    set_timestamp_to_now(msg)
                publish(args.stream_key, msg.SerializeToString())

def parse_input_path(path: Path) -> List[FilePair]:
    if path.is_file() and is_video(path):
        match = find_one_matching_file(path)
        return [FilePair(video=path, gps_log=match)]
    elif path.is_dir():
        return find_file_pairs(path)
    else:
        raise ValueError('Must either be an existing file or an existing directory')
    
def find_one_matching_file(video_file: Path) -> Path:
    video_key = to_numeric_key(video_file)
    similar_files = [f for f in video_file.parent.iterdir() if f.name != video_file.name and to_numeric_key(f) == video_key]
        
    match similar_files:
        case []:
            raise ValueError(f'No matching file found for {video_file}')
        case [single_match]:
            return single_match
        case [*multiple_matches]:
            raise ValueError(f'Found multiple matches: {multiple_matches}')
        
def find_file_pairs(dir: Path) -> List[FilePair]:
    pairs: List[FilePair] = []
    file_groups = find_file_groups(dir.iterdir())
    sorted_groups = [v for _, v in sorted(file_groups.items(), key=lambda item: item[0])]
    for group in sorted_groups:
        if len(group) == 2:
            if is_video(group[0]) and is_gps_log(group[1]):
                pairs.append(FilePair(video=group[0], gps_log=group[1]))
            elif is_video(group[1]) and is_gps_log(group[0]):
                pairs.append(FilePair(video=group[1], gps_log=group[0]))
    return pairs

def find_file_groups(files: Iterable[Path]) -> Dict[str, List[Path]]:
    files_by_numeric_key: Dict[str, List[Path]] = defaultdict(lambda: [])
    for file in files:
        key = to_numeric_key(file)
        files_by_numeric_key[key].append(file)
    return files_by_numeric_key

def to_numeric_key(file: Path) -> str:
    return '_'.join(re.findall(r'[0-9\-]+', file.name))

def is_video(path: Path) -> bool:
    return path.suffix in ('.mp4', '.mkv', '.avi')

def is_gps_log(path: Path) -> bool:
    return path.suffix == '.log'

def iter_recording(video: Path, gps_log: Path, scale_width: int = 0, fps: int = 0) -> Generator[SaeMessage, None, None]:
    gps_log_lines = iter_gps_log(gps_log)
    matching_position = next(gps_log_lines)
    for frame in iter_frames(video, scale_width, fps):
        while matching_position.start_offset < frame.start_offset:
            matching_position = next(gps_log_lines)
        yield create_sae_msg(frame, matching_position)

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

def parse_timestamp_from_file(file: Path) -> datetime:
    # Parse a datetime from the given file name (assuming UTC) - sample 2025-08-15_06-27-37_...
    base_name = file.stem
    timestamp_str = '_'.join(base_name.split('_')[:2])
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
    return timestamp

def scale_frame(frame: NDArray[np.uint8], width: int) -> NDArray[np.uint8]:
    frame_width = frame.shape[1]
    scale_factor = width / frame_width
    return cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)    

def create_sae_msg(frame: Frame, pos: Position) -> SaeMessage:
    msg = SaeMessage()
    msg.type = MessageType.SAE
    msg.frame.source_id = 'test'
    msg.frame.timestamp_utc_ms = int((frame.timestamp + frame.start_offset).timestamp() * 1000)
    msg.frame.frame_data_jpeg = _jpeg_encoder.encode(frame.data, quality=90)
    msg.frame.shape.height = frame.data.shape[0]
    msg.frame.shape.width = frame.data.shape[1]
    msg.frame.shape.channels = frame.data.shape[2]
    msg.frame.camera_location.latitude = pos.lat
    msg.frame.camera_location.longitude = pos.lon
    return msg

def set_timestamp_to_now(msg: SaeMessage) -> None:
    msg.frame.timestamp_utc_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

if __name__ == '__main__':
    main()