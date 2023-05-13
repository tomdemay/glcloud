#!/bin/bash -x
apt-get update
apt-get upgrade -y
apt-get install apache2 -y
systemctl restart apache2
