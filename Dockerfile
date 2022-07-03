FROM python:3

WORKDIR /app
COPY  . .
# RUN python3 -m pip install git+https://github.com/yrro/igd-exporter.git
RUN python3 -m pip install .

CMD [ "igd-exporter" ]
