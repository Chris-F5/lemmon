#!/bin/bash

set -ex

rm -rf mytest.o mytest.so
gcc -c -Wall -fPIC $(pkg-config --cflags python3) mytest.c
gcc -shared -o mytest.so mytest.o
