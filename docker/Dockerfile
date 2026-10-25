# NON TESTÉ - à valider chez toi (docker compose build). TinyOS/TOSSIM exige Python 2.7 + nesC.
FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y build-essential git python2.7 python2.7-dev python-pip \
    python3 python3-dev \
    autoconf automake libtool bison flex gperf emacs-nox openjdk-8-jdk gcc-msp430 \
    ca-certificates wget && rm -rf /var/lib/apt/lists/*
# nesC compiler
RUN git clone --depth 1 https://github.com/tinyos/nesc.git /opt/nesc && \
    cd /opt/nesc && ./Bootstrap && ./configure && make && make install
# TinyOS
RUN git clone --depth 1 https://github.com/tinyos/tinyos-main.git /opt/tinyos-main
ENV TINYOS_ROOT_DIR=/opt/tinyos-main \
    TINYOS_MAKE_DIR=/opt/tinyos-main/support/make \
    TINYOS_OS_DIR=/opt/tinyos-main/tos \
    PYTHONPATH=/opt/tinyos-main/support/sdk/python:$PYTHONPATH
RUN cd /opt/tinyos-main/tools && ./Bootstrap && ./configure && make && make install
WORKDIR /work
CMD ["bash"]
