# Vision Pipeline - Docker Compose
Run the Vision pipeline locally with Docker Compose, mirroring the Kubernetes deployment.

## Requirements
- Docker with Docker Compose
- An H.264-encoded video is required. If needed, see [this FFmpeg example](https://superuser.com/questions/1056599/ffmpeg-re-encode-a-video-keeping-settings-similar#answer-1056632).

## Quickstart
1. Copy `.env.template` to `.env`: 
```SHELL
cp .env.template .env
```
2. Set `VIDEO_PATH` in `.env`: `VIDEO_PATH=/absolute/path/to/car_video.mp4` 
> **Important:** `VIDEO_PATH` is mounted into `streaming-server`.
> The `video source` expects a paced stream. Otherwise 
> it will consume the file as fast as possible.
3. Run (the first time may take a while, some images are large)  
```SHELL
docker compose up -d
``` 

## Inspect the pipeline using sae-watch
Use `sae-watch` from [sae-introspection](https://github.com/starwit/sae-introspection) to inspect pipeline streams visually.

Requires Python >= 3.10

```SHELL
sudo apt install libturbojpeg0
pipx install git+https://github.com/starwit/sae-introspection.git
sae-watch
```

Select a stream to inspect the pipeline visually.

## Configuration
- `.env`: local paths and environment variables
- `video-source-py/video-source-stream1.settings.yaml`: video source settings
- `object-detector/...settings.yaml`: detector settings

## Use database output - PostgreSQL
Store the tracker output in a Postgres DB (what prod deployments do).

Run the pipeline with PostgreSQL enabled:
```SHELL
docker compose -f docker-compose-with-db.yaml up -d
```

Then visit http://localhost:5050 in your browser (pgadmin web UI).

## Troubleshooting

### Low FPS / high CPU
If oyu get inconsistent framerates or your machine gets slow, try lowering the max_fps value on the video-source.
Or try [NVIDIA GPU support](#nvidia-gpu-support).

Lower `max_fps` in:
`video-source-py/video-source-stream1.settings.yaml`

For example:
```yaml
max_fps: 5
```

### sae-watch doesn't recognise vidoestreams
Is your video H.264-encoded?

Running `sae-watch` only shows this available stream:
```
"positionsource:self"
```

1. Stop the setup: 
```SHELL
docker compose down -v
```
2. Reencode your video, using [ffmpeg](https://trac.ffmpeg.org/wiki/Encode/H.264):
```SHELL
ffmpeg -i input.webm -c:v libx264 -crf 23 output.mp4
```
3. Fix the `VIDEO_PATH` in `.env` to the newly encoded file
4. Run the setup:
```SHELL
docker compose up -d
```

## Documentation
The default Compose setup runs:

Valkey --> video source --> object detector --> object tracker --> streaming server

See [architecture and technical documentation](../doc/README.md).


## NVIDIA GPU support
If you have a Nvidia GPU in your system:
- Try changing the `device` on object-detector and -tracker from `cpu` to `cuda`. 
No guarantees whether that will work!

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
  - In the case of `object-detector` change `model.device` in its settings file (by default at `./object-detector/object-detector.settings.yaml`) from `cpu` to `cuda`.
