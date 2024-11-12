#!/bin/bash

# This scripts purpose is to continuously collect snapshots from video streams
# Please adjust fps and file name padding to your liking
# If there is an image file "${cam_id}_mask.png" it will be used to mask the image (black=blacken; white=keep)

SNAPSHOT_INTERVAL_S=600
SNAPSHOT_DIRECTORY=./snapshots

mkdir -p ${SNAPSHOT_DIRECTORY}

# Define video sources (e.g. URL)
sources=(
        "source1"
        "source2"
)  

# These will be used to prefix the corresponding output files
cam_ids=(
        "source-name1"
        "source-name2"
)

# Start recording each video source
for i in "${!sources[@]}"; do
    if [ -f "${cam_ids[$i]}_mask.png" ]; do
        ffmpeg -nostdin -rtsp_transport tcp -i "${sources[$i]}" -i "${cam_ids[$i]}_mask.png" -filter_complex "[1:v]colorkey=white[ckout];[0:v][ckout]overlay[ov];[ov]fps=1/${SNAPSHOT_INTERVAL_S}[out]" -map "[out]" -q:v 1 "file:${SNAPSHOT_DIRECTORY}/${cam_ids[$i]}_${RANDOM}_%05d.jpg" &
    else
        ffmpeg -nostdin -rtsp_transport tcp -i "${sources[$i]}" -vf fps=1/${SNAPSHOT_INTERVAL_S} -q:v 1 "file:${SNAPSHOT_DIRECTORY}/${cam_ids[$i]}_${RANDOM}_%05d.jpg" &
    fi
done

wait
