print("Loading...")
import boto3, docker, ipaddress, sys, logging, random, pyperclip, logging.config, json, os, base64
from docker.models.images import Image
from botocore.exceptions import ClientError
from docker.errors import APIError

if os.path.exists('logging.json'):
    with open('logging.json', "rt") as f:
        config = json.load(f)
    logging.config.dictConfig(config)

repository_name         = 'devops-assessment'
mysql_root_password     = 'glpwd'
mysql_database          = 'devops_db'
ec2_client              = boto3.client('ec2')
ec2_resource            = boto3.resource('ec2')
ecr_client              = boto3.client('ecr')
cloudformation_client   = boto3.client('cloudformation')
registry_id             = ecr_client.describe_registry()['registryId']
dockerClient            = docker.from_env()

def getFileContents(file_path: str, expand: bool = False, base64encode: bool = False, **kwargs: dict) -> str:
    with open(file_path) as f: 
        file_text = f.read()
        if expand: 
            file_text = file_text.format(**{**locals(), **globals(), **kwargs})
        if base64encode:
            file_text = base64.b64encode(file_text.encode('utf-8')).decode('utf-8') 
        return file_text

def getSetupProps() -> tuple[str,str,str,str]:
    logging.info("Getting the default VPC ID, a private subnet CIDR block and a private ip address")
    vpc         = list(ec2_resource.vpcs.filter(Filters=[{'Name': 'is-default', 'Values': [ 'true' ]}]))[0]
    vpc_id      = vpc.id
    subnets     = list(vpc.subnets.filter(Filters = [{'Name': 'default-for-az', 'Values': [ 'true' ]}]))
    subnet_ids  = ",".join([subnet.id for subnet in subnets])
    subnet      = random.choice(subnets)
    subnet_id   = subnet.id
    ip_address  = str(random.choice(list(ipaddress.ip_network(subnet.cidr_block))))
    logging.info(f"Private IP address: {ip_address}, Subnet Id: {subnet_id}, VPC Id: {vpc_id}, Subnet Ids: [{subnet_ids}]")
    return vpc_id, subnet_ids, subnet_id, ip_address

def createStack(stack_name: str, file_name: str, wait: bool = True, parameters: list[dict] = None) -> dict:
    stack    = None
    stack_id = None
    try:
        logging.info(f"Getting Cloudformation stack '{stack_name}' information")
        stack = cloudformation_client.describe_stacks(StackName=stack_name)['Stacks'][0]
        if not stack: raise Exception(f"Cloudformation stack '{stack_name}' does not exist")
        logging.info(f"Cloudformation stack '{stack_name}' already exists")
    except Exception as e:
        logging.info(f"Cloudformation stack '{stack_name}' does not exist: {str(e)}")
        logging.info(f"Creating Cloudformation stack '{stack_name}'")
        template_body = getFileContents(f"./projects/devops/assessment/cloudformation-templates/{file_name}")
        pyperclip.copy(template_body)
        logging.info(f"Creating stack '{stack_name}'")
        logging.debug(f"Stack Template:\n{template_body}")
        stack_id = cloudformation_client.create_stack(
            StackName    = stack_name,
            TemplateBody = template_body,
            Parameters   = parameters if parameters else []
        )
        logging.info(f"CloudFormation stack '{stack_name}({stack_id})' creation initiated.")
        if wait:
            logging.info(f"Waiting for CloudFormation stack '{stack_name}({stack_id})' to complete")
            waiter = cloudformation_client.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)
            logging.info(f"CloudFormation stack '{stack_name}({stack_id})' complete")
        stack = cloudformation_client.describe_stacks(StackName=stack_name)['Stacks'][0]
    stack_id = stack['StackId']
    logging.info(f"CloudFormation stack '{stack_name}({stack_id})' status {stack['StackStatus']}")
    stack_outputs = {output['OutputKey']: output['OutputValue'] for output in stack['Outputs']} if 'Outputs' in stack else []
    logging.debug(f"CloudFormation stack outputs: {str(stack_outputs) if len(stack_outputs) else None}")
    return stack_outputs

def createMySQLStack(vpc_id: str, subnet_id: str, private_ip_address: str) -> tuple[str, str, str, str]:
    encoded_bootstrap_script_text = getFileContents(f"./projects/devops/assessment/bootstrap-scripts/mysql-bootstrap-template.sh", True, True, **locals()) 
    stack_outputs = createStack(
        stack_name  = "devops-assessment-mysql-ecr",
        file_name   = "cloudformation-mysql-ecr.yaml", 
        wait        = True,
        parameters  = [
            { 'ParameterKey': 'VpcId',            'ParameterValue': vpc_id                        },
            { 'ParameterKey': 'SubnetId',         'ParameterValue': subnet_id                     },
            { 'ParameterKey': 'PrivateIpAddress', 'ParameterValue': private_ip_address            }, 
            { 'ParameterKey': 'EncodedBootstrap', 'ParameterValue': encoded_bootstrap_script_text }
        ]
    )
    instance_id         = stack_outputs['devopsAssessmentMySQLInstance']
    public_ip_address   = stack_outputs['devopsAssessmentMySQLInstancePublicIp']
    repository_arn      = stack_outputs['devopsAssessmentRepositoryArn']
    repository_uri      = stack_outputs['devopsAssessmentRepositoryUri']
    return instance_id, public_ip_address, repository_arn, repository_uri

def createDockerFile(private_ip_address: str) -> None:
    # syntax highlighting might suggest private_ip_address is not being used.
    #   it is returned from **locals() and passed to getFileContents
    docker_file_text = getFileContents("./projects/devops/assessment/bootstrap-scripts/docker-file-template.sh", True, False, **locals()) 
    logging.info("Creating 'Dockerfile' in the current directory")
    logging.debug(f"Writing out the following text to Dockerfile:\n{docker_file_text}")
    with open("Dockerfile", "w") as file: file.write(docker_file_text)

def createDockerImage(private_ip_address: str) -> Image:
    logging.info(f"Checking to see if a docker image '{repository_name}' was already created for private_ip_address '{private_ip_address}'")
    image = None
    try:
        image = dockerClient.images.get(name=repository_name)
        if image.labels.get('MYSQL_IP_ADDRESS') == private_ip_address: 
            logging.info(f"Docker image '{repository_name}' has already been created for private_ip_address '{private_ip_address}")
            return image
    except:
        pass

    createDockerFile(private_ip_address=private_ip_address)

    logging.info(f"Building docker file '{repository_name}' (this might take a few minutes)...")
    image, build_logs = dockerClient.images.build(path=".", tag=repository_name, rm=True, nocache=False)
    logging.info(f"Built docker file '{repository_name}': id = {image.id}, tags = {image.tags}")
    logging.debug("Docker Build returned:\n" + json.dumps(list(build_logs), separators=('\n', ':')))

    logging.info(f"Deleting image 'php:7.4-apache'")
    dockerClient.images.remove(image='php:7.4-apache', force=False, noprune=False)
    logging.info(f"Deleted image 'php:7.4-apache'")

    return image

def tagDockerImage(image: Image, repository_uri: str) -> Image:
    logging.info(f"Tagging image '{image.tags}' ({image.id}) in repository '{repository_uri}' with tag 'latest'")

    if f"{repository_uri}:latest" in image.tags: 
        logging.info(f"Image '{image.id}' is already tagged")
        return image

    tag_response = image.tag(repository=repository_uri, tag="latest")
    logging.info(f"Tagged image '{image.tags}' ({image.id}) in repository '{repository_uri}' with tag 'latest'. Response '{tag_response}'")
    return image
    
def pushDockerImage(repository_uri: str, private_ip_address: str, auth_config: dict = {}) -> None:
    try:
        logging.info(f"Checking to see if image with private_ip_address '{private_ip_address}' was already pushed to repository '{repository_uri}'")
        image = dockerClient.images.pull(repository=repository_uri, auth_config=auth_config)
        if image.labels.get('MYSQL_IP_ADDRESS') == private_ip_address: 
            logging.info(f"Image with private_ip_address '{private_ip_address}' has already been pushed to repository '{repository_uri}'")
            return
    except Exception as e:
        logging.info(f"Attempting to pull image from '{repository_uri}' threw an exception: {str(e)}")

    logging.info(f"Pushing image repository '{repository_uri}' with tag 'latest' (this might take a few minutes)...")
    if len(auth_config): 
        push_response = dockerClient.images.push(repository=repository_uri, tag='latest', auth_config=auth_config, decode=True).replace('\r', '')
    else:
        push_response = dockerClient.images.push(repository=repository_uri, tag='latest').replace('\r', '')

    logging.debug(f"Docker Push returned:\n{push_response}")
    error_details = next((json.loads(line) for line in push_response.split('\n') if line and 'errorDetail' in line), None)
    if error_details: raise Exception(error_details['errorDetail']['message'])
    logging.info(f"Pushed image repository '{repository_uri}' with tag 'latest'")

def dockerLoginToECR() -> dict:
    logging.info(f"Logging Docker into ECR")
    logging.debug(f"Retrieving AWS ECR Authorization token")
    auth                 = ecr_client.get_authorization_token()
    registry_credentials = auth['authorizationData'][0]
    token                = registry_credentials['authorizationToken']
    username, password   = base64.b64decode(token).decode('utf-8').split(":")
    repository_url       = registry_credentials['proxyEndpoint']
    expiration           = registry_credentials['expiresAt']
    logging.info(f"Retrieved AWS ECR Authorization token. Expiration '{expiration.isoformat()}'")
    logging.debug(f"Calling docker client login for '{repository_url}'")
    login_response = dockerClient.login(username=username, password=password, registry=repository_url)
    if login_response['Status'] != 'Login Succeeded': raise Exception(f"Docker login attempt failed: {login_response['Status']}")
    logging.info(f"Logged Docker into ECR '{repository_url}' successfully: '{login_response}'")
    return {
        'username': username, 
        'password': password, 
        'registry': repository_url
    }

def createAndPushDockerImage(repository_uri: str, private_ip_address: str) -> Image:
    image = createDockerImage(private_ip_address=private_ip_address)
    image = tagDockerImage(image=image, repository_uri=repository_uri)

    try:
        pushDockerImage(repository_uri=repository_uri, private_ip_address=private_ip_address)
    except Exception as e:
        logging.error(f"Pushing image to repository failed: {str(e)}")
        auth_config = dockerLoginToECR()
        pushDockerImage(repository_uri=repository_uri, private_ip_address=private_ip_address, auth_config=auth_config)
    return image

def createClusterAndTaskStack() -> None:
    createStack(
        stack_name  = "devops-assessment-cluster-task", 
        file_name   = "cloudformation-cluster-task.yaml", 
        wait        = True, 
    )

def createServiceStack(vpc_id: str, subnet_ids: str) -> str:
    stack_outputs       = createStack(
        stack_name      = "devops-assessment-service-alb", 
        file_name       = "cloudformation-service-alb.yaml", 
        wait            = True, 
        parameters      = [
            { 'ParameterKey': 'VpcId',     'ParameterValue': vpc_id     },
            { 'ParameterKey': 'SubnetIds', 'ParameterValue': subnet_ids }
        ]
    )
    return stack_outputs['LoadBalancerDNSName']

def setup():
    logging.info("Setting up...")
    vpc_id, subnet_ids, subnet_id, private_ip_address = getSetupProps()
    instance_id, public_ip_address, repository_arn, repository_uri = \
        createMySQLStack(vpc_id=vpc_id, subnet_id=subnet_id, private_ip_address=private_ip_address)
    pyperclip.copy(public_ip_address)
    logging.info(f'''

        Vpc Id:              {vpc_id}
        Subnet Ids:          {subnet_ids}
        Subnet Id:           {subnet_id}
        Public IP Address:   {public_ip_address}
        Private IP Address:  {private_ip_address}
        Instance ID:         {instance_id}
        Repository Name:     {repository_name}
        Repository ARN:      {repository_arn}
        Repository URI:      {repository_uri}
        The Public IP address has been copied to your clipboard. 
        
    ''')    

    createAndPushDockerImage(repository_uri=repository_uri, private_ip_address=private_ip_address)
    createClusterAndTaskStack()
    alb_dns_name = createServiceStack(vpc_id=vpc_id, subnet_ids=subnet_ids)
    pyperclip.copy(alb_dns_name)
    logging.info(f'''

        Load Balancer DNS Name: {alb_dns_name}
        The DNS Name has been copied to your clipboard. 
        
    ''')    

    logging.info(f"Waiting for instance to finish starting up")
    ec2_client.get_waiter("instance_status_ok").wait(InstanceIds=[instance_id])

def deleteStack(stack_name: str, wait: bool) -> None:
    logging.info(f"Deleting CloudFormation stack '{stack_name}'")
    cloudformation_client.delete_stack(StackName=stack_name)
    if wait:
        logging.info(f"Waiting for CloudFormation stack '{stack_name}' to delete")
        waiter = cloudformation_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)
        logging.info(f"Deleted CloudFormation stack '{stack_name}'")

def deleteRepositoryImages() -> None:
    logging.info(f"Deleting all images on repository '{repository_name}'")
    try:
        logging.debug("Get a list of all images in the repository")
        response = ecr_client.list_images(repositoryName=repository_name)
        imageIds = response['imageIds']
        if len(imageIds):
            logging.debug("Batch deleting all images in the repository")
            ecr_client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=imageIds
            )
            logging.info(f"Deleted all images on repository '{repository_name}'")
    except ClientError as e:
        logging.error(f"Exception thrown attempting to delete repository images: {str(e)}")

def deleteLocalImages() -> None:
    logging.info("Getting list of all local docker images")
    for image in dockerClient.images.list():
        try:
            logging.info(f"Deleting local docker image {image.id}")
            dockerClient.images.remove(image.id, force=True)
            logging.info(f"Deleted local docker image {image.id}")
        except APIError as e:
            logging.error(f"Exception thrown attempting to delete local images: {str(e)}")

def cleanup():
    deleteLocalImages()
    deleteStack(stack_name="devops-assessment-service-alb",     wait=True )
    deleteStack(stack_name="devops-assessment-cluster-task",    wait=True )
    deleteRepositoryImages()
    deleteStack(stack_name="devops-assessment-mysql-ecr",       wait=True )

def main():
    if len(sys.argv) == 1:
        setup()
    elif len(sys.argv) == 2 and sys.argv[1] == '-c':
        cleanup()
    else:
        logging.error("Invalid command-line arguments.")

if __name__ == '__main__':
    main()

