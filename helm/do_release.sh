#!/bin/bash

(
    cd sae/
    rm sae-*.tgz
    helm dependency build
    helm package .
    helm push sae-*.tgz oci://registry-1.docker.io/starwitorg
)