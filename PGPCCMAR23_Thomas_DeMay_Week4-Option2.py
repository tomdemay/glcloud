from common.config import Configuration
from projects.week4.option2.create_aws_resources import CreateAWSResources
from projects.week4.option2.delete_aws_resources import DeleteAWSResources

if __name__ == '__main__': 
    Configuration.setup(description='PGPCC | Project. Creating a file share & sync solution using mattermost and MySQL on AWS')
    DeleteAWSResources.run() if Configuration.args.cleanup else CreateAWSResources.run()

