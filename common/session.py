import boto3
from common.utils import classproperty

class Session:
    _aws_session    = None
    _ec2_resource   = None
    _ec2_client     = None
    _ecr_client     = None
    _ecs_client     = None
    _elbv2_client   = None

    def connect(profile_name: str, region_name: str):
        if Session._aws_session: return
        Session._profile_name   = profile_name
        Session._region_name    = region_name

    @classproperty
    def profile_name(cls: object) -> str:
        return cls._profile_name
    
    @classproperty
    def region_name(cls: object) -> str:
        return cls._region_name

    @classproperty
    def aws_session(cls: object) -> object:
        if cls._aws_session == None:
            cls._aws_session    = boto3.session.Session(
                profile_name    = cls._profile_name, 
                region_name     = cls._region_name
            )
        return cls._aws_session
    
    @classproperty
    def ec2_resource(cls: object) -> object:
        if cls._ec2_resource == None:
            cls._ec2_resource   = cls.aws_session.resource('ec2')
        return cls._ec2_resource
    
    @classproperty
    def ec2_client(cls: object) -> object:
        if cls._ec2_client == None:
            cls._ec2_client     = cls.aws_session.client('ec2')
        return cls._ec2_client

    @classproperty
    def ecr_client(cls: object) -> object:
        if cls._ecr_client == None:
            cls._ecr_client     = cls.aws_session.client('ecr')
        return cls._ecr_client

    @classproperty
    def ecs_client(cls: object) -> object:
        if cls._ecs_client == None:
            cls._ecs_client     = cls.aws_session.client('ecs')
        return cls._ecs_client

    @classproperty
    def elbv2_client(cls: object) -> object:
        if cls._elbv2_client == None:
            cls._elbv2_client     = cls.aws_session.client('elbv2')
        return cls._elbv2_client
