import boto3
from common.utils import classproperty

class Session:
    _connected = False

    def connect(profile_name: str, region_name: str):
        if Session._connected: return
        Session._profile_name   = profile_name
        Session._region_name    = region_name
        Session._aws_session    = boto3.session.Session(
            profile_name    = Session._profile_name, 
            region_name     = Session._region_name
        )
        Session._ec2_resource   = Session._aws_session.resource('ec2')
        Session._ec2_client     = Session._aws_session.client('ec2')
        Session._connected     = True

    @classproperty
    def profile_name(cls: object) -> str:
        return cls._profile_name
    
    @classproperty
    def region_name(cls: object) -> str:
        return cls._region_name

    @classproperty
    def aws_session(cls: object) -> object:
        return cls._aws_session
    
    @classproperty
    def ec2_resource(cls: object) -> object:
        return cls._ec2_resource
    
    @classproperty
    def ec2_client(cls: object) -> object:
        return cls._ec2_client

