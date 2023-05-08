import logging
from botocore.exceptions import ClientError
from common.config import Configuration
from common.aws_resource_interface import AWSResourceInterface

class VpcAddress(AWSResourceInterface):
    def __init__(self: object, eipalloc: object):
        self.eipalloc = eipalloc

    @property
    def id(self: object) -> str:
        return self.eipalloc.allocation_id
    
    def drop(self: object) -> None:
        logging.debug(f"Deleting elastic ip allocation '{self.eipalloc}'...")
        self.eipalloc.release()
        logging.info(f"Deleted elastic ip allocation '{self.eipalloc}'")

class VpcAddresses:
    def findAllocatedAddress(name: str) -> object:
        eipalloc = None
        try:
            eipallocs = list(Configuration.session.ec2_resource.vpc_addresses.filter(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [ name ] }
                ]
            ))
            if (len(eipallocs) == 0): raise IndexError(f"Unable to find elastic ip '{name}'")
            # intentionally not caught
            if (len(eipallocs) != 1): raise RuntimeError(f'Unexpected results. Expected 1 elastic ip, but got {len(eipallocs)}')
            eipalloc = eipallocs[0]
            logging.info(f"Found elastic ip allocation '{name}': {eipalloc}")
        except (IndexError,ClientError):
            logging.info(f"Elastic ip '{name}' not found")
        return VpcAddress(eipalloc=eipalloc) if eipalloc else None

    def allocateAddress(name: str) -> object:
        eipalloc = VpcAddresses.findAllocatedAddress(name)
        if eipalloc: return eipalloc

        logging.debug(f"Allocating elastic ip '{name}'...")
        eipalloc_id = Configuration.session.ec2_client.allocate_address(
            Domain='vpc',
            TagSpecifications=[{
                'ResourceType': 'elastic-ip',
                'Tags'        : [
                    {'Key': 'Name', 'Value': name}
                ]
            }], 
        )['AllocationId']
        ec2_eipalloc = Configuration.session.ec2_resource.VpcAddress(eipalloc_id)
        logging.info(f"Created elastic ip '{name}': {ec2_eipalloc}")
        return VpcAddress(eipalloc=ec2_eipalloc) if ec2_eipalloc else None
