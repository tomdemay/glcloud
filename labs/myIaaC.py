import json
import boto3

def lambda_handler(event, context):
    ec2_client=boto3.client('ec2')
    ec2_resource=boto3.resource('ec2')
    s3_resource=boto3.resource('s3')
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        obj = s3_resource.Object(bucket, key)
        body = obj.get()['Body'].read()
        
        specs=json.loads(body)
        
        
        imageid=specs['ec2']['image-id']
        mincount=specs['ec2']['mincount']
        maxcount=specs['ec2']['maxcount']
        instancetype=specs['ec2']['instance-type']
        keyname=specs['ec2']['key-name']
        securitygroup=specs['ec2']['security-group']
        
        
        
    response = ec2_client.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    
    response = ec2_client.create_security_group(GroupName=securitygroup,
                                         Description='DESCRIPTION',
                                         VpcId=vpc_id)
    security_group_id = response['GroupId']
    print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

    data = ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    print('Ingress Successfully Set %s' % data)
    
    
    instance = ec2_resource.create_instances(
            ImageId = imageid,
            MinCount = int(mincount),
            MaxCount = int(maxcount),
            InstanceType = instancetype,
            SecurityGroupIds=[security_group_id],
            KeyName = keyname)
            
    print ('Instance created %s' % instance)
    
    

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
