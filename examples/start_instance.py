import boto3, os, argparse
from contextlib import suppress
from botocore.exceptions import ClientError

DEFAULT_PROFILE_NAME    = "privateaccount"
DEFAULT_REGION          = "us-east-1"
DEFAULT_NAME            = "python test"
DEFAULT_AZ              = "us-east-1a"
DEFAULT_NAME            = "python test"

VPC_CIDR_BLOCK          = "10.0.0.0/16"
SUBNET_CIDR_BLOCK       = "10.0.1.0/24"
INSTANCE_AMI_ID         = "ami-0aa2b7722dc1b5612" # Ubuntu Server 20.04 LTS (HVM), SSD Volume
INSTANCE_TYPE           = "t2.micro"

parser = argparse.ArgumentParser(description='Sample Start Instance Script', 
                                 epilog='''Refer to the "AWS SDK for Python Quickstart Guide" for help setting up the Python SDK: 
                                        https://olympus.mygreatlearning.com/courses/89450/pages/installing-python-on-windows-and-macos?module_item_id=3675734 
                                        or https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html''', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--name', '-n', help=f"Name to use for the AWS resources created.", default=DEFAULT_NAME, required=False, type=str)
parser.add_argument('--profile', '-p', help=f"AWS Config profile to use.", default=DEFAULT_PROFILE_NAME, required=False, type=str)
parser.add_argument('--region', '-r', help=f"Region to use.", default=DEFAULT_REGION, required=False, type=str)
parser.add_argument('--availabilityzone', '-az', help=f"Availability zone used for the subnet.", default=DEFAULT_AZ, required=False, type=str)
parser.add_argument('--cleanup', '-c', help=f"Find and delete AWS resources created by this script.", action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

session                 = boto3.session.Session(profile_name=args.profile, region_name=args.region)
ec2_resource            = session.resource('ec2')
ec2_client              = session.client('ec2')
key_pair_name           = args.name.replace(' ', '-')
key_pair_filename       = key_pair_name + ".pem"

instance_bootstrap_script = '''#!/bin/bash -x
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
  FLUSH PRIVILEGES;
_EOF_
sed -i "s|^bind-address.*= 127.0.0.1|bind-address = 0.0.0.0|" /etc/mysql/mysql.conf.d/mysqld.cnf
sed -i '/^\[mysqld\]/s/$/\ndefault_authentication_plugin= mysql_native_password/' /etc/mysql/mysql.conf.d/mysqld.cnf
/etc/init.d/mysql restart
'''

def create_vpc():
    if args.cleanup: return None
    vpc = ec2_resource.create_vpc(
            CidrBlock         = VPC_CIDR_BLOCK,
            TagSpecifications =[{
                'ResourceType': 'vpc',
                'Tags': [ {'Key': 'Name', 'Value': f"{args.name} vpc"} ]
            }])
    vpc.modify_attribute(EnableDnsSupport = {'Value': True})
    vpc.modify_attribute(EnableDnsHostnames = {'Value': True})
    return vpc    

def create_subnet():
    if args.cleanup: return None
    subnet = vpc.create_subnet(
        TagSpecifications=[{
            'ResourceType': 'subnet',
            'Tags'        : [{'Key': 'Name', 'Value': f"{args.name} subnet"}]
        }], 
        AvailabilityZone    =args.availabilityzone,
        CidrBlock           =SUBNET_CIDR_BLOCK)
    ec2_client.modify_subnet_attribute(SubnetId = subnet.id, MapPublicIpOnLaunch = {"Value": True})
    return subnet
    
def create_security_group():
    if args.cleanup: return None
    sg = vpc.create_security_group(
        Description         = f"{args.name} security group", 
        GroupName           = f"{args.name} security group", 
        TagSpecifications   =[{
            'ResourceType': 'security-group',
            'Tags'        : [{'Key': 'Name', 'Value': f"{args.name} security group"}]
        }])
    sg.authorize_ingress(
        IpPermissions = [{
            'FromPort': 22, 
            'IpProtocol': 'tcp', 
            'IpRanges': [{
                'CidrIp': '0.0.0.0/0', 
                'Description': 'Accept SSH from anywhere'
            }], 
            'ToPort': 22
        }], 
        TagSpecifications = [{
            'ResourceType': 'security-group-rule',
            'Tags': [
                {'Key': 'Name', 'Value': f"opening port 22 for security group '{args.name} security group'"}
            ]
        }])
    return sg
    
def create_key_pair():
    if args.cleanup: return None
    keypair = ec2_resource.create_key_pair(KeyName=key_pair_name, KeyFormat='pem')
    with open(key_pair_filename, 'w') as file: file.write(keypair.key_material)
    os.chmod(key_pair_filename, 0o400)
    return keypair

def create_instance():
    if args.cleanup: return None
    instance_id = ec2_client.run_instances(
            ImageId             = INSTANCE_AMI_ID,
            InstanceType        = INSTANCE_TYPE, 
            KeyName             = key_pair_name,
            MaxCount            = 1,
            MinCount            = 1,
            UserData            = instance_bootstrap_script, 
            SecurityGroupIds    = [ sg.id ], 
            SubnetId            = subnet.id, 
            TagSpecifications   =[{
                'ResourceType': 'instance',
                'Tags'        : [
                    {'Key': 'Name', 'Value': f"{args.name} instance"}
                ]
            }]
        )['Instances'][0]['InstanceId']
    ec2_client.get_waiter("instance_status_ok").wait(InstanceIds=[instance_id])
    return ec2_resource.Instance(instance_id)
    
def create_internet_gateway():
    if args.cleanup: return None
    internet_gateway = ec2_resource.create_internet_gateway(
        TagSpecifications=[{
            'ResourceType': 'internet-gateway',
            'Tags'        : [{'Key': 'Name', 'Value': f"{args.name} internet gateway"}]
        }])
    ec2_client.get_waiter("internet_gateway_exists").wait(InternetGatewayIds=[internet_gateway.id])
    internet_gateway.attach_to_vpc(VpcId=vpc.id)
    return internet_gateway


vpcs = list(ec2_resource.vpcs.filter(Filters = [{'Name': 'tag:Name', 'Values': [ f"{args.name} vpc" ]}]))
vpc = vpcs[0] if len(vpcs) else create_vpc()

subnets = list(vpc.subnets.filter(Filters = [
                {'Name': 'tag:Name', 'Values': [ f"{args.name} subnet" ]}, 
                {'Name': 'vpc-id',   'Values': [ vpc.id ]}
            ])) if vpc else []
subnet = subnets[0] if len(subnets) else create_subnet()

sgs = list(vpc.security_groups.filter(Filters = [
        {'Name': 'group-name', 'Values': [ f"{args.name} security group" ]}, 
        {'Name': 'vpc-id',     'Values': [ vpc.id ]}
    ])) if vpc else []
sg = sgs[0] if len(sgs) else create_security_group()

keypairs = []
with suppress(ClientError): keypairs = list(ec2_resource.key_pairs.filter(KeyNames=[key_pair_name]))
keypair = keypairs[0] if len(keypairs) else create_key_pair()

internet_gateways = list(ec2_resource.internet_gateways.filter(Filters=[{'Name': 'tag:Name', 'Values': [ f"{args.name} internet gateway" ] }]))
internet_gateway = internet_gateways[0] if len(internet_gateways) else create_internet_gateway()

if vpc and internet_gateway:
    default_route_table = list(vpc.route_tables.filter(Filters = [{'Name': 'association.main', 'Values': ['true']}]))[0]
    default_route_table.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=internet_gateway.id)

instances = list(vpc.instances.filter(Filters = [{'Name': 'tag:Name',   'Values': [ f"{args.name} instance" ]}])) if vpc else []
instance = instances[0] if len(instances) else create_instance()

if args.cleanup: 
    with suppress(ClientError):
        if instance:
            instance.terminate()
            ec2_client.get_waiter("instance_terminated").wait(InstanceIds=[instance.id])
        if keypair: keypair.delete()
        if internet_gateway:
            internet_gateway.detach_from_vpc(VpcId=vpc.id)
            internet_gateway.delete()
        with suppress(FileNotFoundError): 
            os.chmod(key_pair_filename, 0o666)
            os.remove(key_pair_filename)
        if sg: sg.delete()
        if subnet: subnet.delete()
        if vpc: vpc.delete()
