#!/bin/bash
echo "-- deploy test --"
echo "-- 1. system & python version"
uname -a
python --version
echo "-- 2. file list"
ls -R1 /root/
echo "-- Done."
