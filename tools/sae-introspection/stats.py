import requests
import time
import argparse
from os import system
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument('port')
PORT = int(ap.parse_args().port)

# Configuration
PROMETHEUS_ENDPOINT = f"http://localhost:{PORT}/api/v1/query"
COUNTER_METRICS = ["object_detector_frame_counter"]
SUMMARY_METRICS = [
    "object_detector_model_duration",
    "object_detector_nms_duration",
    "object_detector_proto_serialization_duration",
    "object_detector_proto_deserialization_duration",
    "object_detector_get_duration",
    "object_detector_redis_publish_duration",
]
INTERVAL = 0.5  # seconds between queries


# Variables to store the previous value and timestamp
prev_values = defaultdict(lambda: 0)
prev_time = 0

while True:
    try:
        # Get the metrics from Prometheus
        response = requests.get(PROMETHEUS_ENDPOINT)
        response.raise_for_status()
        metrics_data = response.text

        current_values = defaultdict(lambda: 0)
        for line in [l for l in metrics_data.splitlines() if not l.startswith('#')]:
            # Extract the metric value from the line
            parts = line.split()
            name = parts[0]
            value = float(parts[-1])  # The value is the last part of the line
            current_values[name] = value

        # Get the current time
        current_time = time.time()

        system('clear')
        for m in COUNTER_METRICS:
            rate_of_change = (current_values[f'{m}_total'] - prev_values[f'{m}_total']) / (current_time - prev_time)
            print(f"Rate of change for {m}: {rate_of_change} units/second")
        
        for m in SUMMARY_METRICS:
            average = current_values[f'{m}_sum'] / current_values[f'{m}_count']
            print(f"Average for {m}: {average} s")
        
        prev_values = current_values
        prev_time = current_time

    except Exception as e:
        print(e)

    # Wait for the next interval
    time.sleep(INTERVAL)