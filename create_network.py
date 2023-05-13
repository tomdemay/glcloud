print("Loading...")

import os
from common.config import Configuration
from create_network_imports.create_aws_resources import CreateAWSResources
from create_network_imports.delete_aws_resources import DeleteAWSResources

DEFAULT_PORTS = [80,22]

if __name__ == '__main__': 
    project_description = 'Sample project to start an EC2 instance in a new VPC'
    parser = Configuration.getArgParser(project_description=project_description)
    parser.add_argument('--name', '-n', help="Project Name.", required=True, type=str)
    parser.add_argument('--ports', "-p", help="List of ports to open", default=DEFAULT_PORTS, required=False, nargs="+", type=int)
    parser.add_argument('--bootstrap-script', '-bs', help='Bootstrap script to run when instance is created.', default=None, required=False, type=str)

    args = Configuration.getCmdLineArgs(project_description=project_description)
    project_name = args.name
    if args.bootstrap_script and not os.path.exists(args.bootstrap_script):
        raise FileNotFoundError(args.bootstrap_script)

    Configuration.setup(
        project_name=project_name, 
        project_description=project_description)
    DeleteAWSResources.run(project_name) if Configuration.args.cleanup else CreateAWSResources.run(project_name)
