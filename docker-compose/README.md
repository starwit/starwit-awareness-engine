# Docker-Compose Version Of The Vision Pipeline
This repository aims at replicating the Helm/Kubernetes-based vision pipeline for local development as closely as possible. It might not always be up-to-date...

## Documentation
A longer explanation of the architecture and the technical setup can be found in `../doc/README.md`.

## Quickstart
1. Change `VIDEO_PATH` in `.env` to a video on your machine
2. Run `docker compose up`
3. Have a look at the `watch.py` et al. in `../tools` (also see its readme)

### Database output
If you want to have database output, i.e. store the tracker output in a Postgres DB (which is what prod deployments do), you can replace step 3 from above to `docker compose -f docker-compose-with-db.yaml up`. You'll find a pgadmin web UI to browse the database at http://localhost:5050.

## How-To Dev
All relevant components (Redis and Postgres) have healthchecks in place, s.t. `docker compose up` should "just work".\
In order to have more control you might want to start all components separately (e.g. in tmux panes).
For a working (basic) pipeline you need (at least) the following components running (which is what `docker compose up` will give you by default):
- redis
- video-source-py
- object-detector
- object-tracker
- streaming-server

For the video source you either need to have a video stream readily available (and configure its uri accordingly) or you can use the streaming-server compose service, which will play a video file on demand (that you have to mount, that is what `VIDEO_PATH` in `.env` is for).\
**Caution:** Do not try to mount the video file directly into the video source container. This is currently not supported as the video source relies on the source to pace itself, the video source will read frames as fast as possible!

If you have a Nvidia GPU in your system, you can try changing the `device` on object-detector and -tracker from `cpu` to `cuda`. No guarantees whether that will work!

## Visual Pipeline Introspection
The `../tools/watch.py` script can be used to visually look into the data flows within the pipeline. See more detailed description it its readme.