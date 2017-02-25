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
    apt-get -qq update

travis_fold docker-deps-1 \
    apt-get -qqy install --no-install-recommends \
        build-essential devscripts equivs

# Fails with an unhelpful message.
travis_fold docker-deps-2 \
    mk-build-deps -i -t 'apt-get -y -o Debug::pkgProblemResolver=yes --no-install-recommends'

#travis_fold docker-deps-2 \
#    apt-get -qqy install \
#        debhelper \
#        devscripts \
#        git \
#        python3 \
#        python3-prometheus-client \
#        python3-setuptools

travis_fold docker-changelog \
    fakeroot debian/rules clean

# XXX generate changelog in preclean hook?
travis_fold docker-buildpackage \
    dpkg-buildpackage -nc --build=full
