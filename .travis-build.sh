#!/bin/bash

set -eu

function travis_fold {
    local name="$1"; shift
    echo "travis_fold:start:$name"
    echo "\$ $*"
    "$@"
    echo "travis_fold:end:$name"
}

travis_fold build-deps-0 \
    apt-get -qq update

travis_fold build-deps-1 \
    apt-get -qqy install --no-install-recommends \
        build-essential devscripts equivs git

travis_fold build-deps-2 \
    mk-build-deps -i -t 'apt-get -qqy --no-install-recommends'

travis_fold changelog \
    fakeroot debian/rules clean

travis_fold buildpackage \
    dpkg-buildpackage -nc -b
