#!/usr/bin/env bash

# build
cd firewall; docker build -t mpeuster/firewall-vnf .
cd ..
cd iperf; docker build -t mpeuster/iperf-vnf .
cd ..
cd tcpdump; docker build -t mpeuster/tcpdump-vnf .
cd ..

# push
docker push mpeuster/firewall-vnf
docker push mpeuster/iperf-vnf
docker push mpeuster/tcpdump-vnf