from math import cos, radians, sqrt
from typing import Any, Dict, Optional

import cameratransform as ct
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import yaml
from cameratransform import Camera


class Camerafit():
    def __init__(self, camerajson: Optional[str] = None, fitconfig: Optional[str] = None, 
                 px_location: Optional[npt.ArrayLike] = None, gps_location: Optional[npt.ArrayLike] = None) -> None:

        if camerajson is not None:
            self.camera: Camera = ct.Camera.load(camerajson)
            print('Camera loaded with pre-defined parameter')
        else:
            if fitconfig is None:
                raise ValueError('Either pre-defined camera parameter and auto-fitting parameter are missing')
            else: 
                print('Trying to autofit camera')
                self.camera = self._camera_fitting(fitconfig, px_location, gps_location)
        
        self.px_location = px_location
        self.gps_location = gps_location
        self.data: Dict[str, Any]
        self.img: np.ndarray

    def _camera_fitting(self,fitconfig,px_location, gps_location) -> Camera:
        self.data = self._load_camera_settings(fitconfig)
        self.img = plt.imread(self.data['IMG_DIR'])
        camera = self._initialize_camera(self.data, self.img)
        space_location = camera.spaceFromGPS(gps_location)
        camera.addLandmarkInformation(px_location,space_location,[1,1,1e-2])
        fit_parameters = self._create_fit_parameters(
        self.data['Cam_pre_setting_parameters']['SpatialOrientation_parameters'],
        self.data['Cam_pre_setting_parameters']['BrownLensDistortion_parameters']
    )
        trace = camera.metropolis(fit_parameters, iterations=self.data['Iteration_num'])

        # Print all camera parameters after fitting
        print("All Camera Parameters After Fitting:")
        for attr, value in camera.__dict__.items():
            print(f"{attr}: {value}")

        return camera
            
    def _create_fit_parameters(spato_params, brownld_params):
        """Create a list of FitParameters for missing values to be optimized."""
        fit_parameters = []

        # Add missing spatial orientation parameters to fit
        if spato_params['elevation_m'] is None:
            fit_parameters.append(ct.FitParameter("elevation_m", lower=0, upper=25, value=10))
        if spato_params['tilt_deg'] is None:
            fit_parameters.append(ct.FitParameter("tilt_deg", lower=0, upper=180, value=60))
        if spato_params['roll_deg'] is None:
            fit_parameters.append(ct.FitParameter("roll_deg", lower=-180, upper=180, value=0))
        if spato_params['heading_deg'] is None:
            fit_parameters.append(ct.FitParameter("heading_deg", lower=0, upper=360, value=0))

        # Add missing lens distortion parameters to fit
        if brownld_params['k1'] is None:
            fit_parameters.append(ct.FitParameter("k1", lower=-1.5, upper=1.5, value=0))
        if brownld_params['k2'] is None:
            fit_parameters.append(ct.FitParameter("k2", lower=-0.2, upper=0.2, value=0))
        if brownld_params.get('k3') is None:  # Optional third parameter
            fit_parameters.append(ct.FitParameter("k3", lower=-0.2, upper=0.2, value=0))

        return fit_parameters
        
    def _load_camera_settings(self, filepath):
        """Load camera settings from a YAML file."""
        with open(filepath, 'r') as file:
            data = yaml.safe_load(file)
        return data
        
    def _initialize_camera(self, data, image):
        """Initialize the camera with parameters from the YAML data."""
        rectl_params = data['Cam_pre_setting_parameters']['RectilinearProjection_parameters']
        spato_params = data['Cam_pre_setting_parameters']['SpatialOrientation_parameters']
        brownld_params = data['Cam_pre_setting_parameters']['BrownLensDistortion_parameters']
        gps_params = data['Cam_pre_setting_parameters']['GPS']

        # Define camera with conditional parameters
        camera = ct.Camera(
            projection=ct.RectilinearProjection(
                image=image,
                focallength_mm=rectl_params['focallength_mm'],
                view_x_deg=rectl_params['view_x_deg'],
                view_y_deg=rectl_params['view_y_deg'],
                sensor_width_mm=rectl_params['sensor_width_mm'],
                sensor_height_mm=rectl_params['sensor_height_mm']
            ),
            orientation=ct.SpatialOrientation(
                heading_deg=spato_params['heading_deg'],
                tilt_deg=spato_params['tilt_deg'],
                roll_deg=spato_params['roll_deg'],
                pos_x_m=spato_params['pos_x_m'],
                pos_y_m=spato_params['pos_y_m'],
                elevation_m=spato_params['elevation_m']
            ),
            lens=ct.BrownLensDistortion(
                k1=brownld_params['k1'],
                k2=brownld_params['k2'],
                k3=brownld_params.get('k3', 0)
            )
        )
        camera.setGPSpos(gps_params[0], gps_params[1])
        return camera
    

    def _create_fit_parameters(self, spato_params, brownld_params):
        """Create a list of FitParameters for missing values to be optimized."""
        fit_parameters = []

        # Add missing spatial orientation parameters to fit
        if spato_params['elevation_m'] is None:
            fit_parameters.append(ct.FitParameter("elevation_m", lower=0, upper=25, value=10))
        if spato_params['tilt_deg'] is None:
            fit_parameters.append(ct.FitParameter("tilt_deg", lower=0, upper=180, value=60))
        if spato_params['roll_deg'] is None:
            fit_parameters.append(ct.FitParameter("roll_deg", lower=-180, upper=180, value=0))
        if spato_params['heading_deg'] is None:
            fit_parameters.append(ct.FitParameter("heading_deg", lower=0, upper=360, value=0))

        # Add missing lens distortion parameters to fit
        if brownld_params['k1'] is None:
            fit_parameters.append(ct.FitParameter("k1", lower=-1.5, upper=1.5, value=0))
        if brownld_params['k2'] is None:
            fit_parameters.append(ct.FitParameter("k2", lower=-0.2, upper=0.2, value=0))
        if brownld_params.get('k3') is None:  # Optional third parameter
            fit_parameters.append(ct.FitParameter("k3", lower=-0.2, upper=0.2, value=0))
        return fit_parameters
    
    def _calculate_distances(self, calculated_points, groundtruth_points):
        """Calculate distances between calculated and ground truth GPS points."""
        distances = [
            self._gps_distance_m(calc[0], calc[1], gt[0], gt[1])
            for calc, gt in zip(calculated_points, groundtruth_points)
        ]
        return distances
    
    def _gps_distance_m(self, lat1, lon1, lat2, lon2):
        """Calculate the approximate distance between two GPS coordinates in meters."""
        lat_dist_m = 111320 * (lat2 - lat1)
        lon_dist_m = 111320 * cos(radians(lat1)) * (lon2 - lon1)
        return sqrt(lat_dist_m**2 + lon_dist_m**2)


    def topview(self):
        if self.data['TOPVIEW']['do_plot']:
            return self.camera.getTopViewOfImage(self.img, extent=(-80,20,-20,80), scaling=0.05)
        
    def save_cam(self):
        if self.data['SAVE_CAM']:
            self.camera.save('fitted_cam.json')

    def show_perf(self):
        calculated_points = self.camera.gpsFromImage(self.px_location, Z=0)
        distances = self._calculate_distances(calculated_points, self.gps_location)
        average_distance = sum(distances) / len(distances)
        print(f"Average Distance: {average_distance:.2f} meters")