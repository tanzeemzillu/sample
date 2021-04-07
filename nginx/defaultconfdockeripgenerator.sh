#!/bin/bash

dockerIP=`ifconfig docker0 | grep inet | awk 'NR==1 {print $2}'`
echo $dockerIP
sed -e "s/{{ dockerIP }}/${dockerIP}/g" \
    < default-conf-template-dockerip.conf \
    > default.conf
