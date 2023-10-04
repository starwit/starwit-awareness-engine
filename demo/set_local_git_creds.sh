#!/bin/bash

if [ -z "$GITHUB_USER" ]; then
    read -p "GITHUB_USER: " GITHUB_USER
    export GITHUB_USER
fi

if [ -z "$GITHUB_TOKEN" ]; then
    read -s -p "GITHUB_TOKEN: " GITHUB_TOKEN
    export GITHUB_TOKEN
fi

echo -e "\n"

export GIT_CONFIG_COUNT=2
export GIT_CONFIG_KEY_0=credential.username
export GIT_CONFIG_VALUE_0=$GITHUB_USER
export GIT_CONFIG_KEY_1=credential.helper
export GIT_CONFIG_VALUE_1='!f() { test "$1" = get && echo "password=${GITHUB_TOKEN}"; }; f'

echo "Git is now configured to authenticate https requests as $GITHUB_USER in this shell session"