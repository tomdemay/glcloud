import boto3

class Session:
    def __init__(self: object, profile_name: str, region_name: str):
        self._profile_name   = profile_name
        self._region_name    = region_name
        self._session        = boto3.session.Session(profile_name=profile_name, region_name=region_name)
        self._ec2_resource   = self.session.resource('ec2')
        self._ec2_client     = self.session.client('ec2')

    @property
    def session(self: object) -> object:
        return self._session
    
    @session.setter
    def session(self: object, session: object):
        self._session = session
    
    @property
    def ec2_resource(self: object) -> object:
        return self._ec2_resource
    
    @property
    def ec2_client(self: object) -> object:
        return self._ec2_client
    
    @property
    def profile_name(self: object) -> str:
        return self._profile_name
    
    @property
    def region_name(self: object) -> str:
        return self._region_name


