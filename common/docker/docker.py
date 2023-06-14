import docker, logging, base64, json
from docker.errors import ImageNotFound
from common.ecr.repository import Repository
from common.session import Session
from docker.models.images import Image

class DockerImage:
    def __init__(self: object, image: Image) -> None:
        self._image = image

    def tag(self: object, repository: Repository, tag: str = "latest") -> bool:
        logging.info(f"Tagging image  '{self._image.tags}' ({self._image.id}) in repository '{repository.uri}' with tag '{tag}'")
        tag_response = self._image.tag(repository=repository.uri, tag=tag)
        logging.info(f"Tagged image  '{self._image.tags}' ({self._image.id}) in repository '{repository.uri}' with tag '{tag}'")
        return tag_response

    @property
    def tags(self: object) -> list[str]: 
        return self._image.tags
    

class DockerImages:
    @staticmethod
    def build(tag: str, path: str = ".", rm: bool = True, nocache: bool = False) -> DockerImage:
        logging.info(f"Building docker file '{tag}' (this might take a few minutes)...")
        image, build_logs = DockerClient.getClient().images.build(path=path, tag=tag, rm=rm, nocache=nocache)
        logging.info(f"Built docker file '{tag}': id = ${image.id}, tags = ${image.tags}")
        logging.debug("Docker Build returned:\n" + json.dumps(list(build_logs), separators=('\n', ':')))
        return DockerImage(image)

    @staticmethod
    def push(repository: Repository, tag: str = "latest") -> bool:
        retVal = False
        try:
            logging.info(f"Pushing image repository '{repository.uri}' with tag '{tag}' (this might take a few minutes)...")
            push_response = DockerClient.getClient().images.push(repository=repository.uri, tag=tag).replace('\r', '')
            logging.debug(f"Docker Push returned:\n{push_response}")
            error_details = next((json.loads(line) for line in push_response.split('\n') if line and 'errorDetail' in line), None)
            if error_details: raise Exception(error_details['errorDetail']['message'])
            logging.info(f"Pushed image repository '{repository.uri}' with tag '{tag}'")
            retVal = True
        except Exception as e:
            logging.error(f"Pushing image to repository failed: {str(e)}")

        return retVal

    @staticmethod
    def remove(image: str, force: bool = False, noprune: bool = False) -> bool:
        retVal = False
        try: 
            logging.info(f"Deleting image '{image}'")
            DockerClient.getClient().images.remove(image=image, force=force, noprune=noprune)
            retVal = True
            logging.info(f"Deleted image '{image}'")
        except ImageNotFound:
            logging.info(f"Unable to delete image '{image}'. Docker image not found.")
        return retVal

class DockerClient:
    _dockerClient = None

    @staticmethod
    def getClient() -> docker.DockerClient:
        if (DockerClient._dockerClient == None):
            logging.debug("Getting docker client configured from Environment variables")
            DockerClient._dockerClient = docker.from_env()
            logging.debug("Got docker client configured from Environment variables")
        return DockerClient._dockerClient

    @staticmethod
    def write_dockerfile(dockerFileText: str) -> None:
        logging.info("Creating 'Dockerfile' in the current directory")
        logging.debug(f"Writing out the following text to Dockerfile:\n{dockerFileText}")
        trimmedDockerFileText = '\n'.join([line.strip() for line in dockerFileText.split("\n")]).lstrip('\n')
        with open("Dockerfile", "w") as file: file.write(trimmedDockerFileText)
        logging.debug(f"Wrote out the following text to Dockerfile:\n{trimmedDockerFileText}")

    @staticmethod
    def login() -> None:
        logging.info(f"Logging Docker into ECR")
        logging.debug(f"Retrieving AWS ECR Authorization token")
        auth = Session.ecr_client.get_authorization_token()
        registry_credentials = auth['authorizationData'][0]
        token                = registry_credentials['authorizationToken']
        username, password   = base64.b64decode(token).decode('utf-8').split(":")
        repository_url       = registry_credentials['proxyEndpoint']
        expiration           = registry_credentials['expiresAt']
        logging.info(f"Retrieved AWS ECR Authorization token. Expiration '{expiration.isoformat()}'")
        logging.debug(f"Calling docker client login for '{repository_url}'")
        login_response = DockerClient.getClient().login(username=username, password=password, registry=repository_url)
        if login_response['Status'] != 'Login Succeeded': raise Exception(f"Docker login attempt failed: {login_response['Status']}")
        logging.info(f"Logged Docker into ECR '{repository_url}' successfully: '{login_response}'")
 