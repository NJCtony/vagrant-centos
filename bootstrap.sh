#!/usr/bin/env bash

yum clean all
yum -y update
yum -y install httpd
if ! [ -L /var/www ]; then
  rm -rf /var/www
  ln -fs /vagrant /var/www
fi
