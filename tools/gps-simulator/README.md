# GPS Simulator

A Python script that replays GPS log data in real-time through a virtual serial port.

## What it does

- Creates a virtual serial port at `/tmp/gps-simulator`
- Reads timestamped GPS log data from a file
- Replays the GPS messages with original timing preserved
- Allows other applications to read simulated GPS data as if from real hardware

## Usage

```bash
python main.py <path-to-gps-log-file>
```

The GPS log file should contain lines in the format:
```
ISO_TIMESTAMP;GPS_PAYLOAD
```

Example:
```
2024-01-01T12:00:00.000Z;$GPGGA,120000.000,5230.000,N,01322.000,E,1,04,2.0,100.0,M,0.0,M,,*69
```

Connect to the virtual serial port at `/tmp/gps-simulator` to receive the simulated GPS data.
