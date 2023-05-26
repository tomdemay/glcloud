#!/bin/bash -x
apt-get update
apt-get upgrade -y
apt-get wget
apt-get install docker.io -y
apt-get install awscli -y
wget https://d6opu47qoi4ee.cloudfront.net/HelloWorld.war
usermod -aG docker ubuntu
su ubuntu
cd ~
mkdir .aws
echo "[default]
region = us-east-1
output = json" > .aws/config
echo '[default]
aws_access_key_id = {0}
aws_secret_access_key = {1} > .aws/credentials
echo '# ---------------------------------------------------------------------------------------------
# A custom docker image with OpenJava 11, Tomcat 9 with default ROOT and HelloWorld applications
# The valid uri are / and /HelloWorld
# ---------------------------------------------------------------------------------------------

FROM openjdk:11
MAINTAINER Greatlearning

RUN apt update \
    && apt install -y wget \
    && mkdir /opt/tomcat/

RUN wget https://d6opu47qoi4ee.cloudfront.net/tomcat/apache-tomcat-9.0.53.tar.gz \
    && tar xvfz apache*.tar.gz \
    && mv apache-tomcat-9.0.53/* /opt/tomcat/. \
    && cd /opt/tomcat/webapps \
    && wget https://d6opu47qoi4ee.cloudfront.net/HelloWorld.war \
    && java -version

WORKDIR /opt/tomcat/webapps

EXPOSE 8080

CMD ["/opt/tomcat/bin/catalina.sh", "run"]' > Dockerfile
export REPOSITORY_URI=`aws ecr describe-repositories --repository-names 'helloworld' --query 'repositories[0].repositoryUri' | sed 's#/helloworld##g' | sed 's#"##g'`
if [[ ! -z "$REPOSITORY_URI" ]]; then
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REPOSITORY_URI
    docker build -t helloworld .
    docker tag helloworld:latest $REPOSITORY_URI/helloworld:latest
    docker push $REPOSITORY_URI/helloworld:latest
    docker run -d helloworld
fi