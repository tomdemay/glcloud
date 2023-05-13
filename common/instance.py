import logging
from common.session import Session
from common.aws_resource_interface import AWSResourceInterface

class Instance(AWSResourceInterface):
    def __init__(self: object, instance: object):
        self.instance = instance

    @property
    def id(self: object) -> str:
        return self.instance.instance_id
    
    @property
    def public_ip_address(self: object) -> str:
        return self.instance.public_ip_address
    
    @property
    def private_ip_address(self: object) -> str:
        return self.instance.private_ip_address

    def wait_until_terminated(self: object):
        logging.debug(f"Waiting for ec2 instance '{self.instance}' to terminate...")
        self.instance.wait_until_terminated()
        logging.info(f"Ec2 instance '{self.instance} has been terminated'")

    def wait_for_status_ok(self: object) -> None:
        logging.info(f"Waiting for status okay for instance '{self.instance}' (this might take a few minutes)...")
        Session.ec2_client.get_waiter("instance_status_ok").wait(InstanceIds=[self.id])
        logging.info(f"Received okay status for instance '{self.instance}'")

    def wait_for_termination(self: object) -> None:    
        logging.info(f"Waiting for instance '{self.instance}' to terminate (this might take a few minutes)...")
        Session.ec2_client.get_waiter("instance_terminated").wait(InstanceIds=[self.id])
        logging.info(f"Instance '{self.instance}' has been terminated")

    def drop(self: object):
        logging.debug(f"Deleting ec2 instance '{self.instance}' (this might take a few minutes)...")
        self.instance.terminate()
        logging.info(f"Deleted ec2 instance '{self.instance}'")
