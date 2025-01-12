#!/bin/bash

set -ex

rm -rf lemmon_capi.o lemmon_capi.so
gcc -c -Wall -fPIC $(pkg-config --cflags python3 x11 glx) lemmon_capi.c
gcc -shared $(pkg-config --libs x11 glx) -o lemmon_capi.so lemmon_capi.o

# find lemmon.py lemmon_capi.c build.sh | entr -cas "./build.sh && nixGL python3 lemmon.py"
