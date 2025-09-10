#!/bin/bash

if [ ! -f TAG ]; then
    read -p "Please enter image tag to push: " TAG
else
    TAG=$(cat TAG)
fi

docker push starwitorg/sae-gpsd:${TAG}