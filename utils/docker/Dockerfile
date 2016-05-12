FROM mpeuster/containernet
MAINTAINER manuel@peuster.de

ENV SON_EMU_IN_DOCKER 1

WORKDIR /son-emu
COPY . /son-emu/

RUN cd /son-emu/ansible \
    && ansible-playbook install.yml \
    && cd /son-emu \
    # we need to reset the __pycache__ for correct test discovery
    && rm -rf src/emuvim/test/__pycache__ \
    && rm -rf src/emuvim/test/unittests/__pycache__ \
    && rm -rf src/emuvim/test/integrationtests/__pycache__ \
    && python setup.py install \
    && echo 'Done'

ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]

# dummy GK, zerorpc
EXPOSE 5000 4242
