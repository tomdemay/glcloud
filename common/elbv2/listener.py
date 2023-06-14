import logging
from common.session import Session
from enum import Enum

class ListenerProtocol(Enum):
    HTTP        = 'HTTP'
    HTTPS       = 'HTTPS'
    TCP         = 'TCP'
    TLS         = 'TLS'
    UDP         = 'UDP'
    TCP_UDP     = 'TCP_UDP'
    GENEVE      = 'GENEVE'

class Listener:
    def __init__(self: object, arn: str, protocol: ListenerProtocol, port: int):
        self._arn       = arn
        self._protocol  = protocol
        self._port      = port

    @property
    def arn(self: object) -> str:
        return self._arn
    
    @property
    def protocol(self: object) -> ListenerProtocol: 
        return self._protocol
    
    @property
    def port(self: object) -> int:
        return self._port
    
    def drop(self: object) -> None:
        logging.info(f"Deleting Listener '{self.arn}'")
        Session.elbv2_client.delete_listener(ListenerArn = self.arn)
        logging.info(f"Deleted Listener '{self.arn}'")

