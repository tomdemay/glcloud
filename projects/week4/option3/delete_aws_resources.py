from common.ec2.vpc import Vpcs
from common.ec2.internet_gateway import InternetGateways
from common.ec2.vpc_address import VpcAddresses
from common.ec2.nat_gateway import NatGateways
from common.ec2.key_pair import KeyPairs

class DeleteAWSResources():
    def run():
        cleanup_stack = [
            (KeyPairs.findKeyPair(name="glkey"), lambda res: res.drop())
        ]
        vpcf                    = (Vpcs.findVpc(name="owncloud-vpc"),            lambda res: res.drop())
        if vpcf[0]:
            mysql_instance      = vpcf[0].findInstance(name='mysql-server')
            owncloud_instance   = vpcf[0].findInstance(name='owncloud-server')
            cleanup_stack += [
                (mysql_instance,                                                 lambda res: res.drop()), 
                (owncloud_instance,                                              lambda res: res.drop()), 
                (mysql_instance,                                                 lambda res: res.wait_for_termination()), 
                (owncloud_instance,                                              lambda res: res.wait_for_termination())
            ]
        cleanup_stack += [
            (NatGateways.findNatGateway(name='owncloud-nat'),                    lambda res: res.drop() or res.wait_until_deleted()), 
            (VpcAddresses.findAllocatedAddress(name='owncloud-eipalloc'),        lambda res: res.drop())
        ]
        if vpcf[0]:
            cleanup_stack += [
                (vpcf[0].findSecurityGroup(name='private-mysql-sg'),             lambda res: res.drop()),
                (vpcf[0].findSecurityGroup(name='public-owncloud-sg'),           lambda res: res.drop()),
                (vpcf[0].findSubnet(name='private-mysql-subnet'),                lambda res: res.drop()),
                (vpcf[0].findSubnet(name='public-owncloud-subnet'),              lambda res: res.drop()),
                (vpcf[0].findRouteTable(name='public-owncloud-rtb'),             lambda res: res.drop()), 
                (vpcf[0].findRouteTable(name='private-mysql-rtb'),               lambda res: res.drop()), 
                (InternetGateways.findInternetGateway(name="owncloud-igw"),      lambda res: res.detachInternetGateway(vpcf[0]) or res.drop())
            ]
        cleanup_stack += [vpcf]

        for resource, func in cleanup_stack: 
            if resource: func(resource)