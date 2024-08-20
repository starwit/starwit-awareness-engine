# Docker-Compose Version Of The Vision Pipeline
This repository aims at replicating the Helm/Kubernetes-based vision pipeline for local development as closely as possible. It might not always be up-to-date...

## Documentation
A longer explanation of the architecture and the technical setup can be found in `../doc/README.md`.

## Quickstart
1. Copy .env.template and change the name of the copy to .env. Change `VIDEO_PATH` in `.env` to a suitable video file (showing cars) on your machine
2. Run `docker compose up` (the first time may take a while, some images are quite big)
3. Change into `../tools/sae_introspection`
  1. Install python3 venv (e.g. sudo apt install python3.11-venv)
  2. Create and activate a virtualenv (`python3 -m venv .venv && source .venv/bin/activate`)
  3. Install dependencies (`pip install -r requirements.txt`)
  4. Run `python watch.py` and choose a stream to watch

Hint: You need Python 3.11 for sae components. If you just want to test with scripts in `tools\sae_introspection`, you can use Python 3.12.

If you do not get a consistent framerate or your machine gets slow, try lowering the `max_fps` value on the video-source (i.e. 5 fps) in `./video-source-py/video-source-stream1.settings.yaml`. Also, you might want to try setting up your Nvidia GPU, if you have one (see below).

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

## How-To Use Nvidia GPU
- Install `nvidia-container-toolkit` (see https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installing-with-apt)
- Configure NVIDIA container toolkit (see https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuring-docker)
- Test if the Nvidia runtime works (https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/sample-workload.html#running-a-sample-workload-with-docker)
- Enable GPU support for compose services, where you want it (e.g. `object-detector`)
  Add the following section to each service that needs GPU support:
  ```yaml
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
  ```
- Configure application to use Nvidia CUDA
  - In the case of `object-detector` change `model.device` in its settings file (by default at `./object-detector/object-detector.settings.yaml`) from `cpu` to `cuda`