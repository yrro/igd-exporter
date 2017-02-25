#!/bin/bash

set -eu

function travis_fold {
    local name="$1"; shift
    echo "travis_fold:start:$name"
    echo "\$ $*"
    "$@"
    echo "travis_fold:end:$name"
}

travis_fold docker-test-deps-0 \
    apt-get -qq update

travis_fold docker-test-deps-1 \
    apt-get -qqy install autopkgtest

travis_fold docker-test-autopkgtest \
    autopkgtest /workspace/*.changes -- null
