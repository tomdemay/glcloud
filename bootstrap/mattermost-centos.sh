#!/bin/bash -x
wget https://d6opu47qoi4ee.cloudfront.net/install_mattermost_linux.sh
yum install dos2unix -y
dos2unix install_mattermost_linux.sh
chmod 700 install_mattermost_linux.sh
./install_mattermost_linux.sh {0}
chown -R mattermost:mattermost /opt/mattermost
chmod -R g+w /opt/mattermost
cd /opt/mattermost
sudo -u mattermost ./bin/mattermost
