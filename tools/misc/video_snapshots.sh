#!/bin/bash

# This scripts purpose is to continuously collect snapshots from video streams
# Please adjust fps and file name padding to your liking

ffmpeg -rtsp_transport tcp -i rtsp://localhost:8554/video-stream -vf fps=1/10 -q:v 1 out%04d.jpg