#!/bin/bash

# Delete HTTP API Gateway
apiId=$(aws apigatewayv2 get-apis --query "Items[?starts_with(Name, 'gl-pdf-search')].ApiId" --output text)
aws apigatewayv2 delete-api --api-id $apiId

# Empty S3 buckets
BUCKETS=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, 'gl-pdf-search')].Name" --output text)
for BUCKET in $BUCKETS; do
    aws s3 rm s3://$BUCKET --recursive
done

# Delete CloudFormation stacks
STACKS=$(aws cloudformation list-stacks --query "StackSummaries[?starts_with(StackName, 'gl-pdf-search') && StackStatus != 'DELETE_COMPLETE'].StackName" --output text)
for STACK in $STACKS; do
    aws cloudformation delete-stack --stack-name $STACK
done

# Delete CodePipelines
PIPELINES=$(aws codepipeline list-pipelines --query "pipelines[?starts_with(name, 'gl-pdf-search')].name" --output text)
for PIPELINE in $PIPELINES; do
    aws codepipeline delete-pipeline --name $PIPELINE
done

# Delete CodeBuilds
PROJECTS=$(aws codebuild list-projects --query "projects[?starts_with(@, 'gl-pdf-search')]" --output text)
for PROJECT in $PROJECTS; do
    aws codebuild delete-project --name $PROJECT
done

# Delete CodeCommit repositories
REPOSITORIES=$(aws codecommit list-repositories --query "repositories[?starts_with(repositoryName, 'gl-pdf-search')].repositoryName" --output text)
for REPOSITORY in $REPOSITORIES; do
    aws codecommit delete-repository --repository-name $REPOSITORY
done

# Delete Lambda layers
LAYERS=$(aws lambda list-layers --query "Layers[?starts_with(LayerName, 'pdf-search')].LayerName" --output text)
for LAYER in $LAYERS; do
    VERSIONS=$(aws lambda list-layer-versions --layer-name $LAYER --query "LayerVersions[].Version" --output text)
    for VERSION in $VERSIONS; do
        aws lambda delete-layer-version --layer-name $LAYER --version-number $VERSION
    done
done

# Force delete S3 buckets
BUCKETS=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, 'gl-pdf-search')].Name" --output text)
for BUCKET in $BUCKETS; do
    aws s3 rb s3://$BUCKET --force
done

# Delete OpenSearch Service domain
aws opensearch delete-domain --domain-name pdf-search

# Stop bastion instance
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=user-mgmt-portal-bastion" --query "Reservations[].Instances[].InstanceId" --output text)
aws ec2 stop-instances --instance-ids $INSTANCE_ID


