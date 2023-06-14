import logging
from botocore.exceptions import ClientError
from common.session import Session

class Repository:
    def __init__(self: object, registry_id: str, name: str, arn: str, uri: str):
        self._registry_id = registry_id
        self._arn = arn
        self._uri = uri
        self._name = name

    @property
    def registry_id(self: object) -> str:
        return self._registry_id
    
    @property
    def name(self: object) -> str:
        return self._name
    
    @property
    def arn(self: object) -> str:
        return self._arn
    
    @property
    def uri(self: object) -> str:
        return self._uri
    
    def drop(self: object, force: bool = False) -> None:
        logging.info(f"Deleting ECR Repository '{self._name}'")
        Session.ecr_client.delete_repository(registryId = self._registry_id, repositoryName = self._name, force = force)
        logging.info(f"Deleted ECR Repository '{self._name}'")

