import logging, os
from botocore.exceptions import ClientError
from common.session import Session
from common.aws_resource_interface import AWSResourceInterface

class KeyPair(AWSResourceInterface):
    def __init__(self: object, keypair: object):
        self.keypair = keypair

    @property
    def id(self: object) -> str:
        return self.keypair.key_pair_id
    
    @property
    def name(self: object) -> str:
        return self.keypair.key_name
    
    @property
    def filename(self: object) -> str:
        return os.path.join("./pemfiles/", self.name + '.pem')
    
    def save(self: object) -> None:
        logging.debug(f"Downloading keypair '{self.keypair}' to {self.filename}...")
        with open(self.filename, 'w') as file: 
            file.write(self.keypair.key_material)
        os.chmod(self.filename, 0o400)
        logging.info(f"Saved keypair '{self.keypair}' to {self.filename}")

    def wait_until_exists(self: object):
        Session.ec2_client.get_waiter("key_pair_exists").wait(KeyPairIds=[self.keypair.key_pair_id])

    def drop(self: object) -> None:
        logging.debug(f"Deleting keypair filename '{self.filename}'...")
        if os.path.isfile(self.filename):
            os.chmod(self.filename, 0o666)
            os.remove(self.filename)
        logging.info(f"Deleted keypair filename '{self.filename}'")
        logging.debug(f"Deleting keypair '{self.keypair}'...")
        self.keypair.delete()
        logging.info(f"Deleted keypair '{self.keypair}'")

class KeyPairs:
    def getKeyPair(name: str):
        keypair = KeyPairs.findKeyPair(name)
        if keypair: return keypair

        logging.debug(f"Creating keypair '{name}'...")
        ec2_keypair = Session.ec2_resource.create_key_pair(
            KeyName=name, 
            KeyFormat='pem'
        )
        logging.info(f"Created keypair '{name}': {ec2_keypair}")
        keypair = KeyPair(keypair=ec2_keypair) if ec2_keypair else None        
        keypair.save()
        return keypair

    def findKeyPair(name: str):
        keypair = None
        try:
            keypairs = list(Session.ec2_resource.key_pairs.filter(
                KeyNames=[name]
            ))
            if len(keypairs) == 0: raise IndexError(f"Unable to find keypair '{name}'")
            # intentionally not caught
            if len(keypairs) != 1: raise RuntimeError(f"Unexpected results. Expected 1 internet gateway but got {len(keypairs)}")
            keypair = keypairs[0]
            logging.info(f"Found keypair '{name}': {keypair}")
        except (IndexError,ClientError):
            logging.info(f"Key pair '{name}' not found")
        return KeyPair(keypair=keypair) if keypair else None
