#!/bin/bash

# Acknowledgement: Adapted from redis/utils/gen-test-certs.sh (at https://github.com/redis/redis)

# Generate some test certificates which are used by the regression test suite:
#
#   certs/ca.{crt,key}          Self signed CA certificate.
#   certs/client.{crt,key}      A certificate signed by the CA above.
#   certs/server.{crt,key}      A certificate signed by the CA above.

generate_cert() {
    local name=$1
    local cn="$2"
    local opts="$3"

    local keyfile=certs/${name}.key
    local certfile=certs/${name}.crt

    [ -f $keyfile ] || openssl genrsa -out $keyfile 2048
    openssl req \
        -new -sha256 \
        -subj "/O=Starwit Technologies GmbH/CN=$cn" \
        -key $keyfile | \
        openssl x509 \
            -req -sha256 \
            -CA certs/ca.crt \
            -CAkey certs/ca.key \
            -CAserial certs/ca.txt \
            -CAcreateserial \
            -days 365 \
            $opts \
            -out $certfile
}

mkdir -p certs
[ -f ca.key ] || openssl genrsa -out certs/ca.key 4096
openssl req \
    -x509 -new -nodes -sha256 \
    -key certs/ca.key \
    -days 3650 \
    -subj '/O=Starwit Technologies GmbH/CN=Redis CA' \
    -out certs/ca.crt

generate_cert server "server"
generate_cert client "client"
