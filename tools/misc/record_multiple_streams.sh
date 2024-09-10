#!/bin/bash

# This scripts purpose is to read a number of name;stream-uri pairs from a CSV file and record all streams in parallel.

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path_to_csv_file>"
  exit 1
fi

csv_file="$1"

if [ ! -f "$csv_file" ] || [ ! -r "$csv_file" ]; then
  echo "Error: File '$csv_file' does not exist or is not readable."
  exit 1
fi

trap 'exit 1' SIGINT SIGTERM 

mkdir -p recordings

start_time=$(date --iso-8601=sec)

while IFS=';' read -r name uri; do
    ffmpeg -nostdin -rtsp_transport tcp -i "${uri}" -c:v copy "file:recordings/${start_time}-${name}.mp4" &
done < "$csv_file"