import logging
from enum import Enum
from botocore.exceptions import ClientError
from common.session import Session
from common.ecr.repository import Repository

class ImageTagMutability(Enum):
    MUTABLE = 'MUTABLE'
    IMMUTABLE = 'IMMUTABLE'

class Registry:
    def __init__(self: object, registryId: str):
        self._registry_id = registryId

    @property
    def id(self: object) -> str:
        return self._registry_id

    @staticmethod
    def findRegistry() -> object:
        registryId = None
        try:
            registryId = Session.ecr_client.describe_registry()['registryId']
            logging.info(f"Found ECR Registry '{registryId}'")
        except (IndexError, ClientError):
            logging.info(f"ECR Registry not found")
        return Registry(registryId) if registryId else None
        

    def findRepository(self: object, name: str) -> Repository: 
        ecr_arn = None
        ecr_uri = None
        ecr_name = None
        try:
            repositories = Session.ecr_client.describe_repositories(
                registryId = self._registry_id, 
                repositoryNames = [ name ]
            )['repositories']

            if len(repositories) == 0: raise IndexError(f"Unable to find ECR repository '{name}'")
            # intentionally not caught
            if len(repositories) != 1: raise RuntimeError(f"Unexpected results. Expected 1 ECR repository but got {len(repositories)}")
            repository = repositories[0]
            ecr_arn = repository['repositoryArn']
            ecr_uri = repository['repositoryUri']
            ecr_name = repository['repositoryName']
            logging.info(f"Found ECR Repository '{ecr_name}': {ecr_uri}")
        except (IndexError,ClientError):
            logging.info(f"ECR Repository '{name}' not found")
        return Repository(registry_id=self._registry_id, name=ecr_name, arn=ecr_arn, uri=ecr_uri) if ecr_name else None

    def getRepository(self: object, name: str, imageTagMutability: ImageTagMutability = ImageTagMutability.MUTABLE, scanOnPush: str = True) -> Repository:
        repository = self.findRepository(name)
        if repository: return repository

        ecr_arn = None
        ecr_uri = None
        ecr_name = None
        logging.info(f"Creating ECR Registry '{name}'")
        repository = Session.ecr_client.create_repository(
            registryId = self._registry_id,
            repositoryName = name, 
            imageTagMutability=imageTagMutability.value, 
            imageScanningConfiguration= {
                'scanOnPush': scanOnPush
            }, 
            encryptionConfiguration= {
                'encryptionType': 'KMS'
            }
        )['repository']
        ecr_arn = repository['repositoryArn']
        ecr_uri = repository['repositoryUri']
        ecr_name = repository['repositoryName']
        logging.info(f"Created ECR Repository '{name}': {ecr_uri}")
        return Repository(registry_id=self._registry_id, name=ecr_name, arn=ecr_arn, uri=ecr_uri)
