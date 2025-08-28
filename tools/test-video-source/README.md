# Test Video Source

A tool that replays recorded video files with synchronized GPS data for testing the Starwit Awareness Engine.

## What it does

- Plays back video files with real-time timing
- Synchronizes GPS location data from corresponding log files
- Publishes video frames with location metadata to Redis/Valkey
- Supports frame scaling and FPS adjustment for testing different scenarios

## Prerequisites

- Video file with timestamp in filename format: `YYYY-MM-DD_HH-MM-SS_...`
- Corresponding GPS log file with format: `ISO_TIMESTAMP;NMEA_SENTENCE`
- Redis/Valkey server running

## Usage

```bash
python main.py [options] <video_file> <gps_log_file>
```

### Options

- `-h, --redis-host HOST`: Redis/Valkey host (default: localhost)
- `-p, --redis-port PORT`: Redis/Valkey port (default: 6379)
- `-s, --scale-width WIDTH`: Downscale frames to specified width in pixels
- `-f, --fps FPS`: Target FPS for playback
- `--help`: Show help message

### Example

```bash
# Basic usage
python main.py 2024-06-01_14-30-00_video.mp4 2024-06-01_14-30-00_gps.log

# With custom Redis server, downscaled frames and 10 fps
python main.py -h 192.168.1.100 -s 640 -f 10 2024-06-01_14-30-00_video.mp4 2024-06-01_14-30-00_gps.log
```

The tool will publish SAE messages containing video frames and GPS coordinates to the Redis channel for consumption by the awareness engine.
