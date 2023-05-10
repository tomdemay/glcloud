from common.config import Configuration
from projects.week4.option3.create_aws_resources import CreateAWSResources
from projects.week4.option3.delete_aws_resources import DeleteAWSResources

# This script creates a file share and sync solution (much like Dropbox) in AWS
#
# This script does the following on AWS
# Creates a new VPC:                owncloud-vpc with 10.0.0.0/16 Cidr block in us-east-1
# Creates Internet Gateway:         owncloud-igw
# Creates an Elastic IP Address:    owncloud-eipalloc
# Creates a keypair:                glkey
# Creates a public subnet:          public-owncloud-subnet with 10.0.1.0/24 cidr in us-east-1a
# Create a private subnet:          private-mysql-subnet with 10.0.2.0/24 cidr in us-east-1b
# Creates two Route Tables:         public-owncloud-rtb and private-mysql-rtb
# Creates a security group:         public-owncloud-sg
# Creates another security group:   private-mysql-sg
# Createa a NAT gateway:            owncloud-nat on public-owncloud-subnet with owncloud-eipalloc
# Creates an EC2 instance:          mysql-server on private-mysql-subnet and private-mysql-sg
#                                       using Ubuntu 20.04 on t2.micro with a bootstrap script to install and configure MySQL
# Creates another EC2 Instance:     owncloud-server on public-owncloud-subnet with public-owncloud-sg
#                                       using Ubuntu 20.04 on t2.micro with a bootstrap script to install and configure Owncloud
#
# authorizes ingress ports from anywhere for public-owncloud-sg: 22, 80, 443
# authorizes ingress ports from public-owncloud-subnet only for private-mysql-sg: 22, 3306
# 0.0.0.0/0 (anywhere) targeting owncloud-igw route is added to public-owncloud-rtb
#   and is associated with public-owncloud-subnet
# 0.0.0.0/0 (anywhere) targeting owncloud-nat route is added to private-mysql-rtb
#   and is associated with the private-mysql-subnet
#
# run script with --help to get information on what is configurable on the command line
# and refer to config.ini to see what defaults are configurable
# run script with --clean option to delete all of the above resources


if __name__ == '__main__': 
    Configuration.setup(description='PGPCC | Project. Creating a file share & sync solution using ownCloud and AWS')
    DeleteAWSResources.run() if Configuration.args.cleanup else CreateAWSResources.run()

