#!/bin/bash
cmd=$*

while true; do
    echo $*
    $*
    if [ $? == 0 ]; then
        echo "Done."
        break;
    else
        echo "Operation returns $?, retrying..."
        sleep 1
    fi
done
