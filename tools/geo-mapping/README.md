# How-To Run

## Prerequisites
- A camera snapshot (i.e. an image from the camera perspective)
- GPS location of the camera
- A means to determine pixel locations in image space (e.g. an image editor like GIMP)
- A means to determine geo coordinates on a satellite image (e.g. Google Maps in satellite view)

## Create parameters file
- Copy `autofit.yaml` template to a new file
- Set image_path at the top to the camera snapshot
- Fill in camera location under `camera_parameters.gps_location`
- Under `camera_parameters.spatial_orientation` set initial values and valid ranges for `heading_deg` and `elevation_m`
  - Heading in degrees can be estimated from the camera snapshot (draw a vertical line through the frame center and cross reference with a satellite image)
  - It is usually a good idea to give the algorithm some wiggle room even if the known values should be precise (i.e. allow for +/- 5°,  +/- 1m)
- Under `landmarks` add points that reference image pixel coordinates to geo coordinates

## Run autofitting script
- Use Python 3.11 (pandas < 2.0.0 is apparently not compatible with python >= 3.12 and cameratransform is not updated anymore, so we're stuck with this)
- Install dependencies
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Run autofitting script
  - Because we also need horizontal angle of view, the script runs multiple rounds of optimization with separate angles of views
  - Run script with a coarse search interval (of angle of view) to find rough sweet spot
    ```bash
    # Example values for standard wide angle camera
    python autocameratransform.py -l 80 -u 120 -s 5 autofit.xyz.yaml
    ```
  - Run script a second time with a finer interval to find best angle of view
    ```bash
    # Example values, depends on output from coarse search
    python autocameratransform.py -l 82 -u 92 -s 1 autofit.xyz.yaml
    ```
  - Check the output images (esp. `info.png` and `topview.png` which should yield a pretty good intuition on how good the mapping is)