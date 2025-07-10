# Installation Guides
Awareness Engine can be deployed in various ways. In this section all necessary steps for every variant are described.
So far the following scenarios are supported:
* Deployment on Kubernetes clusters (recommended productive mode)
* Docker Compose
* Installation via APT packages (embedded deployment)

Please note, that regardless of deployment method - SAE works in all of them with the same general concepts described [here](../README.md).

## Installation on Kubernetes cluster
1. Set up K3s cluster \
    - Create K3s config file (adapt the value of `tls-san`)
        ```yaml
        write-kubeconfig-mode: "0644"
        tls-san:
            - "TAILSCALE_HOSTNAME"
        disable:
            - servicelb
            - traefik
        ```
        - `tls-san` only has to be set if the hostname the cluster is supposed to be managed through is not equal to the actual hostname (e.g. it is on Tailscale)
        - As we currently do not open any ports and do not host publicly host any services `traefik` and `servicelb` can be disabled
        - `--write-kubeconfig-mode 644` enables managing the cluster through any user on the machine
    - Install K3s `curl -sfL https://get.k3s.io | sh -s -` (use the same command for upgrading, assuming you have the config file in place)
    - If the machine you install K3s on has a NVIDIA GPU available and wants to use it for running the pipeline, 
    you have to follow the instructions in [`./nvidia/notes.md`](nvidia/notes.md)
2. Install Timescale DB (if do not have one on another machine and you want to store the pipeline output data)
    - Create a database for pipeline data and a table / hypertable. See [`./doc/database.md`](doc/database.md) for instructions.
3. Install SAE
    - Copy the values template file and adapt it to your needs (see the file for information)
        ```sh
        cp ./helm/sae/customvalues.template my.values.yaml
        ``` 
    - Install helm chart
        ```sh
        helm install <release-name> oci://registry-1.docker.io/starwitorg/sae -f my.values.yaml
        ```
4. Set up and use the watch tool in [`tools/`](tools/watch.py) to inspect the pipeline visually
5. Check out the internal pipeline metrics
    - Forward Grafana port to your local machine and log in (user admin, password admin)
    - Import dashboard [`./dashboards/sae_overview.json`](/dashboards/sae_overview.json) into Grafana

## Docker Compose

Docker Compose is described in detail in [this section](../../docker-compose/README.md).

## APT/Debian package installation
On some embedded devices Docker may not be an option, so SAE components are also shipped into installable Debian packages. So far embedded installation targets at running all necessary SAE components, such that on a device tracked objects are geo-mapped. 

This way application developers can decide, whether to use collected data, to implement function directly in hardware, or to forward aggregated information to a receiving backend. See section [sample use cases](../usage-scenarios.md) for more details.

Packages are published as release in every component. This table contains links to each package.

| Component        | Repository / URI                                           |
| ---------------- | ---------------------------------------------------------- |  
| Video Source     | https://github.com/starwit/video-source-py/releases        |
| Object Detector  | https://github.com/starwit/object-detector/releases        |
| Object Tracker   | https://github.com/starwit/object-tracker/releases         |
| Geo-Mapper       | https://github.com/starwit/geo-mapper/releases             |
| Redis Writer     | https://github.com/starwit/sae-redis-writer/releases       |

For future release setting up a proper package source is under consideration.

### Installation steps

The following installation steps are the same for all Linux derivates. For distro-specific steps see section(s) below.

* Install ValKey (see [here](https://github.com/starwit/linux-tools) for help)
* Download *.deb file for each component
* Create folder /etc/starwit and place config files (see next section)
* Install all component (see above table for order) using:
    ```bash
    apt install ./package_for_component.deb
    ```
You can skip config file step, but then each component will install a config file with default values - which needs to be adapted.

### Configuration
The following table is an overview of all configuration files
| Component        | Example Config File                                             | Notes |
| ---------------- | ----------------------------------------------------------      | ----------- |
| Video Source     | [settings.yaml](apt-configuration/videosource/settings.yaml)    | video sources coordinates (RTSP, usename/password) |
| Object Detector  | [settings.yaml](apt-configuration/objectdetector/settings.yaml) | Select detection model, inferencing size,... |
| Object Tracker   | [settings.yaml](apt-configuration/objecttracker/settings.yaml)  | Select tracking method |
| Geo-Mapper       | [settings.yaml](apt-configuration/geomapper/settings.yaml)      | Provide geo coordinates of camera |
| Redis Writer     | [settings.yaml](apt-configuration/rediswriter/settings.yaml)    | Transfer data to backend |


### Nvidia Jetson

```bash
# Add Nvidia Sources
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/arm64/cuda-keyring_1.1-1_all.deb
sudo apt install ./cuda-keyring_1.1-1_all.deb

# avoid possible version conflict
sudo apt remove python3-sympy
```
