import logging, random
from botocore.exceptions import ClientError
from common.session import Session
from common.config import Configuration
from common.ec2.key_pair import KeyPair
from common.aws_resource_interface import AWSResourceInterface
from common.ec2.subnet import Subnet
from common.ec2.route_table import RouteTable
from common.ec2.security_group import SecurityGroup
from common.ec2.instance import Instance
from common.elbv2.target_group import TargetGroup, TargetGroupTargetType, TargetGroupProtocol
from common.elbv2.elastic_load_balancer import ElasticLoadBalancer, ElasticLoadBalancerType

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

    def findSubnet(self: object, name: str = None) -> Subnet :
        subnet = None
        try:
            subnets = list(self.vpc.subnets.filter(
                Filters = [
                    {'Name': 'vpc-id',   'Values': [ self.vpc.id ]}, 
                    {'Name': 'default-for-az', 'Values': [ 'true' ]} \
                    if name == None else \
                    {'Name': 'tag:Name', 'Values': [ name ]}
                ]
            ))
            if (len(subnets) == 0): raise IndexError(f"Unable to find subnet '{name}'")
            # intentionally not caught
            if (len(subnets) != 1 and name != None): raise RuntimeError(f'Unexpected results. Expected 1 subnet, but got {len(subnets)}')
            subnet = random.choice(subnets)
            logging.info(f"Found subnet '{name}': {subnet}")
        except (IndexError, ClientError):
            logging.info(f"Subnet '{name}' not found")
        return Subnet(subnet=subnet) if subnet else None

    def findSubnets(self: object) -> list[Subnet] :
        subnets = []
        try:
            subnets = list(self.vpc.subnets.filter( Filters = [  {'Name': 'vpc-id',   'Values': [ self.vpc.id ]} ]))
            subnet_ids = ",".join([subnet.id for subnet in subnets])
            logging.info(f"Found subnets '{subnet_ids}' for vpc {self.vpc.id}")
        except (IndexError, ClientError):
            logging.info(f"Subnets for vpc '{self.vpc.id}' not found")
        return [Subnet(subnet=subnet) for subnet in subnets]

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

    def findSecurityGroup(self: object, name: str = 'default') -> SecurityGroup:
        sg = None
        try:
            sgs = list(Session.ec2_resource.security_groups.filter( 
                Filters = [
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
            subnet:                     Subnet = None, 
            sg:                         SecurityGroup = None, 
            sgs:                        list[SecurityGroup] = None, 
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

        if subnet == None: subnet = self.findSubnet()
        sgs_ids = [ sg.id for sg in sgs ] if sgs else []
        if sg: sgs_ids += sg.id
        if len(sgs_ids) == 0: sgs_ids = [ self.findSecurityGroup().id ]

        ec2_instances = Session.ec2_client.run_instances(
            ImageId             = ami_id if ami_id else Configuration.default_ami_id,
            InstanceType        = instance_type if instance_type else Configuration.default_instance_type, 
            KeyName             = keypair.name,
            MaxCount            = 1,
            MinCount            = 1,
            UserData            = userdata, 
            SecurityGroupIds    = sgs_ids, 
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

    def findLoadBalancer(self: object, name: str) -> ElasticLoadBalancer:
        elb_arn = None
        try:
            elbs = [balancer for balancer 
                    in Session.elbv2_client.describe_load_balancers(Names=[name])['LoadBalancers'] 
                    if balancer['VpcId'] == self.vpc.id]
            if (len(elbs) == 0): raise IndexError(f"Unable to find elastic load balancer '{name}'")
            # intentionally not caught
            if (len(elbs) != 1): raise RuntimeError(f'Unexpected results. Expected 1 elastic load balancer, but got {len(elbs)}')
            elb_arn = elbs[0]["LoadBalancerArn"]
            logging.info(f"Found Elastic Load Balancer '{name}': {elb_arn}")
        except (IndexError, ClientError, AttributeError):
            logging.info(f"Elastic Load Balancer '{name}' not found")
        return ElasticLoadBalancer(arn=elb_arn) if elb_arn else None
    
    def getLoadBalancer(self: object, name: str, subnets: list[Subnet], securityGroups: list[SecurityGroup], type: ElasticLoadBalancerType) -> ElasticLoadBalancer:
        elb = self.findLoadBalancer(name)
        if elb: return elb

        invalid_subnet_ids = [subnet.id for subnet in subnets if subnet.vpc_id != self.vpc.id]
        if len(invalid_subnet_ids):
            ids = ", ".join(invalid_subnet_ids)
            raise RuntimeError(f"Invalid subnet ({ids}) provided. Subnets must belong to VPC '{self.vpc.id}'")
        
        invalid_security_group_ids = [sg.id for sg in securityGroups if sg.vpc_id != self.vpc.id]        
        if len(invalid_subnet_ids):
            ids = ", ".join(invalid_security_group_ids)
            raise RuntimeError(f"Invalid security groups ({ids}) provided. Security groups must belong to VPC '{self.vpc.id}'")

        elb_arn = None
        logging.info(f"Creating Elastic Load Balancer '{name}'")
        elb_arn = Session.elbv2_client.create_load_balancer(
            Name            = name, 
            Subnets         = [subnet.id for subnet in subnets], 
            SecurityGroups  = [sg.id for sg in securityGroups], 
            Scheme          = 'internet-facing', 
            Tags            = [ {'Key': 'Name', 'Value': name} ], 
            Type            = type.value, 
            IpAddressType   = 'ipv4'
        )['LoadBalancers'][0]['LoadBalancerArn']
        logging.info(f"Created Elastic Load Balancer '{name}': {elb_arn}")
        return ElasticLoadBalancer(arn=elb_arn) if elb_arn else None

    def findTargetGroup(self: object, name: str) -> TargetGroup:
        arn = None
        try:
            groups = [group for group 
                      in Session.elbv2_client.describe_target_groups(Names=[name])['TargetGroups']
                      if group['VpcId'] == self.vpc.id]
            if (len(groups) == 0): raise IndexError(f"Unable to find Taget Group '{name}'")
            # intentionally not caught
            if (len(groups) != 1): raise RuntimeError(f'Unexpected results. Expected 1 Taget Group, but got {len(groups)}')
            arn = groups[0]["TargetGroupArn"]
            logging.info(f"Found Taget Group '{name}': {arn}")
        except (IndexError, ClientError, AttributeError):
            logging.info(f"Taget Group '{name}' not found")
        return TargetGroup(arn=arn) if arn else None
    
    def getTargetGroup(self: object, name: str, protocol: TargetGroupProtocol, port: int, type: TargetGroupTargetType) -> TargetGroup:
        group = self.findTargetGroup(name)
        if group: return group

        arn = None
        logging.info(f"Creating Taget Group '{name}'")
        arn = Session.elbv2_client.create_target_group(
            Name        = name, 
            Protocol    = protocol.value, 
            Port        = port, 
            VpcId       = self.vpc.id, 
            TargetType  = type.value
        )['TargetGroups'][0]['TargetGroupArn']

        logging.info(f"Created Taget Group '{name}': {arn}")
        return TargetGroup(arn=arn) if arn else None



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