# Starwit Awareness Engine (formerly Vision Pipeline)
This is an umbrella repository containing much of the documentation and orchestration code for the Starwit Awareness Engine.
It links to all relevant components and is meant to be the place to start exploring the SAE project.

## Repositories
The components of the vision pipeline can be found in the following repositories:
| Component        | Repository / URI                                                   |
| ---------------- | ------------------------------------------------------------------ | 
| Video Source     | https://github.com/starwit/video-source-py                         |
| Object Detector  | https://github.com/starwit/object-detector                         |
| Object Tracker   | https://github.com/starwit/object-tracker                          |
| Geo-Mapper       | https://github.com/starwit/geo-mapper                              |
| Database Writer  | https://github.com/starwit/vision-api-jms-client                   |
| vision-api       | https://github.com/starwit/vision-api                              |
| vision-lib       | https://github.com/starwit/vision-lib                              |

## Contents
- [`/doc`](doc/README.md) - Documentation of the architecture and some details of the technical setup
- [`/helm/sae`](helm/sae) - The main Helm chart
- [`/docker-compose`](docker-compose/README.md) - A docker compose version of the pipeline (should be more or less up-to-date with the Helm chart)
- [`/tools`](tools/README.md) - Contains the [`watch`](tools/watch.py) script which makes visually introspecting the pipeline easy (can render image output for every stage)
- [`/nvidia`](nvidia/notes.md) - Some rough documentation about setting up K3s with Nvidia properly (needs to be extended / automated)
- [`/dashboards`](dashboards/) - A place to save created dashboards for viewing the pipeline metrics (not part of the demo setup yet)

<<<<<<< HEAD
## How-To Prod Install

### Installation Steps
1. Set up K3s cluster
=======
## SemVer conventions
As this is highly debatable, here is what we are currently trying to maintain:
- Patch version: This is increased if neither the public API of the artifact in question is changed nor any new features are implemented. Upgrade should be possible without any changes to config or setup. Dependency bumps are also included, if the preceding constraints are fulfilled.
- Minor version: This is increased if the component changes its public API in a downwards compatible way (that usually means the new feature extends the existing functionality and has some sane defaults). Upgrade should be possible without any changes to the configuration.
- Major version: This is increased if the component changes its public API in a non-downwards-compatible way and changes to configuration / infrastructure / etc. have to be made to upgrade.

## How-To Prod Install

### Installation Steps
1. Set up K3s cluster \
    `curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--tls-san <tailscale_host_name> --write-kubeconfig-mode 644 --disable traefik --disable servicelb" sh -`
    - `--tls-san` only has to be set if the hostname the cluster is suppose to be managed through is not equal to the actual hostname (e.g. it is on Tailscale)
    - As we currently do not open any ports and do not host publicly host any services `traefik` and `servicelb` can be disabled
    - `--write-kubeconfig-mode 644` enables managing the cluster through any user on the machine
>>>>>>> main
    - If the machine you install K3s on has a NVIDIA GPU available and want to use it for running the pipeline, 
    you have to follow the instructions in [`./nvidia/notes.md`](nvidia/notes.md)
2. Install Timescale DB (if do not have one on another machine and you want to store the pipeline output data)
    - Create a database for pipeline data and a table / hypertable. See [`./doc/database.md`](doc/database.md) for instructions.
3. Install SAE
<<<<<<< HEAD
    - Set up internal Starwit Helm repo (see Bitwarden for credentials)
        ```sh
        helm repo add starwit-internal https://helm.internal.starwit-infra.de --username chartmuseum --password-stdin < <(read -s -p "Password: "; echo $REPLY)
        helm repo update
        ```
=======
>>>>>>> main
    - Copy the values template file and adapt it to your needs (see the file for information)
        ```sh
        cp ./helm/sae/customvalues.template my.values.yaml
        ``` 
    - Install helm chart
        ```sh
<<<<<<< HEAD
        helm install <release-name> starwit-internal/sae -f my.values.yaml
=======
        helm install <release-name> oci://registry-1.docker.io/starwitorg/sae -f my.values.yaml
>>>>>>> main
        ```
4. Set up and use the watch tool in [`tools/`](tools/watch.py) to inspect the pipeline visually
5. Check out the internal pipeline metrics
    - Forward Grafana port to your local machine and log in (user admin, password admin)
    - Import dashboard [`./dashboards/sae_overview.json`](/dashboards/sae_overview.json) into Grafana

## How-To Dev
There are many ways of how to run the pipeline for local developments on individual components.
Because all components communicate through Redis streams it does not matter where or how the pipeline is running.
As long as the Redis port of the pipeline instance is available on the local machine, a locally started version
(possibly within the IDE, e.g. in debug mode) can be hooked into the pipeline.
For port forwarding either k9s or `kubectl port-forward` can be used (or any other K8s tool).
The compose-based version of the pipeline can be used for maximum (or rather most convenient) 
control over individual components (see [`/docker-compose`](docker-compose/README.md)).
<<<<<<< HEAD
=======

## How-To create a new component / pipeline stage
See https://github.com/starwit/sae-stage-template on how to get started with a new component.
>>>>>>> main
