import logging
from common.config import Configuration
from common.vpc import Vpc, Vpcs
from common.subnet import Subnet
from common.security_group import SecurityGroup
from common.route_table import RouteTable
from common.internet_gateway import InternetGateway, InternetGateways
from common.vpc_address import VpcAddress, VpcAddresses
from common.nat_gateway import NatGateway, NatGateways
from common.key_pair import KeyPair, KeyPairs
from common.instance import Instance

class CreateAWSResources():
    def _getVpc() -> Vpc:
        vpc = Vpcs.getVpc(name="Project 1 VPC", cidr_block=Configuration.vpc_cidr_block)
        vpc.wait_until_exists()
        vpc.wait_until_available()
        vpc.enableDnsSupport = True
        vpc.enableDnsHostnames = True
        return vpc

    def _getTopLevelObjects():
        return \
            InternetGateways.getInternetGateway(name='Project 1 Internet Gateway'), \
            VpcAddresses.allocateAddress(name="Project 1 Elastic IP"), \
            KeyPairs.getKeyPair(name=Configuration.connectivity_keypair_name)

    def _getSubnets(vpc: Vpc):
        return \
            vpc.getSubnet(
                name                ='Public Subnet', 
                cidr_block          =Configuration.public_subnet_cidr_blck, 
                availability_zone   =Configuration.public_subnet_availability_zone), \
            vpc.getSubnet(
                name                ='Private Subnet', 
                cidr_block          =Configuration.private_subnet_cidr_blck, 
                availability_zone   =Configuration.private_subnet_availability_zone)

    def _getRouteTables(vpc: Vpc):
        return \
            vpc.getRouteTable(name='Public Route Table'), \
            vpc.getRouteTable(name='Private Route Table')

    def _getSecurityGroups(vpc: Vpc):
        return \
            vpc.getSecurityGroup(name='Project 1 Mattermost Security Group', description="Opens SSH, HTTP, HTTPS, Mattermost ports from the internet"), \
            vpc.getSecurityGroup(name='Project 1 MySQL Server', description="Opens SSH, HTTP, HTTPs, MySQL ports from the public subnet")

    def _getNatGateway(vpc: Vpc, igw: InternetGateway, eipalloc: VpcAddress, subnet: Subnet) -> NatGateway:
        igw.wait_until_gateway_exists()
        igw.attachInternetGateway(vpc)
        natgateway = NatGateways.getNatGateway(eipalloc=eipalloc, subnet=subnet, name='Project 1 NAT Gateway')
        natgateway.wait_until_available()
        return natgateway

    def _getInstances(vpc: Vpc, keypair: KeyPair, private_subnet: Subnet, public_subnet: Subnet, private_sg: SecurityGroup, public_sg: SecurityGroup):
        keypair.wait_until_exists()
        private_subnet.wait_until_available()
        private_sg.wait_until_exists()
        mysql_server        = vpc.runInstance(
                name                    ='Project 1 MySQL Server', 
                keypair                 =keypair, 
                subnet                  =private_subnet, 
                sg                      =private_sg, 
                ami_id                  ='ami-02396cdd13e9a1257',               # hard coding Amazon AMI as it's required for this project
                type                    =Configuration.instances_type,
                bootstrap_file          ='./bootstrap/mysql-server-centos.sh')
        mysql_server.wait_for_status_ok()

        bootstrap_str = ''
        with open('./bootstrap/mattermost-centos.sh') as f: 
            bootstrap_str = f.read().format(mysql_server.private_ip_address)

        public_subnet.wait_until_available()
        public_subnet.map_public_ip_on_launch = True
        public_sg.wait_until_exists()
        mattermost_server     = vpc.runInstance(
                name                    ='Project 1 Mattermost Server', 
                keypair                 =keypair, 
                subnet                  =public_subnet, 
                sg                      =public_sg, 
                ami_id                  ='ami-02396cdd13e9a1257',               # hard coding Amazon AMI as it's required for this project
                type                    =Configuration.instances_type,
                bootstrap_str           =bootstrap_str)
        
        return mysql_server, mattermost_server
    
    def _wire_everything_up(
            igw: InternetGateway,
            public_rtb: RouteTable, 
            private_rtb: RouteTable, 
            public_subnet: Subnet, 
            private_subnet: Subnet,
            public_sg: SecurityGroup, 
            private_sg: SecurityGroup, 
            nat_gateway: NatGateway):
        public_sg.authorizeIngress(from_port=22, protocol='tcp', cidr_block='0.0.0.0/0', name='open-ssh-public', description='Opening SSH from the internet', to_port=22)
        public_sg.authorizeIngress(from_port=443, protocol='tcp', cidr_block='0.0.0.0/0', name='open-https-public', description='Opening HTTPS from the internet', to_port=443)
        public_sg.authorizeIngress(from_port=80, protocol='tcp', cidr_block='0.0.0.0/0', name='open-http-public', description='Opening HTTP from the internet', to_port=80)
        public_sg.authorizeIngress(from_port=8065, protocol='tcp', cidr_block='0.0.0.0/0', name='open-mattermost-public', description='Opening Mattermost from the internet', to_port=8065)
        private_sg.authorizeIngress(from_port=22, protocol='tcp', cidr_block=Configuration.public_subnet_cidr_blck, name='open-ssh-private', description='Opening SSH from the public subnet', to_port=22)
        private_sg.authorizeIngress(from_port=80, protocol='tcp', cidr_block=Configuration.public_subnet_cidr_blck, name='open-http-private', description='Opening HTTP from the public subnet', to_port=80)
        private_sg.authorizeIngress(from_port=443, protocol='tcp', cidr_block=Configuration.public_subnet_cidr_blck, name='open-https-private', description='Opening HTTPS from the public subnet', to_port=443)
        private_sg.authorizeIngress(from_port=3306, protocol='tcp', cidr_block=Configuration.public_subnet_cidr_blck, name='open-mysql-private', description='Opening MySQL from the public subnet', to_port=3306)
        public_rtb.addIgwRoute(igw, '0.0.0.0/0')
        public_rtb.associate_with_subnet(public_subnet)
        private_rtb.addNatRoute(nat_gateway, '0.0.0.0/0')
        private_rtb.associate_with_subnet(private_subnet)

    def _wait_for_status_ok(instances):
        [instance.wait_for_status_ok() for instance in instances]

    def run():
        vpc                               = CreateAWSResources._getVpc()
        igw, eipalloc, keypair            = CreateAWSResources._getTopLevelObjects()
        public_subnet, private_subnet     = CreateAWSResources._getSubnets(vpc=vpc)
        public_rtb, private_rtb           = CreateAWSResources._getRouteTables(vpc=vpc)
        public_sg, private_sg             = CreateAWSResources._getSecurityGroups(vpc=vpc) 
        nat_gateway                       = CreateAWSResources._getNatGateway(vpc=vpc, igw=igw, eipalloc=eipalloc, subnet=public_subnet)
        mysql_server, mattermost_server   = CreateAWSResources._getInstances(
                                            vpc=vpc, 
                                            keypair=keypair, 
                                            private_subnet=private_subnet, 
                                            public_subnet=public_subnet, 
                                            private_sg=private_sg, 
                                            public_sg=public_sg)
        CreateAWSResources._wire_everything_up(
            igw=igw, 
            public_rtb=public_rtb, 
            private_rtb=private_rtb,
            public_subnet=public_subnet, 
            private_subnet=private_subnet,
            public_sg=public_sg, 
            private_sg=private_sg, 
            nat_gateway=nat_gateway
        )

        CreateAWSResources._wait_for_status_ok([mysql_server, mattermost_server])

        logging.info(f'''

            Open web broswer to {mattermost_server.public_ip_address}:8065. 

        ''')