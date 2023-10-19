# Vision Pipeline (SAE core) for Kubernetes / Docker Compose
This repository contains much of the documentation and orchestrating configuration for the container-based vision pipeline (which is the only supported version now).

## Repositories
The components of the vision pipeline can be found in the following repositories:
| Component        | Repository / URI                                                   |
| ---------------- | ------------------------------------------------------------------ | 
| Helm Chart (sae) | https://github.com/starwit/helm-charts/tree/main/charts/sae        | 
| Video Source     | https://github.com/starwit/video-source-py                         |
| Object Detector  | https://github.com/starwit/object-detector                         |
| Object Tracker   | https://github.com/starwit/object-tracker                          |
| Database Writer  | https://github.com/starwit/vision-api-jms-client                   |
| vision-api       | https://github.com/starwit/vision-api                              |
| vision-lib       | https://github.com/starwit/vision-lib                              |

## Contents
- `/doc` - Documentation of the architecture and some details of the technical setup
- `/helm/sae` - The main Helm chart
- `/docker-compose` - A docker compose version of the pipeline (should be more or less up-to-date with the Helm chart)
- `/tools` - Contains the `watch` script which makes visually introspecting the pipeline easy (can render image output for every stage)
- `/nvidia` - Some rough documentation about setting up K3s with Nvidia properly (needs to be extended / automated)
- `/dashboards` - A place to save created dashboards for viewing the pipeline metrics (not part of the demo setup yet)