import logging
from botocore.exceptions import ClientError
from common.session import Session
from common.aws_resource_interface import AWSResourceInterface

class NatGateway(AWSResourceInterface):
    def __init__(self: object, nat_id: str):
        self.nat_id = nat_id

    @property
    def id(self: object) -> str:
        return self.nat_id
    
    def wait_until_available(self: object):
        logging.info(f"Waiting for NAT Gateway '{self.nat_id}' to be available (this might take a few minutes)...")
        Session.ec2_client.get_waiter("nat_gateway_available").wait(NatGatewayIds=[self.nat_id])
        logging.info(f"NAT Gateway '{self.nat_id}' is available")

    def wait_until_deleted(self: object) -> None:
        logging.info(f"Waiting for NAT Gateway '{self.nat_id}' to be deleted (this might take a few minutes)...")
        Session.ec2_client.get_waiter("nat_gateway_deleted").wait(NatGatewayIds=[self.nat_id])
        logging.info(f"NAT Gateway '{self.nat_id}' has been deleted")

    def drop(self: object) -> None:
        logging.info(f"Deleting NAT Gateway '{self.nat_id}'")
        Session.ec2_client.delete_nat_gateway(NatGatewayId = self.nat_id)
        logging.info(f"Deleted NAT Gateway '{self.nat_id}'")

class NatGateways:
    def findNatGateway(name: str) -> NatGateway:
        nat_id = None
        try:
            nats = Session.ec2_client.describe_nat_gateways(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [ name ] },
                    {'Name': 'state',    'Values': [ 'pending', 'available' ]}
                ]
            )['NatGateways']
            if (len(nats) == 0): raise IndexError(f"Unable to find NAT gateways '{name}'")
            # intentionally not caught
            if (len(nats) != 1): raise RuntimeError(f'Unexpected results. Expected 1 NAT gateway, but got {len(nats)}')
            nat_id = nats[0]["NatGatewayId"]
            logging.info(f"Found NAT gateway '{name}': {nat_id}")
        except (IndexError, ClientError):
            logging.info(f"NAT gateway '{name}' not found")
        return NatGateway(nat_id=nat_id) if nat_id else None

    def getNatGateway(eipalloc: object, subnet: object, name: str) -> NatGateway:
        nat = NatGateways.findNatGateway(name)
        if nat: return nat

        nat_id = None
        logging.info(f"Creating NAT gateway '{name}'")
        nat_id = Session.ec2_client.create_nat_gateway(
            AllocationId = eipalloc.id, 
            SubnetId = subnet.id, 
            TagSpecifications = [{
                'ResourceType': 'natgateway', 
                'Tags': [
                    { 'Key': 'Name', 'Value': name } 
                ]
            }]
        )['NatGateway']['NatGatewayId']
        logging.info(f"Created NAT gateway '{name}': {nat_id}")
        return NatGateway(nat_id=nat_id) if nat_id else None
