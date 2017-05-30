#!/usr/bin/env bash

echo "Updating yum..."
sudo yum -y update
sudo yum -y install yum-utils

echo "Installing CentOS Development Tools..."
sudo yum -y groupinstall development

echo "Installing Python 3.6..."
sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y install python36u

echo "Installing pip..."
sudo yum -y install python36u-pip
sudo yum -y install python36u-devel

echo "Creating Virtual Environment..."
cd /srv
sudo python3.6 -m venv venv
# sudo chmod -R 777 venv
sudo chown vagrant venv/
sudo chmod -R ug+rwx venv/
