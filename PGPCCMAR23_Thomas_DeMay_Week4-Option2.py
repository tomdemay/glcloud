from common.config import Configuration
from projects.week4.option2.create_aws_resources import CreateAWSResources
from projects.week4.option2.delete_aws_resources import DeleteAWSResources

# This script creates a system for teams to securily collaborate using Mattermost
# 
# This script does the following on AWS
# Creates a new VPC:                Project 1 VPC with 10.0.0.0/16 Cidr block in us-east-1
# Creates Internet Gateway:         Project 1 Internet Gateway
# Creates an Elastic IP Address:    Project 1 Elastic IP
# Creates a keypair:                glkey
# Creates a public subnet:          Public Subnet with 10.0.1.0/24 cidr in us-east-1a
# Create a private subnet:          Private Subnet with 10.0.2.0/24 cidr in us-east-1a
# Creates two Route Tables:         Public Route Table and Private Route Table
# Creates a security group:         Project 1 Mattermost Security Group
# Creates another security group:   Project 1 MySQL Server Security Group
# Createa a NAT gateway:            Project 1 NAT Gateway on Public Subnet with Project 1 Elastic IP
# Creates an EC2 instance:          Project 1 MySQL Server on Private Subnet and Project 1 MySQL Server Security Group
#                                       using Ubuntu 20.04 on t2.micro with a bootstrap script to install and configure MySQL
# Creates another EC2 Instance:     Project 1 Mattermost Server on Public Subnet with Project 1 Mattermost Security Group
#                                       using Ubuntu 20.04 on t2.micro with a bootstrap script to install and configure
#                                       Mattermost server and point it to the private IP address of the MySQL Server instance
#
# authorizes ingress ports from anywhere for Project 1 Mattermost Security Group: 22, 443,80,8065
# authorizes ingress ports from public subnet only for Project 1 MySQL Server Security Group: 22, 80, 443, 3306
# 0.0.0.0/0 (anywhere) targeting Project 1 Internet Gateway route is added to Public Route Table 
#   and is associated with the Public Subnet
# 0.0.0.0/0 (anywhere) targeting Project 1 NAT Gateway route is added to Private Route Table
#   and is associated with the Private Subnet
#
# run script with --help to get information on what is configurable on the command line
# and refer to config.ini to see what defaults are configurable
# run script with --clean option to delete all of the above resources

if __name__ == '__main__': 
    Configuration.setup(
        project_name="matterMost", 
        project_description='PGPCC | Project. Creating a secure collaboration solution using mattermost and MySQL on AWS')
    DeleteAWSResources.run() if Configuration.args.cleanup else CreateAWSResources.run()

