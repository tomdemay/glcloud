#!/bin/bash -x
yum update  
yum upgrade -y
yum install wget
wget http://dev.mysql.com/get/mysql57-community-release-el7-9.noarch.rpm
yum localinstall mysql57-community-release-el7-9.noarch.rpm -y
yum install mysql-community-server -y --nogpgcheck
systemctl start mysqld.service
export TEMP_PASS=`grep 'temporary password' /var/log/mysqld.log | rev | cut -d" " -f1 | rev | tr -d "."`
mysql --user=root -p$TEMP_PASS --connect-expired-password<<_EOF_
  ALTER USER 'root'@'localhost' IDENTIFIED BY 'Password42!';
  DELETE FROM mysql.user WHERE User='';
  DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
  DROP DATABASE IF EXISTS test;
  DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
  FLUSH PRIVILEGES;
_EOF_
wget https://d6opu47qoi4ee.cloudfront.net/install_mysql_linux.sh
chmod 777 install_mysql_linux.sh
./install_mysql_linux.sh
