print("Loading...")
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
parser.add_argument('--run-mysql', help=f"Run MySQL", action=argparse.BooleanOptionalAction, default=False)
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
''' if args.run_mysql else ''

def create_vpc(name):
    if args.cleanup: return None
    print(f"Creating '{name}'...")
    vpc = ec2_resource.create_vpc(
            CidrBlock         = VPC_CIDR_BLOCK,
            TagSpecifications =[{
                'ResourceType': 'vpc',
                'Tags': [ {'Key': 'Name', 'Value': name} ]
            }])
    vpc.modify_attribute(EnableDnsSupport = {'Value': True})
    vpc.modify_attribute(EnableDnsHostnames = {'Value': True})
    print(f"'{name}' created: {vpc.id}")
    return vpc    

def create_subnet(name):
    if args.cleanup: return None
    print(f"Creating '{name}'...")
    subnet = vpc.create_subnet(
        TagSpecifications=[{
            'ResourceType': 'subnet',
            'Tags'        : [{'Key': 'Name', 'Value': name}]
        }], 
        AvailabilityZone    =args.availabilityzone,
        CidrBlock           =SUBNET_CIDR_BLOCK)
    ec2_client.modify_subnet_attribute(SubnetId = subnet.id, MapPublicIpOnLaunch = {"Value": True})
    print(f"'{name}' created: {subnet.id}")
    return subnet
    
def create_security_group(name):
    if args.cleanup: return None
    print(f"Creating '{name}'...")
    sg = vpc.create_security_group(
        Description         = name, 
        GroupName           = name, 
        TagSpecifications   =[{
            'ResourceType': 'security-group',
            'Tags'        : [{'Key': 'Name', 'Value': name}]
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
    print(f"'{name}' created: {sg.id}")
    return sg
    
def create_key_pair():
    if args.cleanup: return None
    print(f"Creating key pair '{key_pair_name}'...")
    keypair = ec2_resource.create_key_pair(KeyName=key_pair_name, KeyFormat='pem')
    if os.path.exists(key_pair_filename):
        os.chmod(key_pair_filename, 0o666)
        os.remove(key_pair_filename)
    with open(key_pair_filename, 'w') as file: file.write(keypair.key_material)
    os.chmod(key_pair_filename, 0o400)
    print(f"Key pair '{key_pair_name}' created and downloaded to '{key_pair_filename}': {keypair.key_pair_id}")
    return keypair

def create_instance(name):
    if args.cleanup: return None
    print(f"Starting '{name}'...")
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
                    {'Key': 'Name', 'Value': name}
                ]
            }]
        )['Instances'][0]['InstanceId']
    print(f"Waiting for '{name}'...: {instance_id}")    
    ec2_client.get_waiter("instance_status_ok").wait(InstanceIds=[instance_id])
    print(f"'{name}' started: {instance_id}")
    return ec2_resource.Instance(instance_id)
    
def create_internet_gateway(name):
    if args.cleanup: return None
    print(f"Creating '{name}'...")
    internet_gateway = ec2_resource.create_internet_gateway(
        TagSpecifications=[{
            'ResourceType': 'internet-gateway',
            'Tags'        : [{'Key': 'Name', 'Value': name}]
        }])
    print(f"Waiting for '{name}'...: {internet_gateway.id}")
    ec2_client.get_waiter("internet_gateway_exists").wait(InternetGatewayIds=[internet_gateway.id])
    internet_gateway.attach_to_vpc(VpcId=vpc.id)
    print(f"'{name}' created: {internet_gateway.id}")
    return internet_gateway


if __name__ == "__main__": 
    if not args.cleanup: print(f"Creating network '{args.name}'...")
    vpc_name = f"{args.name} vpc"
    vpcs = list(ec2_resource.vpcs.filter(Filters = [{'Name': 'tag:Name', 'Values': [ vpc_name ]}]))
    vpc = vpcs[0] if len(vpcs) else create_vpc(vpc_name)

    subnet_name = f"{args.name} subnet"
    subnets = list(vpc.subnets.filter(Filters = [
                    {'Name': 'tag:Name', 'Values': [ subnet_name ]}, 
                    {'Name': 'vpc-id',   'Values': [ vpc.id ]}
                ])) if vpc else []
    subnet = subnets[0] if len(subnets) else create_subnet(subnet_name)

    sg_name = f"{args.name} security group"
    sgs = list(vpc.security_groups.filter(Filters = [
            {'Name': 'group-name', 'Values': [ sg_name ]}, 
            {'Name': 'vpc-id',     'Values': [ vpc.id ]}
        ])) if vpc else []
    sg = sgs[0] if len(sgs) else create_security_group(sg_name)

    keypairs = []
    with suppress(ClientError): keypairs = list(ec2_resource.key_pairs.filter(KeyNames=[key_pair_name]))
    keypair = keypairs[0] if len(keypairs) else create_key_pair()

    internet_gateway_name = f"{args.name} internet gateway"
    internet_gateways = list(ec2_resource.internet_gateways.filter(Filters=[{'Name': 'tag:Name', 'Values': [ internet_gateway_name ] }]))
    internet_gateway = internet_gateways[0] if len(internet_gateways) else create_internet_gateway(internet_gateway_name)

    if vpc and internet_gateway:
        default_route_table = list(vpc.route_tables.filter(Filters = [{'Name': 'association.main', 'Values': ['true']}]))[0]
        default_route_table.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=internet_gateway.id)

    instance_name = f"{args.name} instance"
    instances = list(vpc.instances.filter(Filters = [{'Name': 'tag:Name',   'Values': [ instance_name ]}])) if vpc else []
    instance = instances[0] if len(instances) else create_instance(instance_name)
    if not args.cleanup: print(f"'{args.name}' network created")



    if args.cleanup: 
        print(f"Cleaning up network '{args.name}'...")
        if instance:
            print(f"Terminating '{instance_name}'...: {instance.id}")
            instance.terminate()
            print(f"Waiting for '{instance_name}' to terminate...: {instance.id}")
            ec2_client.get_waiter("instance_terminated").wait(InstanceIds=[instance.id])
            print(f"'{instance_name}' terminated: {instance.id}")
        if keypair: 
            key_pair_id = keypair.key_pair_id
            print(f"Deleting key pair '{key_pair_name}'...: {key_pair_id}")
            keypair.delete()
            print(f"'{key_pair_name}' deleted: {key_pair_id}")
        if os.path.exists(key_pair_filename): 
            print(f"Deleting file '{key_pair_filename}'...")
            os.chmod(key_pair_filename, 0o666)
            os.remove(key_pair_filename)
            print(f"File '{key_pair_filename}' deleted")
        if internet_gateway:
            print(f"Deleting '{internet_gateway_name}'...: {internet_gateway.id} ")
            internet_gateway.detach_from_vpc(VpcId=vpc.id)
            internet_gateway.delete()
            print(f"'{internet_gateway_name}' deleted: {internet_gateway.id} ")
        if sg: 
            print(f"Deleting '{sg_name}'...: {sg.id}")
            sg.delete()
            print(f"'{sg_name}' deleted: {sg.id}")
        if subnet: 
            print(f"Deleting '{subnet_name}'...: {subnet.id}")
            subnet.delete()
            print(f"'{subnet_name}' deleted: {subnet.id}")
        if vpc: 
            print(f"Deleting '{vpc_name}'...: {vpc.id}")
            vpc.delete()
            print(f"'{vpc_name}' deleted: {vpc.id}")
        print(f"'{args.name}' network cleaned up")