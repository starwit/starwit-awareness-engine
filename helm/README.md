# How-To Install
`helm install sae oci://registry-1.docker.io/starwitorg/sae`

# How-To Build and Publish
```sh
cd sae/
helm dependency build
helm package .
helm push sae-x.tgz oci://registry-1.docker.io/starwitorg
```

# Changelog
**Breaking changes (esp. with regard to config format) should only happen on major version bumps (i.e. you should be fine with just upgrading in all other cases)**
## 7.1.1
- Fix Bitnami charts, uses bitnamilegacy now; Long-term solution is needed
## 7.1.0
- Update components
  - `position-source` to 1.2.0
## 7.0.0
- Add `position-source`
- Add `detection-aggregator`
- Remove `geo-merger`
- Update components
  - `video-source` to 2.3.1 (supports setting camera position from position-source stream; supports NVIDIA hardware video decoder)
  - `object-detector` to 4.1.0 (supports Intel GPUs through openvino)
  - `object-tracker` to 3.3.0
  - `geo-mapper` to 0.10.0 (supports dynamic position mode)
  - `redis-writer` to 2.0.2 (support more flexible mapping; supports more message types)
- Config changes
  - All component configs now closer resemble actual individual config files -> all components now have a `settingsYaml` key in some way, which contains the settings.yaml contents and is used more consistently throughout the values, please refer to `customvalues.template.yaml` for details
  - Log levels are not set by helm anymore and need to be configured within the `settingsYaml` sections
  - `object-detector` had config changes (`inference_size` and `classes` now in `model`)
  - `redis-writer` had a major config update

## 6.3.0
- Update `geo-mapper` to 0.7.0 (update `vision-api` to 3.1.0), which now adds the configured camera location to the output message (`frame.camera_location`); in the case of `passthrough==True` a configured location is still honoured, i.e. added to the message

## 6.2.0
- Update `geo-mapper` to 0.6.0 (adds `remove_unmapped_detections` feature extending geo-filtering)

## 6.1.0
- Update `geo-mapper` to 0.5.0 (adds geo-filtering feature)

## 6.0.2
- Update `sae-redis-writer` to 1.2.2, which fixed a memory leak (would occur when connection was down and writer started buffering messages)

## 6.0.1
- `object-tracker`: Change default Kalman parameters (`Q_xy_scaling`, `Q_s_scaling`) to values we have empirically found to perform better in typical traffic observation use cases

## 6.0.0
- `object-detector`: Do not filter classes by default (i.e. if `classes` was unset before, only cars were detected, now the filter is off when unset) -> if your config didn't include a `classes` filter and you were only interested in cars, you have to explicitly add that now, otherwise no config change needed

## 5.0.2
- Increase default Valkey CPU limit (to 500mCPU)

## 5.0.1
- Increase default Valkey memory limit (from 192MiB to 512MiB) to help with high-throughput scenarios

## 5.0.0
- Add capability to run multiple instances of `redis-writer`, i.e. multiple data targets -> `config` key is now `configs` and holds a list; each config is as before with the exception of a unique `name` that must be added

## 4.0.0
- Separate model weights from `object-detector` image. It is now possible to feed custom weights for the YOLO model via a Docker image, check `tools/sae-object-detector-weights` for how to build such an image -> **you HAVE to change the config here**, check values template for the correct format (in the simplest case, you have to set `weights_path` to e.g. `yolov8m.pt` if you use default weights)

## 3.0.0
- `object-detector` is fully configurable now (i.e. everything below key `config` is passed to the object-detector as content in `settings.yaml`) -> the config format must now match `settings.yaml` of the component (see `values.template.yaml` or `object-detector` repo for details)
- No functionality changes

## 2.13.0
- Update `object-detector` to 2.4.0 (adds `drop_edge_detections` feature)

## 2.12.0
- Update `geo-mapper` to 0.4.0 (additional mapping options)

## 2.11.0
- Update `object-tracker` to 3.1.0

## 2.10.2
- Complete Valkey migration (init containers)

## 2.10.1
- Switch from Redis to Valkey

## 2.10.0
- Add `geo-merger` (disabled by default)
- Update `video-source` to 1.0.1

## 2.9.1
- Add message counter metric to `redis-writer`

## 2.9.0
- Update `redis-writer` to 1.2.0 (improve performance on high RTT links by using pipelined redis client, effectively batching messages)