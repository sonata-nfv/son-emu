FROM cgeoffroy/dockernet

ENV SON_EMU_IN_DOCKER 1

# ensure that we have the latest dockernet code base!
WORKDIR /
RUN rm -rf dockernet
RUN git clone -b dockernet-sonata https://github.com/mpeuster/dockernet.git
WORKDIR /dockernet
RUN python setup.py develop

WORKDIR /son-emu
COPY . /son-emu/

# ensure that we have the right docker image for tests available
RUN docker run --rm ubuntu:trusty

RUN cd /son-emu/ansible \
    && ansible-playbook install.yml \
    && cd /son-emu \
    && python setup.py install \
    && echo 'Done'

ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]
