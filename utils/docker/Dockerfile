FROM cgeoffroy/dockernet

# ensure that we have the latest dockernet code base!
WORKDIR /dockernet
RUN git pull \
    && python setup.py install

WORKDIR /son-emu

COPY . /son-emu/

RUN cd /son-emu/ansible \
    && ansible-playbook install.yml \
    && cd /son-emu \
    && python setup.py install \
    && echo 'Done'

ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]
