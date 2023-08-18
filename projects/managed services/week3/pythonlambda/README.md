The steps in the PDF are wrong. And you have to use an Ubuntu image. 

I used ubuntu on WSL and it didn't download some of the required files. 


ubuntu@ip-172-31-84-29:~$ history
    1  sudo apt update
    3  sudo apt install zip -y
    4  sudo apt install python3-pip -y
    5  sudo chown ubuntu:ubuntu -R /opt
    6  cd /opt
    7  mkdir appbase
    8  cd appbase
    9  sudo pip3 install pypdf -t python
   11  zip -r appbase.zip python
 