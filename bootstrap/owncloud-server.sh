#!/bin/bash 
apt-get update
apt-get upgrade -y
apt install mysql-client-core-8.0 -y
apt-get install apache2 -y
apt-get install php7.4 php7.4-cli libapache2-mod-php php7.4-mysql -y
curl https://attic.owncloud.org/download/repositories/10.5/Ubuntu_20.04/Release.key | apt-key add -
echo 'deb http://attic.owncloud.org/download/repositories/10.5/Ubuntu_20.04/ /' | tee /etc/apt/sources.list.d/owncloud.list
apt-get update
apt-get install php7.4-bz2 php7.4-curl php7.4-gd php7.4-imagick php7.4-intl php7.4-mbstring php7.4-xml php7.4-zip owncloud-files -y
sed -i "s/DirectoryIndex /DirectoryIndex index.php /" /etc/apache2/mods-enabled/dir.conf
sed -i "s|DocumentRoot /var/www/html|DocumentRoot /var/www/owncloud|" /etc/apache2/sites-enabled/000-default.conf
systemctl restart apache2
