# ---------------------------------------------------------------------------------------------
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

CMD ["/opt/tomcat/bin/catalina.sh", "run"]
