#!/bin/bash

localIP=`cat ip_address.txt`
echo $localIP
sed -e "s/{{ localIP }}/${localIP}/g" \
    < default-conf-template.conf \
    > default.conf
