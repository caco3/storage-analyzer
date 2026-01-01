ARG UBUNTU_VERSION=24.04

####################################
# Temporary image for building Duc #
####################################

FROM ubuntu:${UBUNTU_VERSION} AS build

ARG DUC_VERSION=1.4.6

RUN apt-get update -qq \
 && apt-get install -y -qq --no-install-recommends \
        build-essential \
        git \
        ca-certificates \
        checkinstall \
        curl \
        libcairo2-dev \
        libncursesw5-dev \
        libpango1.0-dev \
        libtokyocabinet-dev \
        pkg-config \
 && rm -rf /var/lib/apt/lists/*

ADD https://github.com/zevv/duc/releases/download/${DUC_VERSION}/duc-${DUC_VERSION}.tar.gz .

COPY patches/*.patch ./

RUN tar xzf duc-${DUC_VERSION}.tar.gz \
 && cd duc-${DUC_VERSION} \
 && git apply ../*.patch \
 && ./configure \
 && make -j"$(nproc)" \
 && checkinstall --install=no --default \
 && cp duc_${DUC_VERSION}-*.deb /duc.deb

###############################
# Final image for running Duc #
###############################

FROM ubuntu:${UBUNTU_VERSION}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG BUILD_DATE
ARG VCS_REF
LABEL maintainer="George Ruinelli <caco3@ruinelli.ch>" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/caco3/storage-analyzer.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0.0-rc1"

COPY --from=build /duc.deb /

RUN dpkg -i /duc.deb \
 && rm /duc.deb \
 && apt-get update -qq \
 && apt-get install -y -qq --no-install-recommends \
        cron \
        fcgiwrap \
        libcairo2 \
        libpango-1.0 \
        libpangocairo-1.0-0 \
        libtokyocabinet9 \
        nginx \
        zstd \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /var/www/html/* \
 && mkdir -p /snapshots /scan /config

COPY app/nginx.conf /etc/nginx/nginx.conf
COPY app/ducrc /etc/ducrc

COPY app/*.cgi /var/www/html/
COPY app/*.png /var/www/html/
COPY app/*.ico /var/www/html/
COPY app/*.htm /var/www/html/
COPY app/*.css /var/www/html/
COPY app/*.js /var/www/html/

COPY app/startup.sh /startup.sh
COPY app/scan.sh /scan.sh
COPY app/env.sh /env.sh
COPY app/manual_scan.sh /manual_scan.sh


RUN chmod +x /var/www/html/*.cgi \
 && chmod +x /startup.sh /scan.sh /manual_scan.sh

# Default schedule: every sunday at midnight
ENV SCHEDULE="0 0 * * 0"

EXPOSE 80

STOPSIGNAL SIGTERM

CMD ["/startup.sh"]
