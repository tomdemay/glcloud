from common.config import Configuration
from projects.week4.option3.create_aws_resources import CreateAWSResources
from projects.week4.option3.delete_aws_resources import DeleteAWSResources

if __name__ == '__main__': 
    Configuration.setup(description='PGPCC | Project. Creating a file share & sync solution using ownCloud and AWS')
    DeleteAWSResources.run() if Configuration.args.cleanup else CreateAWSResources.run()

