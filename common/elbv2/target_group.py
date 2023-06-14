import logging
from common.session import Session
from enum import Enum

class TargetGroupTargetType(Enum):
    INSTANCE    = 'instance'
    IP          = 'ip'
    LAMBDA      = 'lambda'
    ALB         = 'alb'

class TargetGroupProtocol(Enum):
    HTTP        = 'HTTP'
    HTTPS       = 'HTTPS'
    TCP         = 'TCP'
    TLS         = 'TLS'
    UDP         = 'UDP'
    TCP_UDP     = 'TCP_UDP'
    GENEVE      = 'GENEVE'

class TargetGroup:
    def __init__(self: object, arn: str):
        self._arn = arn

    @property
    def arn(self: object):
        return self._arn
    
    def drop(self: object) -> None:
        logging.info(f"Deleting Taget Group '{self.arn}'")
        Session.elbv2_client.delete_target_group(TargetGroupArn = self.arn)
        logging.info(f"Deleted Taget Group '{self.arn}'")

