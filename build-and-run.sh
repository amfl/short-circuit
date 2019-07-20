#!/bin/sh
# The image only needs to be rebuilt if the dependencies change.
# The source code is not baked in, it is volume-mounted at runtime.

docker build . -t short-circuit:latest && ./run.sh
