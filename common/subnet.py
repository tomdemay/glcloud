import logging
from common.session import Session
from common.aws_resource_interface import AWSResourceInterface

class Subnet(AWSResourceInterface):
    def __init__(self, subnet: object):
        self.subnet = subnet

    @property
    def id(self: object) -> str:
        return self.subnet.id
    
    @property
    def availability_zone(self: object) -> str:
        return self.subnet.availability_zone
    
    @property
    def map_public_ip_on_launch(self: object) -> str:
        return self.subnet.map_public_ip_on_launch

    @map_public_ip_on_launch.setter
    def map_public_ip_on_launch(self: object, value: bool):
        if self.subnet.map_public_ip_on_launch != value:
            Session.ec2_client.modify_subnet_attribute(
                SubnetId = self.subnet.id, 
                MapPublicIpOnLaunch = {"Value": value}
            )
            # refresh self
            self.subnet = list(self.subnet.vpc.subnets.filter(SubnetIds = [self.subnet.id]))[0]

    def wait_until_available(self: object) -> None:
        Session.ec2_client.get_waiter("subnet_available").wait(SubnetIds=[self.subnet.id])
        
    def drop(self: object) -> None:
        logging.debug(f"Deleting subnet '{self.subnet}'...")
        self.subnet.delete()
        logging.info(f"Deleted subnet '{self.subnet}'")

