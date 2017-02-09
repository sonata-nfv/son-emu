#! /bin/bash -e
set -x

#cp /containernet/util/docker/entrypoint.sh /tmp/x.sh
#cat /tmp/x.sh | awk 'NR==1{print; print "set -x"} NR!=1' > /conteinernet/util/docker/entrypoint.sh

# this cannot be done from the Dockerfile since we have the socket not mounted during build
# this image is needed for the monitoring in son-emu
#echo 'Pulling the "google/cadvisor" image ... please wait'
#docker pull 'google/cadvisor'

exec /containernet/util/docker/entrypoint.sh $*