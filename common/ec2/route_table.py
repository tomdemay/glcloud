import logging
from common.aws_resource_interface import AWSResourceInterface

class RouteTable(AWSResourceInterface):
    def __init__(self: object, rtb: object):
        self.rtb = rtb

    @property
    def id(self: object) -> str:
        return self.rtb.id

    def addIgwRoute(self: object, igw: object, cidr_block: str) -> None:
        if self._findRoute(target_id_name='GatewayId', target=igw, cidr_block=cidr_block): return

        logging.debug(f"Adding route to '{cidr_block}' through internet gateway '{igw.id}' on route table '{self.rtb.id}'...")
        self.rtb.create_route(DestinationCidrBlock=cidr_block, GatewayId=igw.id)
        logging.info(f"Route added to '{cidr_block}' through internet gateway '{igw.id}' on route table '{self.rtb.id}'")

    def addNatRoute(self: object, nat: object, cidr_block: str) -> None:
        if self._findRoute(target_id_name='NatGatewayId', target=nat, cidr_block=cidr_block): return
        
        logging.debug(f"Adding route to '{cidr_block}' through NAT gateway '{nat.id}' on route table '{self.rtb.id}'...")
        self.rtb.create_route(DestinationCidrBlock=cidr_block, NatGatewayId=nat.id)
        logging.info(f"Route added to '{cidr_block}' through NAT gateway '{nat.id}' on route table '{self.rtb.id}'")

    def _findRoute(self: object, target_id_name: str, target: object, cidr_block: str) -> bool:
        for route in self.rtb.routes_attribute:
            if route['DestinationCidrBlock'] == cidr_block \
                    and route[target_id_name] == target.id:
                logging.info(f"Route to '{cidr_block}' through target '{target.id}' on route table '{self.rtb.id}' found")
                return True
            
        logging.debug(f"Route to '{cidr_block}' through target '{target.id}' on route table '{self.rtb.id}' not found")
        return False

    def associate_with_subnet(self: object, subnet: object) -> None:
        for association in self.rtb.associations_attribute:
            if association['SubnetId'] == subnet.id:
                logging.info(f"Route table '{self.rtb.id}' is already associated with subnet '{subnet.id}'")
                return
            
        logging.debug(f"Associating route table '{self.rtb.id}' with subnet '{subnet.id}'...")
        self.rtb.associate_with_subnet(SubnetId=subnet.id)
        logging.info(f"Associated route table '{self.rtb.id}' with subnet '{subnet.id}'")

    def drop(self: object) -> None:
        logging.debug(f"Deleting route table '{self.rtb}'...")
        self.rtb.delete()
        logging.info(f"Deleted route table '{self.rtb}'")
