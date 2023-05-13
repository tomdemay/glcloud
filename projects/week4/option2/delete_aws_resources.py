import os
from common.config import Configuration
from common.vpc import Vpcs
from common.internet_gateway import InternetGateways
from common.vpc_address import VpcAddresses
from common.nat_gateway import NatGateways
from common.key_pair import KeyPairs

class DeleteAWSResources():
    def run(project_name: str):
        vpc_name                     = f"{project_name} vpc"
        internet_gateway_name        = f"{project_name} igw"
        key_pair_name                = project_name.replace(' ', '-')
        key_pair_filename            = key_pair_name + ".pem"
        subnet_name                  = f"{project_name} subnet"
        security_group_name          = f"{project_name} security group"
        instance_name                = f"{project_name} instance"

        cleanup_stack = [
            (KeyPairs.findKeyPair(name=key_pair_name), lambda res: res.drop())
        ]
        vpcf                    = (Vpcs.findVpc(name=vpc_name),                     lambda res: res.drop())
        if vpcf[0]:
            instance            = vpcf[0].findInstance(instance_name)
            cleanup_stack += [
                (instance,                                                          lambda res: res.drop()), 
                (instance,                                                          lambda res: res.wait_for_termination()), 
            ]
        if vpcf[0]:
            cleanup_stack += [
                (vpcf[0].findSecurityGroup(name=security_group_name),               lambda res: res.drop()),
                (vpcf[0].findSubnet(name=subnet_name),                              lambda res: res.drop()),
                (InternetGateways.findInternetGateway(name=internet_gateway_name),  lambda res: res.detachInternetGateway(vpcf[0]) or res.drop())
            ]
        cleanup_stack += [vpcf]

        for resource, func in cleanup_stack: 
            if resource: func(resource)