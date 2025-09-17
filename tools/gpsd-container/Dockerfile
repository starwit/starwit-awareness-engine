FROM debian:trixie-slim

ARG CACHE_BUST=1

RUN apt-get update && apt-get install -y gpsd gpsd-clients

ENTRYPOINT [ "/bin/bash", "/entrypoint.sh" ]