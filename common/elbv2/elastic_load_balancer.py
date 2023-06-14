import logging
from enum import Enum
from botocore.exceptions import ClientError
from common.session import Session
from common.elbv2.target_group import TargetGroup
from common.elbv2.listener import Listener, ListenerProtocol

class ElasticLoadBalancerType(Enum):
    APPLICATION = 'application'
    NETWORK     = 'network'
    GATEWAY     = 'gateway'

class ElasticLoadBalancer:
    def __init__(self: object, arn: str):
        self._arn = arn

    @property
    def arn(self: object):
        return self._arn
    
    def findListener(self: object, protocol: ListenerProtocol, port: int) -> Listener:
        arn = None
        try:
            listeners = [listener for listener 
                         in Session.elbv2_client.describe_listeners(LoadBalancerArn=self._arn)['Listeners']
                         if listener['Protocol'] == protocol.value and listener['Port'] == port]
            if (len(listeners) == 0): raise IndexError(f"Unable to find Listener for load balancer '{self._arn}'")
            # intentionally not caught
            if (len(listeners) != 1): raise RuntimeError(f'Unexpected results. Expected 1 Listener, but got {len(listeners)}')
            arn = listeners[0]["ListenerArn"]
            logging.info(f"Found Listener for load balancer '{self._arn}': {arn}")
        except (IndexError, ClientError, AttributeError):
            logging.info(f"Listener for load balancer '{self._arn}' not found")
        return Listener(arn=arn, protocol=protocol, port=port) if arn else None
    
    def getListener(self: object, protocol: ListenerProtocol, port: int, target_group: TargetGroup) -> Listener:
        listener = self.findListener(protocol, port)
        if listener: return listener

        arn = None
        logging.info(f"Creating Listener for load balancer '{self._arn}'")
        arn = Session.elbv2_client.create_listener(
            LoadBalancerArn = self._arn, 
            Protocol        = protocol.value, 
            Port            = port, 
            DefaultActions  = [
                {
                    'Type': 'forward', 
                    'TargetGroupArn': target_group.arn
                }
            ]
        )['Listeners'][0]['ListenerArn']

        logging.info(f"Created Listener for load balancer '{self._arn}': {arn}")
        return Listener(arn=arn, protocol=protocol, port=port) if arn else None
    
    def wait_until_available(self: object):
        logging.info(f"Waiting for Elastic Load Balancer '{self.arn}' to be available (this might take a few minutes)...")
        Session.elbv2_client.get_waiter("load_balancer_available").wait(LoadBalancerArns=[self.arn])
        logging.info(f"Elastic Load Balancer '{self.arn}' is available")

    def wait_until_deleted(self: object) -> None:
        logging.info(f"Waiting for Elastic Load Balancer '{self.arn}' to be deleted (this might take a few minutes)...")
        Session.elbv2_client.get_waiter("load_balancers_deleted").wait(LoadBalancerArns=[self.arn])
        logging.info(f"Elastic Load Balancer '{self.arn}' has been deleted")

    def drop(self: object) -> None:
        logging.info(f"Deleting Elastic Load Balancer '{self.arn}'")
        Session.elbv2_client.delete_load_balancer(LoadBalancerArn = self.arn)
        logging.info(f"Deleted Elastic Load Balancer '{self.arn}'")
