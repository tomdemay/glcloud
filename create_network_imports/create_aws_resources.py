import logging, pyperclip
from common.config import Configuration
from common.vpc import Vpc, Vpcs
from common.instance import Instance
from common.subnet import Subnet
from common.security_group import SecurityGroup
from common.internet_gateway import InternetGateways
from common.key_pair import KeyPairs

class CreateAWSResources():
    def _getVpc() -> Vpc:
        vpc = Vpcs.getVpc(name=f"{Configuration.project_name} vpc", cidr_block='10.0.0.0/16')
        vpc.wait_until_exists()
        vpc.wait_until_available()
        vpc.enableDnsSupport = True
        vpc.enableDnsHostnames = True
        return vpc

    def _getSubnet(vpc: Vpc) -> Subnet:
        subnet = vpc.getSubnet(
                name                = f"{Configuration.project_name} subnet", 
                cidr_block          = "10.0.1.0/24", 
                availability_zone   = Configuration.region_name + "a")
        subnet.wait_until_available()
        subnet.map_public_ip_on_launch = True
        return subnet

    def _getSecurityGroup(vpc: Vpc) -> SecurityGroup:
        sg = vpc.getSecurityGroup(name=f"{Configuration.project_name} security group")
        for port in set(Configuration.args.ports):
            ingress_description  = f"Open port {port}"
            ingress_name         = ingress_description.lower().replace(" ", "-")
            sg.authorizeIngress(
                from_port   = port, 
                protocol    = 'tcp', 
                cidr_block  = '0.0.0.0/0', 
                name        = ingress_name, 
                description = ingress_description, 
                to_port     = port
            )
        sg.wait_until_exists()
        return sg

    def _getInstance(vpc: Vpc, subnet: Subnet, sg: SecurityGroup) -> Instance:
        keypair = KeyPairs.getKeyPair(name=Configuration.project_name.lower().replace(' ', '-'))
        keypair.wait_until_exists()
        bootstrap_string = None
        if Configuration.args.aws_access_key_id and Configuration.args.aws_secret_access_key and Configuration.args.bootstrap_script:
            with open(Configuration.args.bootstrap_script) as f:
                bootstrap_string = f.read().format(Configuration.args.aws_access_key_id, Configuration.args.aws_secret_access_key)

        instance = vpc.runInstance(
            name            = f"{Configuration.project_name} instance", 
            keypair         = keypair, 
            subnet          = subnet, 
            sg              = sg, 
            bootstrap_str   = bootstrap_string, 
            bootstrap_file  = None if bootstrap_string else Configuration.args.bootstrap_script )
        return instance
    
    def _addRoute(vpc: Vpc) -> None:
        igw = InternetGateways.getInternetGateway(name=f"{Configuration.project_name} igw")
        igw.attachInternetGateway(vpc)
        rtb = vpc.getRouteTable()
        rtb.addIgwRoute(igw, '0.0.0.0/0')
    
    def run(project_name: str):
        vpc         = CreateAWSResources._getVpc()
        subnet      = CreateAWSResources._getSubnet(vpc=vpc)
        sg          = CreateAWSResources._getSecurityGroup(vpc=vpc) 
        instance    = CreateAWSResources._getInstance(vpc=vpc, subnet=subnet, sg=sg)
        CreateAWSResources._addRoute(vpc)

        instance.wait_for_status_ok()

        pyperclip.copy(instance.public_ip_address)

        logging.info(f'''

            Instance IP Address: {instance.public_ip_address}. 
            The IP address has been copied to your clipboard. 
            
        ''')