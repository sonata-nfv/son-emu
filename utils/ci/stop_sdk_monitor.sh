#!/bin/bash

# stop the monitor
son-emu-cli monitor stop_metric -vnf vnf1:output --metric tx_packets

sleep 1

#stop the vnf
son-emu-cli compute-zapi stop -d datacenter1 -n vnf1


