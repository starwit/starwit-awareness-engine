# Object-Detector model deployment container
This container copies all its model weights into a certain directory upon start.
The idea is to ship weights in images of this and use this as an init container in Kubernetes,
mounting a volume (as a weights target) that will then be mounted into the object-detector container
once init has completed.
## How-To create a new release
- Move the .pt file you want to release into `./weights`
- Run the openvino export for deployment on Intel\
  `yolo export format=openvino model=weights.pt imgsz=1280 half=True dynamic=True nms=True`
- Optionally run the tensorrt optimization for deployment on NVIDIA (this has a lot of constraints, like TensorRT version, CUDA version, GPU architecture, etc.)
- Run `docker_build.sh` and choose a tag
- Run `docker_push.sh`