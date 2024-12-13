from math import cos, radians, sqrt
from typing import Any, Dict, Optional, List, NamedTuple

import cameratransform as ct
import matplotlib.pyplot as plt
import numpy as np
from typing_extensions import Annotated
import numpy.typing as npt
import yaml
from cameratransform import Camera
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class RectilinearProjection(BaseModel):
    focallength_mm: Optional[float] = None
    view_x_deg: Optional[float] = None
    view_y_deg: Optional[float] = None
    sensor_width_mm: Optional[float] = None
    sensor_height_mm: Optional[float] = None

class SpatialOrientation(BaseModel):
    heading_deg: Optional[float] = None
    tilt_deg: Optional[float] = None
    roll_deg: Optional[float] = None
    elevation_m: Optional[float] = None
    pos_x_m: float = 0
    pos_y_m: float = 0

class BrownLensDistortion(BaseModel):
    k1: Optional[float] = 0
    k2: Optional[float] = 0
    k3: Optional[float] = 0

class GPSLocation(BaseModel):
    lat: float
    lon: float

class CameraParameters(BaseModel):
    rectilinear_projection: RectilinearProjection
    spatial_orientation: SpatialOrientation
    brown_lens_distortion: BrownLensDistortion
    gps_location: GPSLocation

class ImageCoords(NamedTuple):
    px_x: int
    px_y: int

class GPSCoords(NamedTuple):
    lat: float
    lon: float
    elevation_m: float

class Landmark(NamedTuple):
    image_coords: ImageCoords
    gps_coords: GPSCoords

class TopView(BaseModel):
    do_plot: bool
    extent: Annotated[list[int], Field(min_length=4, max_length=4)]
    m_per_pixel: float

class AutofitConfig(BaseModel):
    image_path: Path
    camera_parameters: CameraParameters
    landmarks: List[Landmark]
    iteration_num: int
    top_view: TopView
    save_cam: bool

    @property
    def gps_locations(self):
        return np.array([(lm.gps_coords.lat, lm.gps_coords.lon, lm.gps_coords.elevation_m) for lm in self.landmarks])
    
    @property
    def px_locations(self):
        return np.array([(lm.image_coords.px_x, lm.image_coords.px_y) for lm in self.landmarks])


class Camerafit():
    def __init__(self, camerajson: Optional[str] = None, fitconfig: AutofitConfig = None) -> None:

        self._fitconfig = fitconfig

        if camerajson is not None:
            self.camera: Camera = ct.Camera.load(camerajson)
            print('Camera loaded with pre-defined parameter')
        else:
            if fitconfig is None:
                raise ValueError('Either pre-defined camera parameter and auto-fitting parameter are missing')
            else: 
                print('Trying to autofit camera')
                self.camera = self._camera_fitting()
        
        self.img: np.ndarray

    def _camera_fitting(self) -> Camera:
        self.img = plt.imread(self._fitconfig.image_path)
        camera = self._initialize_camera()
        space_location = camera.spaceFromGPS(self._fitconfig.gps_locations)
        camera.addLandmarkInformation(self._fitconfig.px_locations, space_location, [1, 1, 1e-2])
        fit_parameters = self._create_fit_parameters()
        trace = camera.metropolis(fit_parameters, iterations=self._fitconfig.iteration_num)

        # Print all camera parameters after fitting
        print("All Camera Parameters After Fitting:")
        for attr, value in camera.__dict__.items():
            print(f"{attr}: {value}")

        return camera
    
    def _initialize_camera(self):
        """Initialize the camera with known parameters from fitconfig"""
        cam_params = self._fitconfig.camera_parameters

        rectl_params = cam_params.rectilinear_projection
        spato_params = cam_params.spatial_orientation
        brownld_params = cam_params.brown_lens_distortion
        gps_params = cam_params.gps_location

        # Define camera with conditional parameters
        camera = ct.Camera(
            projection=ct.RectilinearProjection(
                image=self.img,
                focallength_mm=rectl_params.focallength_mm,
                view_x_deg=rectl_params.view_x_deg,
                view_y_deg=rectl_params.view_y_deg,
                sensor_width_mm=rectl_params.sensor_width_mm,
                sensor_height_mm=rectl_params.sensor_height_mm
            ),
            orientation=ct.SpatialOrientation(
                heading_deg=spato_params.heading_deg,
                tilt_deg=spato_params.tilt_deg,
                roll_deg=spato_params.roll_deg,
                pos_x_m=spato_params.pos_x_m,
                pos_y_m=spato_params.pos_y_m,
                elevation_m=spato_params.elevation_m
            ),
            lens=ct.BrownLensDistortion(
                k1=brownld_params.k1,
                k2=brownld_params.k2,
                k3=brownld_params.k3
            )
        )
        camera.setGPSpos(gps_params.lat, gps_params.lon)
        return camera

    def _create_fit_parameters(self):
        """Create a list of FitParameters for missing values to be optimized."""
        spato_params = self._fitconfig.camera_parameters.spatial_orientation
        brownld_params = self._fitconfig.camera_parameters.brown_lens_distortion
        fit_parameters = []

        # Add missing spatial orientation parameters to fit
        if spato_params.elevation_m is None:
            fit_parameters.append(ct.FitParameter("elevation_m", lower=0, upper=25, value=10))
        if spato_params.tilt_deg is None:
            fit_parameters.append(ct.FitParameter("tilt_deg", lower=0, upper=180, value=60))
        if spato_params.roll_deg is None:
            fit_parameters.append(ct.FitParameter("roll_deg", lower=-180, upper=180, value=0))
        if spato_params.heading_deg is None:
            fit_parameters.append(ct.FitParameter("heading_deg", lower=0, upper=360, value=0))

        # Add missing lens distortion parameters to fit
        if brownld_params.k1 is None:
            fit_parameters.append(ct.FitParameter("k1", lower=-1.5, upper=1.5, value=0))
        if brownld_params.k2 is None:
            fit_parameters.append(ct.FitParameter("k2", lower=-0.2, upper=0.2, value=0))
        if brownld_params.k3 is None:
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
        if self._fitconfig.top_view.do_plot:
            return self.camera.getTopViewOfImage(self.img, extent=self._fitconfig.top_view.extent, scaling=self._fitconfig.top_view.m_per_pixel)
        
    def save_cam(self):
        if self._fitconfig.save_cam:
            self.camera.save('fitted_cam.json')

    def show_perf(self):
        calculated_points = self.camera.gpsFromImage(self._fitconfig.px_locations, Z=0)
        distances = self._calculate_distances(calculated_points, self._fitconfig.gps_locations)
        average_distance = sum(distances) / len(distances)
        print(f"Average Distance: {average_distance:.2f} meters")