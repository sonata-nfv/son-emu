#! /bin/bash -e
set -x

#cp /containernet/util/docker/entrypoint.sh /tmp/x.sh
#cat /tmp/x.sh | awk 'NR==1{print; print "set -x"} NR!=1' > /conteinernet/util/docker/entrypoint.sh

exec /containernet/util/docker/entrypoint.sh $*
