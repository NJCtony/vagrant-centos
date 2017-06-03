# Vagrant Centos
Vagrant box with Centos 7, with scripts to install Python 3.4, MySQL 5.6 and Django 1.11.
> This repo is meant for a school project, but it may also suit your purposes.

Prerequisites
-----
* [Vagrant](https://www.vagrantup.com/docs/installation/)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads)


Getting Started
-----
1. Clone this repository and `cd` into the directory.
2. Run `$ vagrant up`. This will take a few minutes.
3. When done, run `$ vagrant ssh` to access your newly-created Centos 7 VM.
4. Run `$ source /srv/venv/bin/activate & cd /srv/website` to activate the virtual environment and change directory to where the project files are located.
5. Run `$ python manage.py runserver 0.0.0.0:8000`.
6. Access the site on your host machine (not the VM) by going to `http://localhost:8000` on your browser.
7. Use user = `vagrant` and password = `password` to login to the superuser account.
