#!/bin/bash
rm /root/.xonotic/lock
ls -l /root/.xonotic
chmod 777 /root/.xonotic
echo "----------------"
echo "starting Xonotic server..."
echo "----------------"
/opt/xonotic/xonotic-linux64-dedicated
