#!/bin/bash -x
apt-get update
apt-get upgrade -y
apt-get install mysql-server -y
systemctl start mysql.service
mysql --user=root <<_EOF_
  ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
  DELETE FROM mysql.user WHERE User='';
  DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
  DROP DATABASE IF EXISTS test;
  DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
  CREATE USER 'gluser'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
  GRANT ALL PRIVILEGES on *.* TO 'gluser'@'%' WITH GRANT OPTION;
  FLUSH PRIVILEGES;
_EOF_
mysql --user=gluser -ppassword <<__EOF__
    CREATE DATABASE owncloud_db;
__EOF__
sed -i "s|^bind-address.*= 127.0.0.1|bind-address = 0.0.0.0|" /etc/mysql/mysql.conf.d/mysqld.cnf
sed -i '/^\[mysqld\]/s/$/\ndefault_authentication_plugin= mysql_native_password/' /etc/mysql/mysql.conf.d/mysqld.cnf
/etc/init.d/mysql restart





