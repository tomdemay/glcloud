from common.vpc import Vpcs
from common.internet_gateway import InternetGateways
from common.key_pair import KeyPairs

class DeleteAWSResources():
    def run(project_name: str):
        keypair     = KeyPairs.findKeyPair(name=project_name.lower().replace(' ', '-'))
        igw         = InternetGateways.findInternetGateway(f"{project_name} igw")
        vpc         = Vpcs.findVpc(name=f"{project_name} vpc")
        subnet      = vpc.findSubnet(name=f"{project_name} subnet") if vpc else None
        sg          = vpc.findSecurityGroup(name=f"{project_name} security group") if vpc else None
        instance    = vpc.findInstance(f"{project_name} instance") if vpc else None
        cleanup_stack = [
            (keypair,   lambda res: res.drop()),
            (instance,  lambda res: res.drop()), 
            (instance,  lambda res: res.wait_for_termination()),
            (sg,        lambda res: res.drop()),
            (subnet,    lambda res: res.drop()),
            (igw,       lambda res: res.detachInternetGateway(vpc)),
            (igw,       lambda res: res.drop()),
            (vpc,       lambda res: res.drop())
        ]
        for resource, func in cleanup_stack: 
            if resource: func(resource)