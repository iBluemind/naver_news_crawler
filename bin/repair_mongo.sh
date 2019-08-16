#!/bin/sh

docker run --rm -v /home/odroid/workspace/db:/data/db andresvidal/rpi3-mongodb3 mongod --repair
