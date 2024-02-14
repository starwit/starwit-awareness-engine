# How-To Build and Publish
```sh
cd sae/
helm dependency build
helm package .
helm push sae-x.tgz oci://registry-1.docker.io/starwitorg
```