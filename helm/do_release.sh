#!/bin/bash

if [[ -z "$HELM_REPO_USER" ]]; then
    if [[ $CI == "true" ]]; then
        echo "HELM_REPO_USER must be set!"
        exit 1
    else 
        read -p "HELM_REPO_USER: " HELM_REPO_USER
    fi
fi

if [[ -z "$HELM_REPO_PASSWORD" ]]; then
    if [[ $CI == "true" ]]; then
        echo "HELM_REPO_PASSWORD must be set!"
        exit 1
    else 
        read -s -p "HELM_REPO_PASSWORD: " HELM_REPO_PASSWORD
    fi
fi

OLD_PWD=$(pwd)
CHART_DIR=$(dirname "$0")/sae

echo "Changing into chart directory directory: $CHART_DIR"
cd $CHART_DIR

helm dependency build || exit 1
helm package . || exit 1

FILES=(sae-*.tgz)
CHART_FILE=${FILES[0]}

echo "Uploading chart package..."
cat $CHART_FILE | curl -i -u $HELM_REPO_USER:$HELM_REPO_PASSWORD --data-binary @- https://helm.internal.starwit-infra.de/api/charts || exit 1
echo ""

rm sae-*.tgz

echo "Restoring old PWD: $OLD_PWD"
cd $OLD_PWD

exit 0