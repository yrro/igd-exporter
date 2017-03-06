#!/bin/bash

set -eu

function travis_fold {
    local name="$1"; shift
    echo "travis_fold:start:$name"
    echo "\$ $*"
    "$@"
    echo "travis_fold:end:$name"
}

travis_fold docker-deps-0 \
    apt -q update

travis_fold docker-deps-1 \
    apt -qqy install --no-install-recommends \
        build-essential devscripts equivs git

travis_fold docker-deps-2 \
    mk-build-deps -i -t 'apt-get -qqy --no-install-recommends'

travis_fold docker-changelog \
    fakeroot debian/rules clean

travis_fold docker-buildpackage \
    dpkg-buildpackage -nc -b
