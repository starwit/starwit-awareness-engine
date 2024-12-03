# Object-Detector Performance Tuning (i.e. what are our biggest bottlenecks)
In general, it is quite challenging to saturate even a modest GPU with input data (images).

## Low-Hanging Fruit (all tested with YOLOv8m)
- TensorRT-optimize the model on the GPU it will be running on (or a very similar one); see object-detector repo for details and code samples -> roughly 200% increase in throughput
- Do not use standard square inference sizes but restrict to the exact resolution (or rather a multiple of 32 in both dimensions) of the video frames (e.g. 1280x736 for 1280x720 frames) -> roughly 30% increase in throughput for 16:9 frames compared to square
  - not all configurations benefit from this, but TensorRT does almost linearly (w.r.t. input pixel count)
- Run multiple object-detectors in parallel to improve GPU usage (one Python process is currently not enough to saturate a RTX A2000) -> roughly 40% increase in throughput

## Detailed performance testing
### Loop times (JPEG mode; order of magnitude; not scientifically tested)
- JPEG decoding: 3ms
- NMS: 1ms
- Proto deserialization (excluding JPEG decode): 1ms
- Proto serialization: 1ms
- Redis send/receive: .5ms each

### Results from performance testing on RTX 3070; YOLO8m (TensorRT-optimized); 1280px
- roughly 7ms inference time (model without NMS)
- one instance of object-detector manages a main loop time (redis input -> redis output) of 14ms, i.e. 70fps
- two instances of object-detector in parallel manage loop times of 22ms, i.e. 45fps each -> 90fps combined
- even being fed by two instances the GPU is still not saturated

### Tradeoffs and limits
- At 100fps and 1280px, we would have to move roughly 5GB/s to the model, which is a lot for network I/O
- JPEG decoding takes time, but the same goes for network I/O. I have found that it can be roughly equivalent (if we ignore load on redis instance)

### Where to go from here?
- Run two models in parallel and investigate the bottlenecks in Python code (CUDA seems to handle two parallel models well enough)
- Detailed optimization of python code (not sure how much potential is still left)
- Start to use multiprocessing to feed the GPU (there is torch.multiprocessing) -> multiprocessing in Python is quite complex
- Move model hosting into NVIDIA Triton (for example) -> then we have network overhead (see above)
- Reimplement the object-detector in another language that has more control over memory -> unclear, if that would improve things; Difficulty: official TensorRT bindings are only available for C++ and Python