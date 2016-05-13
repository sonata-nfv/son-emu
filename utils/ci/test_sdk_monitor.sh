#!/bin/bash
# test if a vnf can be monitored and deployed

cpu_load=$(son-emu-cli monitor prometheus -d datacenter1 -vnf vnf1 -q 'sum(rate(container_cpu_usage_seconds_total{id="/docker/<uuid>"}[10s]))')

# test if prometheus query worked
regex="[0-9.]+, [0-9.']+"
if [[ $cpu_load =~ $regex ]] ; then
	echo "OK"
	exit 0
else
	echo $cpu_load
	echo "not OK"
	exit 1
fi
