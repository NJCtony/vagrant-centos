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
4. Change directory to project files using `$ cd /srv` within the VM.
5. Run `$ source venv/bin/activate` to activate the virtual environment.
6. Go into the directory containing Django's `manage.py` file using `$ cd /srv/website`.
7. Run `$ python manage.py runserver 0.0.0.0:8000`.
8. Access the site on your host machine (not the VM) by going to `http://localhost:8000` on your browser.
