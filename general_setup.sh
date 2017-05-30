#!/usr/bin/env bash

echo "Updating yum..."
sudo yum -y update
sudo yum -y install yum-utils

echo "Installing CentOS Development Tools..."
sudo yum -y groupinstall development
sudo yum -y install tree

echo "Installing inotify-tools..."
sudo yum -y install epel-release
sudo yum -y install inotify-tools
