#!/bin/bash
if [ -z "$TAG" ]; then
    read -p "Please enter image tag: " TAG
fi

docker build -t starwitorg/sae-object-detector-weights:${TAG} .

echo -n ${TAG} > TAG