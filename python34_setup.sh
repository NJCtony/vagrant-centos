#!/usr/bin/env bash

echo "Updating yum..."
sudo yum -y update
sudo yum -y install yum-utils

echo "Installing CentOS Development Tools..."
sudo yum -y groupinstall development
sudo yum -y install tree

echo "Installing Python 3.4..."
sudo yum -y install epel-release
sudo yum -y install python34 python34-devel python34-setuptools

echo "Installing pip..."
sudo easy_install-3.4 pip

echo "Installing virtualenv"
sudo pip install virtualenv

echo "Creating virtual environment..."
cd /srv
virtualenv venv
sudo chmod -R 777 venv

echo "Installing required packages within virtual environment and making database migrations..."
cd /srv/website
make install
