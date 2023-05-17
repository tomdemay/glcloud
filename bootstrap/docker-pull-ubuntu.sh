#!/bin/bash -x
apt-get update
apt-get wget
apt-get install docker.io -y
apt-get install awscli -y
usermod -aG docker ubuntu
su ubuntu
cd ~
mkdir .aws
echo "[default]
region = us-east-1
output = json" > .aws/config
echo "[default]
aws_access_key_id = {0}
aws_secret_access_key = {1}" > .aws/credentials
exit
export REPOSITORY_URI=`aws ecr describe-repositories --query 'repositories[0].repositoryUri' | sed 's#/helloworld##g' | sed 's#"##g'`
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REPOSITORY_URI
docker run -d -p 80:8080 helloworld:latest
