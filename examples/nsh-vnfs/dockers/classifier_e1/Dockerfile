FROM sfc-base

ADD vnfs/classifier.py classifier.py
ADD vnfs/dockers/classifier_e1/classifier_e1.py classifier_e1.py
ADD vnfs/dockers/classifier_e1/start.sh start.sh
RUN chmod +x start.sh

ENV SON_EMU_CMD ./start.sh
CMD /bin/bash
