#!/bin/bash

# Define video sources
sources=("rtsp://localhost:8554/video-stream" "rtsp://localhost:8554/video-stream")  # Replace these with actual video source names/URLs
output_files=("output1.mp4" "output2.mp4")  # Replace these with desired output file names

start_time=$(date --iso-8601=sec)

(
    # Start recording each video source
    for i in "${!sources[@]}"; do
        ffmpeg -nostdin -rtsp_transport tcp -i "${sources[$i]}" -c copy "file:${start_time}-${output_files[$i]}" &
    done

    trap '' INT TERM

    wait
)
