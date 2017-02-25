#!/bin/bash

set -eux

mkdir igd-exporter
sudo mount --bind . igd-exporter
# shellcheck disable=SC2064
trap "sudo umount '$PWD/igd-exporter'" EXIT

docker run --rm -v "$PWD:/workspace" -w /workspace/igd-exporter debian:stretch ./.travis-build.sh
docker run --rm -v "$PWD:/workspace" -w /workspace/igd-exporter debian:stretch ./.travis-test.sh
