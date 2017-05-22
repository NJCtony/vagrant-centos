#!/usr/bin/env bash

echo "Updating yum..."
sudo yum -y update

echo "Setting up MySQL repository..."
sudo yum -y install http://dev.mysql.com/get/mysql-community-release-el7-5.noarch.rpm

echo "Installing MySQL server packages..."
sudo yum -y install mysql-community-server mysql-community-devel

echo "Starting MySQL Service..."
sudo systemctl start mysqld
sudo systemctl enable mysqld.service

echo "Creating database for Django application"
sudo mysql -e "CREATE DATABASE djangodb"
sudo mysql -e "CREATE USER 'user'@'localhost' IDENTIFIED BY 'password'"
sudo mysql -e "GRANT ALL PRIVILEGES ON djangodb.* TO 'user'@'localhost'"
sudo mysql -e "FLUSH PRIVILEGES"

echo "Securing MySQL installation..."
sudo mysql -e "UPDATE mysql.user SET Password = PASSWORD('password') WHERE User = 'root'"
sudo mysql -e "DROP USER ''@'localhost'"
sudo mysql -e "DROP USER ''@'$(hostname)'"
sudo mysql -e "DROP DATABASE test"
sudo mysql -e "FLUSH PRIVILEGES"
