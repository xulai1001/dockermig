#!/bin/bash
service ssh start
echo "----------------"
echo "ISLAB ubuntu container"
uname -a
echo "run with -it to get an interactive shell."
echo "press Ctrl-P Q to detach"
echo "----------------"
cd ..
tail -f /dev/null

