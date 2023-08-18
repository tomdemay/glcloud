# The Problem

I am expirimenting with AWS RDS and AWS ElastiCache

I have setup a AWS RDS MySQL Instance and the AWS ElastiCache following the steps in this video

https://olympus.mygreatlearning.com/courses/89455/pages/module-2-rds-with-elasticache-1hr30mins?module_item_id=4093895

My python script is in rds_advanced.py

This script works from within the AWS VPC (output-from-ec2-instance.out)
But I cannot get the same script to work from my local desktop computer, outside of AWS (output-from-local-desktop.out)

I checked everything I can think of and can't see any cause for this.

I initially had a problem with AWS RDS because I didn't enable "Allow Public Access" initially. Once I changed that it worked. But I don't see any such setting on AWS ElastiCache.

Screen shots attached.

I would like to understand this. I can connect to the AWS RDS, but not to AWS ElastiCache.



