#!/bin/bash
read -p "Please enter a new version: " NEW_VERSION

if [ ! -z "$NEW_VERSION" ]; then
    TAG="$NEW_VERSION"
else
    echo "No version given. Exiting."
    exit 1
fi

docker build --build-arg CACHE_BUST="$(date)" -t starwitorg/sae-gpsd:${TAG} .

echo -n ${TAG} > TAG