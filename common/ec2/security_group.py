import logging
from botocore.exceptions import ClientError
from common.session import Session
from common.aws_resource_interface import AWSResourceInterface

class SecurityGroup(AWSResourceInterface):
    def __init__(self:object, sg: object):
        self.sg = sg

    @property
    def id(self: object) -> str:
        return self.sg.id
    
    @property
    def vpc_id(self: object) -> str:
        return self.sg.vpc_id

    def authorizeIngress(self: object, from_port: int, protocol: str, cidr_block: str, name: str, description: str, to_port: int) -> None:
        try:
            for ingress in self.sg.ip_permissions:
                if ingress['FromPort'] == from_port \
                        and ingress['IpProtocol'] == protocol \
                        and ingress['ToPort'] == to_port:
                    for iprange in ingress['IpRanges'] :
                        if iprange['CidrIp'] == cidr_block :
                            logging.info(f"Security Group Ingress rule '{description}' is already authorized")
                            return
            raise IndexError
        except (IndexError,ClientError):
            logging.debug(f"Security Group Ingress rule '{description}' is being authorized...")
            self.sg.authorize_ingress(
                IpPermissions = [{
                    'FromPort': from_port, 
                    'IpProtocol': protocol, 
                    'IpRanges': [{
                        'CidrIp': cidr_block, 
                        'Description': description 
                    }], 
                    'ToPort': to_port
                }], 
                TagSpecifications = [{
                    'ResourceType': 'security-group-rule',
                    'Tags': [
                        {'Key': 'Name', 'Value': name}
                    ]
                }]            
            )
            logging.info(f"Security Group Ingress rule '{description}' has been authorized")

    def wait_until_exists(self: object) -> None:
        Session.ec2_client.get_waiter("security_group_exists").wait(GroupIds=[self.sg.id])

    def drop(self: object) -> None:
        logging.debug(f"Deleting security group '{self.sg}'...")
        self.sg.delete()
        logging.info(f"Deleted security group '{self.sg}'")

