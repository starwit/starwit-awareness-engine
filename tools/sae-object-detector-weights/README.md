# Object-Detector model deployment container
This container copies all its model weights into a certain directory upon start.
The idea is to ship weights in images of this and use this as an init container in Kubernetes,
mounting a volume (as a weights target) that will then be mounted into the object-detector container
once init has completed.