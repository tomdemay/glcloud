# PGPCCMAR23 Cloud Computing on AWS
### by Tom DeMay

## Contents

---

## PGPCCMAR23_Thomas_DeMay_Week4-Option3.py
This script sets up all the required AWS resources to satisfy project "*Creating a file share & sync solution using ownCloud and AWS*"

The scripts creates (if not already created) the following resources:

1. VPC: owncloud-vpc. CIDR Block is defaulted to `10.0.0.0/16`: This is configurable in `config.ini`
2. Internet Gateway: owncloud-igw
3. Elastic IP Address: owncloud-eipalloc
4. Key Pair: The default keypair name is `glkey` (pem file is downloaded to `pemfiles` subdirectory): This is configurable in `config.ini`

Next the following resources are created (if not already created)

1. Public Subnet: public-owncloud-subnet. 
    - The default CIDR block is `10.0.1.0/24`: This default is configurable in `config.ini` and can be changed on the command line.
    - The default availability zone is  `us-east-1a`: This default is configurable in `config.ini` and can be changed on the command line.
2. Private Subnet: private-mysql-subnet. 
    - The default CIDR block is `10.0.2.0/24`: This default is configurable in `config.ini` and can be changed on the command line.
    - The default availability zone is  `us-east-1a`: This default is configurable in `config.ini` and can be changed on the command line.
3. Security Group for the web application: public-owncloud-sg
4. Security Group for MySQL: private-mysql-sg
5. Route Tables: public-owncloud-rtb and private-mysql-rtb

The internet gateway (owncloud-igw) is then attached to the VPC (owncloud-vpc). This is required before the NAT Gateway can be created.

Created: 

NAT Gateway: (owncloud-nat) is created using the Elastic IP (owncloud-eipalloc) and Public Subnet (public-owncloud-subnet). The script waits until the NAT is available. 

The following instances are created after the NAT Gateway is available:

1. EC2 Instance: mysql-server. The following are associated with this instance.
    - `bootstrap/mysql-server.sh` script is used to bootstrap the EC2 instance to install, configure and secure MySQL. 
    - The keypair `glkey`
    - Private Subnet (private-mysql-subnet)
    - Private Security Group (private-mysql-sq)
    - AMI ID `ami-007855ac798b5175e`: This is configurable in `config.ini`
    - Instance Type `t2.micro`: This is configurable in `config.ini`
2. EC2 Instance: owncloud-server. The following are associated with this instance.
    - `bootstrap/owncloud-server.sh` script is used to bootstrap the EC2 instance to install and configure appache, PHP 7.1, and owncloud.
    - The keypair `glkey`
    - Public Subnet (public-owncloud-subnet)
    - Public Security Group (public-owncloud-sg)
    - AMI ID `ami-007855ac798b5175e`: This is configurable in `config.ini`
    - Instance Type `t2.micro`: This is configurable in `config.ini`

After all the resources are created, they are then wired up:
1. A route is added in the public route table (public-owncloud-rtb) for the  Internet Gateway (owncloud-igw) to allow traffic to anywhere
2. The route table (public-owncloud-rtb) is associated with the Public Subnet (public-owncloud-subnet)
3. Ports are added to the public security group (public-owncloud-sg) to allow all HTTP and SSH traffic from anywhere into the EC2 Instance running the ownCloud web application (owncloud-server)
4. Ports are added to the private security group (private-mysql-sq) to allow all SSH and MySQL traffic from the public subnet (public-owncloud-subnet) only
5. A route is added to the private route table (private-mysql-rtb) for the VPC (owncloud-vpc) for the NAT Gateway (owncloud-nat) to allow traffic to anywhere
6. The route table (private-mysql-rtb) is associated with the Private Subnet (private-mysql-subnet)

The script then waits for status `ok` for the MySQL EC2 Instance (mysql-server) and the ownCloud HTTP Server (owncloud-server)

The following can be configured in the config.ini file:
- AWS default profile name: This default can be overriden through command line arguments
- AWS default region name: This default can be overriden through command line arguments 
- AMI ID to use for the EC2 instances
- Instance Type for the EC2 instances
- KeyPair name
- CIDR block for the VPC
- Availability Zone and CIDR block for the public subnet
- Availability Zone and CIDR block for the private subnet

Logging can be configured in logging.json. The default loggers are:
- All `ERROR` log messages are directed to `stderr`
- All `INFO` log messages are directed to `stdin`
- All `DEBUG` log messages are directed to `./output.log`

This script accepts the following arguments: 


```
> python .\PGPCCMAR23_Thomas_DeMay_Week4-Option3.py --help
usage: PGPCCMAR23_Thomas_DeMay_Week4-Option3.py [-h] [--profile PROFILE] [--region REGION] [--public-zone PUBLIC_ZONE] [--private-zone PRIVATE_ZONE] [--cleanup | --no-cleanup | -c]

PGPCC | Project. Creating a file share & sync solution using ownCloud and AWS

options:
  -h, --help            show this help message and exit
  --profile PROFILE, -p PROFILE
                        AWS Config profile to use. Default is 'privateaccount'
  --region REGION, -r REGION
                        Region to use. Default is 'us-east-1'
  --public-zone PUBLIC_ZONE
                        Availability zone used for the public subnet. Default is 'us-east-1a'
  --private-zone PRIVATE_ZONE
                        Availability zone used for the private subnet. Default is 'us-east-1a'
  --cleanup, --no-cleanup, -c
                        Find and delete AWS resources created by this script (default is --no-cleanup).

NOTE: these arguments default values are specified in 'config.ini'
```

---

### bootstrap subdirectory

- `bootstrap/mysql-server.sh` script is used to bootstrap the EC2 instance to install, configure and secure MySQL. 
    - root user is limited access only from the localhost
    - anonymous users are deleted
    - test database is dropped
    - `gluser` user is created with `password` password and permitted access from anywhere. In production this can be improved to allow traffic only from the owncloud http server.
    - `gluser` is granted all privileges.
    - database `owncloud` is created for `gluser`
    - MySQL is configured to allow traffic from anywhere. In production this can be improved to allow traffic only from the owncloud http server.
    - mysql_native_password is defined as the default_authentication_plugin
- `bootstrap/owncloud-server.sh` script is used to bootstrap the EC2 instance to install and configure appache, PHP 7.1, and owncloud. 
    - Apache is installed
    - MySQL Client is installed to test connectivity to the MySQL server
    - PHP7.1 is installed
    - ownCloud is downloaded and installed
    - index.php is defined as a apache default home page
    - `/var/www/owncloud` as apache's document root

When starting the web application for the first time, the user must create an admin user name and password and specify the database connections. In production this can be improved to be scripted in bootstrap script.


---

## PGPCCMAR23_Thomas_DeMay_Week4-Option2.py
This script sets up all the required AWS resources to satisfy option 2. Setting up a mattermost server. 

This creates VPC, igw, elastic ip, keypair, public and private subnets, public and private routing tables, security groups, nat gateway and a configured MySQL Server on the private subnet with a Mattermost server on public subnet pointing to the MySQL host.

Using Amazon AMI's

Refer to the following URLs for how to install python and the AWS Python SDK (it's referred to as boto3). On Amazon
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

Information on how to use the SDK could be found here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html.  Or just google boto3. There's a lot of good examples out there. It's real easy to use. 

For this python script just run 
python ./start_instance.py --help
for more information. You can edit any of the hard coded values at the top of the program. There's no output or logging or anything. I wanted to keep it as short as possible to hopefully make it easy to read/understand.

--- 

## examples/start_instance.py

Example barebones script to create a VPC with a MySQL Server on it to share with someone trying to learn AWS Python SDK

--- 

### project subdirectory

Scripts and artifacts for specific projects.

---

### pemfiles subdirectory

PEM files are downloaded to this subdirectory when keypairs are created

