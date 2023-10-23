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

SCRIPT_DIR=$(dirname "$0")

helm package $SCRIPT_DIR/sae -d $SCRIPT_DIR || exit 1

FILES=($SCRIPT_DIR/sae-*)
CHART_FILE=${FILES[0]}

cat $CHART_FILE | curl -i -u $HELM_REPO_USER:$HELM_REPO_PASSWORD --data-binary @- https://helm.internal.starwit-infra.de/api/charts || exit 1

rm $SCRIPT_DIR/sae-*

exit 0