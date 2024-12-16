import yaml
import argparse
from pathlib import Path

import cv2
from CameraFit import Camerafit, AutofitConfig

argparser = argparse.ArgumentParser()
argparser.add_argument('config_path', type=Path, help='The path to the autofit*.yaml')
args = argparser.parse_args()

with open(args.config_path, 'r') as f:
    yaml_config = yaml.safe_load(f)

config_obj = AutofitConfig.model_validate(yaml_config)

camera = Camerafit(fitconfig=config_obj)

camera.show_perf()
camera.plot_fit_information_image_space('info.png')
camera.plot_trace('trace.png')
cv2.imwrite('undistorted.png', camera.get_undistorted_image())

topview_im = camera.get_topview()
cv2.imwrite('topview.jpg', topview_im)

camera.save_cam()