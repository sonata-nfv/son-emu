FROM python:3-onbuild

#periods in milliseconds
ENV SAMPLE_PERIOD 10
ENV TOTAL_PERIOD 2000

ADD requirements.txt .
ADD skewmon.py .

CMD [ "python", "./skewmon.py" ]