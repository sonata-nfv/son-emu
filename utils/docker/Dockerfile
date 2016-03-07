FROM cgeoffroy/dockernet

WORKDIR /son-emu

COPY . /son-emu/

RUN cd /son-emu/ansible \
    && ansible-playbook install.yml \
    && cd /son-emu \
    && python setup.py install \
    && echo 'Done'

ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]
