import logging, os
from botocore.exceptions import ClientError
from common.session import Session
from common.config import Configuration
from common.key_pair import KeyPair
from common.aws_resource_interface import AWSResourceInterface
from common.subnet import Subnet
from common.route_table import RouteTable
from common.security_group import SecurityGroup
from common.instance import Instance

class Vpc(AWSResourceInterface):
    def __init__(self, vpc: object):
        self.vpc = vpc

    @property
    def id(self: object) -> str:
        return self.vpc.id
    
    @property
    def enableDnsSupport(self: object) -> bool:
        return self.vpc.describe_attribute(Attribute = 'enableDnsSupport')["EnableDnsSupport"]["Value"]
    
    @enableDnsSupport.setter
    def enableDnsSupport(self: object, value: bool):
        if self.enableDnsSupport != value:
            self.vpc.modify_attribute(EnableDnsSupport = {'Value': value})
            # refresh self
            vpcs = list(Session.ec2_resource.vpcs.filter(VpcIds = [self.vpc.id]))[0]

    @property
    def enableDnsHostnames(self: object) -> bool:
        return self.vpc.describe_attribute(Attribute = 'enableDnsHostnames')["EnableDnsHostnames"]["Value"]
    
    @enableDnsHostnames.setter
    def enableDnsHostnames(self: object, value: bool):
        if self.enableDnsHostnames != value:
            self.vpc.modify_attribute(EnableDnsHostnames = {'Value': value})
            # refresh self
            vpcs = list(Session.ec2_resource.vpcs.filter(VpcIds = [self.vpc.id]))[0]

    def wait_until_exists(self: object):
        self.vpc.wait_until_exists()

    def wait_until_available(self: object):
        self.vpc.wait_until_available()

    def getSubnet(self: object, name: str, cidr_block: str, availability_zone: str = None) -> Subnet:
        subnet = self.findSubnet(name=name)
        if subnet: return subnet

        logging.debug(f"Creating subnet '{name}'...")
        ec2_subnet = self.vpc.create_subnet(
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags'        : [
                    {'Key': 'Name', 'Value': name}
                ]
            }], 
            AvailabilityZone=availability_zone if availability_zone else Configuration.region_name + "a",
            CidrBlock=cidr_block
        )
        logging.info(f"Created subnet '{name}': {ec2_subnet}")
        return Subnet(subnet=ec2_subnet) if ec2_subnet else None
    
    def getRouteTable(self: object, name: str = None) -> RouteTable:
        rtb = self.findRouteTable(name)
        if rtb: return rtb

        logging.debug(f"Creating route table '{name}'...")
        ec2_rtb = Session.ec2_resource.create_route_table(
            VpcId=self.vpc.id, 
            TagSpecifications=[{
                'ResourceType': 'route-table',
                'Tags'        : [
                    {'Key': 'Name', 'Value': name}
                ]
            }]
        )
        logging.info(f"Created route table '{name}': {ec2_rtb}")
        return RouteTable(rtb=ec2_rtb) if ec2_rtb else None
        
    def getSecurityGroup(self: object, name: str, description: str = None) -> SecurityGroup:
        sg = self.findSecurityGroup(name)
        if sg: return sg

        logging.debug(f"Creating security group '{name}'...")
        ec2_sg = Session.ec2_resource.create_security_group(
            Description = description if description else name, 
            GroupName   = name, 
            VpcId       = self.vpc.id, 
            TagSpecifications =[{
                'ResourceType': 'security-group',
                'Tags'        : [
                    {'Key': 'Name', 'Value': name}
                ]
            }]
        )
        logging.info(f"Created security group '{name}': {ec2_sg}")
        return SecurityGroup(sg=ec2_sg) if ec2_sg else None

    @property 
    def subnets(self: object) -> list[Subnet] :
        subnets = []
        try:
            ec2_subnets = list(self.vpc.subnets.all())
            if (len(ec2_subnets) == 0): raise IndexError(f"Unable to find subnets for '{self.vpc.id}'")
            subnet_ids = [ec2_subnet.id for ec2_subnet in ec2_subnets]
            subnets = [Subnet(ec2_subnet) for ec2_subnet in ec2_subnets]
            logging.info(f"Found subnets '{', '.join(subnets)} for '{self.vpc.id}'")
        except (IndexError, ClientError):
            logging.info(f"Subnets for '{self.vpc.id}' not found")
        return subnets

    def findSubnet(self: object, name: str) -> Subnet :
        subnet = None
        try:
            subnets = list(self.vpc.subnets.filter(
                Filters = [
                    {'Name': 'tag:Name', 'Values': [ name ]}, 
                    {'Name': 'vpc-id',   'Values': [ self.vpc.id ]}
                ]
            ))
            if (len(subnets) == 0): raise IndexError(f"Unable to find subnet '{name}'")
            # intentionally not caught
            if (len(subnets) != 1): raise RuntimeError(f'Unexpected results. Expected 1 subnet, but got {len(subnets)}')
            subnet = subnets[0]
            logging.info(f"Found subnet '{name}': {subnet}")
        except (IndexError, ClientError):
            logging.info(f"Subnet '{name}' not found")
        return Subnet(subnet=subnet) if subnet else None
    
    def findRouteTable(self: object, name: str = None) -> RouteTable:
        rtb = None
        if name == None:
            rtbs = list(Session.ec2_resource.route_tables.filter(
                Filters = [
                    {'Name': 'association.main', 'Values': ['true']}, 
                    {'Name': 'vpc-id',   'Values': [ self.vpc.id ]}
                ]
            ))
            if len(rtbs) != 1:  raise RuntimeError(f"Unexpected results. Expected 1 default route table, but got {len(rtbs)}")
            rtb = rtbs[0]
            logging.info(f"Found default route table: {rtb}")
            return RouteTable(rtb=rtb)

        try:
            rtbs = list(Session.ec2_resource.route_tables.filter(
                Filters = [
                    {'Name': 'tag:Name', 'Values': [ name ]}, 
                    {'Name': 'vpc-id',   'Values': [ self.vpc.id ]}
                ]
            ))
            if (len(rtbs) == 0): raise IndexError(f"Unable to find route table '{name}'")
            # intentionally not caught
            if (len(rtbs) != 1): raise RuntimeError(f"Unexpected results. Expected 1 route table, but got {len(rtbs)}")
            rtb = rtbs[0]
            logging.info(f"Found route table '{name}': {rtb}")
        except (IndexError,ClientError):
            logging.debug(f"Route table '{name}' not found")
        return RouteTable(rtb=rtb) if rtb else None

    def findSecurityGroup(self: object, name: str) -> SecurityGroup:
        sg = None
        try:
            sgs = list(Session.ec2_resource.security_groups.filter( 
                Filters = [
                    {'Name': 'tag:Name',   'Values': [ name ]   }, 
                    {'Name': 'group-name', 'Values': [ name ]   }, 
                    {'Name': 'vpc-id',     'Values': [ self.vpc.id ] }
                ]
            ))
            if (len(sgs) == 0): raise IndexError(f"Unable to find security group '{name}'")
            # intentionally not caught
            elif (len(sgs) != 1): raise RuntimeError(f'Unexpected results. Expected 1 security group, but got {len(sgs)}')
            sg = sgs[0]
            logging.info(f"Found security group '{name}': {sg}")
        except (IndexError, ClientError):
            logging.info(f"Security group '{name}' not found")
        return SecurityGroup(sg=sg) if sg else None

    def findInstance(self: object, name: str) -> Instance:
        instance = None
        try:
            instances = list(Session.ec2_resource.instances.filter(
                Filters = [
                    {'Name': 'tag:Name',   'Values': [ name ]   }, 
                    {'Name': 'vpc-id',     'Values': [ self.vpc.id ] }
                ]
            ))
            if (len(instances) == 0): raise IndexError(f"Unable to find ec2 instance '{name}'")
            # intentionally not caught
            if (len(instances) != 1): raise RuntimeError(f'Unexpected results. Expected 1 ec2 instance, but got {len(instances)}')
            instance = instances[0]
            logging.info(f"Found ec2 instance '{name}': {instance}")
        except (IndexError, ClientError):
            logging.info(f"EC2 instance '{name}' not found")
        return Instance(instance) if instance else None
    
    def runInstance(
            self:                       object, 
            name:                       str, 
            keypair:                    KeyPair, 
            subnet:                     Subnet, 
            sg:                         SecurityGroup, 
            ami_id:                     str = None, 
            root_volume_device_name:    str = None,
            instance_type:              str = None,
            ebs_volume_size:            int = None,
            bootstrap_file:             str = None, 
            bootstrap_str:              str = None) -> Instance:
        instance = self.findInstance(name)
        if instance: return instance
        logging.info(f"Creating ec2 instance '{name}' (this might take a few minutes)...")
        
        if bootstrap_file != None and bootstrap_str != None:
            raise ValueError("bootstrap_file and bootstrap_str arguments were both provided. Only one should be provided")
        
        userdata = ''
        if bootstrap_file: 
            with open(bootstrap_file) as f: userdata = f.read()
        elif bootstrap_str:
            userdata = bootstrap_str

        ec2_instances = Session.ec2_client.run_instances(
            ImageId             = ami_id if ami_id else Configuration.default_ami_id,
            InstanceType        = instance_type if instance_type else Configuration.default_instance_type, 
            KeyName             = keypair.name,
            MaxCount            = 1,
            MinCount            = 1,
            UserData            = userdata, 
            SecurityGroupIds    = [ sg.id ], 
            SubnetId            = subnet.id, 
            BlockDeviceMappings = [{
                'DeviceName':               root_volume_device_name if root_volume_device_name else Configuration.default_root_volume_device_name, 
                'Ebs': {
                    "DeleteOnTermination":  True,
                    'VolumeSize':           ebs_volume_size if ebs_volume_size else Configuration.default_ebs_volume_size,
                    'VolumeType':           'gp3'
                }
            }], 
            TagSpecifications   =[{
                'ResourceType': 'instance',
                'Tags'        : [
                    {'Key': 'Name', 'Value': name}
                ]
            }]
        )['Instances']

        if len(ec2_instances) != 1: raise RuntimeError(f'Unexpected results. Expected to create 1 ec2 instance, but got {len(ec2_instances)}')
        ec2_instance = Session.ec2_resource.Instance(ec2_instances[0]['InstanceId'])
        logging.info(f"Created ec2 instance '{name}': {ec2_instance}")
        return Instance(instance=ec2_instance) if ec2_instance else None

    def drop(self: object) -> None:
        logging.debug(f"Deleting VPC '{self.vpc}'...")
        self.vpc.delete()
        logging.info(f"Deleted VPC '{self.vpc}'")



class Vpcs:
    def getVpc(name: str, cidr_block: str) -> Vpc:
        vpc = Vpcs.findVpc(name)
        if vpc: return vpc

        logging.debug(f"Creating VPC '{name}'...")
        ec2_vpc = Session.ec2_resource.create_vpc(
            CidrBlock         =cidr_block,
            TagSpecifications =[{
                'ResourceType': 'vpc',
                'Tags': [
                    {'Key': 'Name', 'Value': name}
                ]
            }]
        )
        logging.info(f"Created VPC '{name}': {ec2_vpc}")
        return Vpc(vpc=ec2_vpc) if ec2_vpc else None

    def findVpc(name: str = None) -> Vpc:
        vpc = None
        try:
            filters = [{'Name': 'tag:Name', 'Values': [ name ]}] \
                if name \
                else [{'Name': 'is-default', 'Values': [ 'true' ]}]
            vpcs = list(Session.ec2_resource.vpcs.filter(Filters=filters))
            if (len(vpcs) == 0): raise IndexError(f"Unable to find vpc '{name if name else 'default vpc'}'")
            # intentionally not caught
            elif (len(vpcs) != 1): raise RuntimeError(f'Unexpected results. Expected 1 vpc, but got {len(vpcs)}')
            vpc = vpcs[0]
            logging.info(f"Found VPC '{name if name else 'default vpc'}': {vpc}")
        except (IndexError, ClientError):
            logging.info(f"VPC '{name if name else 'default vpc'}' not found")
        return Vpc(vpc=vpc) if vpc else None