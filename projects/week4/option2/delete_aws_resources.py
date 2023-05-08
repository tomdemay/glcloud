from common.config import Configuration
from common.vpc import Vpcs
from common.internet_gateway import InternetGateways
from common.vpc_address import VpcAddresses
from common.nat_gateway import NatGateways
from common.key_pair import KeyPairs

class DeleteAWSResources():
    def run():
        cleanup_stack = [
            (KeyPairs.findKeyPair(name=Configuration.connectivity_keypair_name), lambda res: res.drop())
        ]
        vpcf                    = (Vpcs.findVpc(name="Project 1 VPC"),                      lambda res: res.drop())
        if vpcf[0]:
            mysql_instance      = vpcf[0].findInstance(name='Project 1 MySQL Server')
            mattermost_instance   = vpcf[0].findInstance(name='Project 1 Mattermost Server')
            cleanup_stack += [
                (mysql_instance,                                                            lambda res: res.drop()), 
                (mattermost_instance,                                                       lambda res: res.drop()), 
                (mysql_instance,                                                            lambda res: res.wait_for_termination()), 
                (mattermost_instance,                                                       lambda res: res.wait_for_termination())
            ]
        cleanup_stack += [
            (NatGateways.findNatGateway(name='Project 1 NAT Gateway'),                      lambda res: res.drop() or res.wait_until_deleted()), 
            (VpcAddresses.findAllocatedAddress(name='Project 1 Elastic IP'),                lambda res: res.drop())
        ]
        if vpcf[0]:
            cleanup_stack += [
                (vpcf[0].findSecurityGroup(name='Project 1 MySQL Server'),                  lambda res: res.drop()),
                (vpcf[0].findSecurityGroup(name='Project 1 Mattermost Security Group'),     lambda res: res.drop()),
                (vpcf[0].findSubnet(name='Private Subnet'),                                 lambda res: res.drop()),
                (vpcf[0].findSubnet(name='Public Subnet'),                                  lambda res: res.drop()),
                (vpcf[0].findRouteTable(name='Public Route Table'),                         lambda res: res.drop()), 
                (vpcf[0].findRouteTable(name='Private Route Table'),                        lambda res: res.drop()), 
                (InternetGateways.findInternetGateway(name="Project 1 Internet Gateway"),   lambda res: res.detachInternetGateway(vpcf[0]) or res.drop())
            ]
        cleanup_stack += [vpcf]

        for resource, func in cleanup_stack: 
            if resource: func(resource)