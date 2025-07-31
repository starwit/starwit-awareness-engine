import os
import pty
import time
import datetime
from argparse import ArgumentParser
from typing import Tuple

def main():
    parser = ArgumentParser(description="GPS Simulator")
    parser.add_argument('source_file', type=str, help='Path to the GPS log file')
    args = parser.parse_args()

    master_fd, slave_fd = pty.openpty()

    slave_name = os.ttyname(slave_fd)
    print(f'You can read the simulated data at {slave_name}')

    # Read first timestamp
    with open(args.source_file, 'r') as log_file:
        first_timestamp, _ = parse_line(log_file.readline())

    start_time = time.time()

    with os.fdopen(master_fd, 'w') as pseudo_term, open(args.source_file, 'r') as log_file:

        while len(line := log_file.readline()) > 0:
            timestamp, payload = parse_line(line)

            offset = timestamp - first_timestamp
            wait_until_offset(start_time, offset)
            
            pseudo_term.write(payload + '\n')
            pseudo_term.flush()

    
def parse_line(line: str) -> Tuple[float, str]:
    iso_timestamp, payload = line.strip().split(';')
    timestamp = datetime.datetime.fromisoformat(iso_timestamp).timestamp()
    return timestamp, payload

def wait_until_offset(start_time: float, data_offset: float) -> None:
    '''Sleep until the elapsed time matches the data offset in the log'''
    time_elapsed = time.time() - start_time
    time.sleep(max(0, data_offset - time_elapsed))

if __name__ == '__main__':
    main()