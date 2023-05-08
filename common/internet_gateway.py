import logging, time
from botocore.exceptions import ClientError
from common.config import Configuration
from common.aws_resource_interface import AWSResourceInterface

class InternetGateway(AWSResourceInterface):
    def __init__(self: object, igw: object):
        self.igw = igw

    @property
    def id(self: object) -> str:
        return self.igw.id

    def attachInternetGateway(self: object, vpc: object) -> None:
        for attachment in self.igw.attachments:
            if attachment['VpcId'] == vpc.id:
                logging.info(f"Internet gateway '{self.igw.id}' is already attached to vpc '{vpc.id}")
                return
            
        logging.debug(f"Attaching internet gateway '{self.igw.id}' to vpc '{vpc.id}...")
        self.igw.attach_to_vpc(VpcId=vpc.id)
        logging.info(f"Attached internet gateway '{self.igw.id}' to vpc '{vpc.id}")       

    def detachInternetGateway(self: object, vpc: object) -> None:
        for attachment in self.igw.attachments:
            if attachment["VpcId"] == vpc.id:
                logging.debug(f"Detaching internet gateway '{self.igw.id}' from '{vpc.id}'...")
                self.igw.detach_from_vpc(VpcId=vpc.id)
                logging.info(f"Detached internet gateway '{self.igw.id}' from '{vpc.id}'")
                return

        logging.info(f"Internet gateway '{self.igw.id}' is already detached from '{vpc.id}'")
        return

    def wait_until_gateway_exists(self: object) -> None:
        Configuration.session.ec2_client.get_waiter("internet_gateway_exists").wait(InternetGatewayIds=[self.igw.id])

    def drop(self: object) -> None:
        logging.debug(f"Deleting internet gateway '{self.igw}'...")
        self.igw.delete()
        logging.info(f"Deleted internet gateway '{self.igw}'")
        

class InternetGateways:
    def getInternetGateway(name: str) -> object:
        igw = InternetGateways.findInternetGateway(name=name)
        if igw: return igw

        logging.debug(f"Creating internet gateway '{name}'...")
        ec2_igw = Configuration.session.ec2_resource.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags'        : [
                    {'Key': 'Name', 'Value': name}
                ]
            }], 
        )
        # timing issue here..... inject sleep. getting InvalidInternetGatewayID.NotFound on waiter call
        time.sleep(1)
        logging.info(f"Created internet gateway '{name}': {ec2_igw}")
        return InternetGateway(igw=ec2_igw) if ec2_igw else None

    def findInternetGateway(name: str) -> object:
        igw = None
        try:
            igws = list(Configuration.session.ec2_resource.internet_gateways.filter(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [ name ] }
                ]
            ))
            if (len(igws) == 0): raise IndexError(f"Unable to find internet gateway '{name}'")
            # intentionally not caught
            if (len(igws) != 1): raise RuntimeError(f'Unexpected results. Expected 1 internet gateway, but got {len(igws)}')
            igw = igws[0]
            logging.info(f"Found internet gateway '{name}': {igw}")
        except (IndexError,ClientError):
            logging.info(f"Internet gateway '{name}' not found")
        return InternetGateway(igw=igw) if igw else None
