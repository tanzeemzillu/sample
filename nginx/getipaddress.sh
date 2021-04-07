#!/bin/bash

set -e

declare -a interface_name=($(find /sys/class/net -type l -not -lname '*virtual*' -printf '%f\n'))

for i in "${interface_name[@]}"
do
  ifconfig $i | grep inet | awk 'NR==1 {print $2}' > ip_address.txt
done
