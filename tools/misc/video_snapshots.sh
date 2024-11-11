#!/bin/bash

# This scripts purpose is to continuously collect snapshots from video streams
# Please adjust fps and file name padding to your liking

#!/bin/bash

SNAPSHOT_INTERVAL_S=600
SNAPSHOT_DIRECTORY=./snapshots

mkdir -p ${SNAPSHOT_DIRECTORY}

# Define video sources
sources=(
        "source1"
        "source2"
)  

# Replace these with actual video source names/URLs
cam_ids=(
        "source-name1"
        "source-name2"
)

# Start recording each video source
for i in "${!sources[@]}"; do
    ffmpeg -nostdin -rtsp_transport tcp -i "${sources[$i]}" -vf fps=1/${SNAPSHOT_INTERVAL_S} -q:v 1 "file:${SNAPSHOT_DIRECTORY}/${cam_ids[$i]}_${RANDOM}_%05d.jpg" &
done

wait
