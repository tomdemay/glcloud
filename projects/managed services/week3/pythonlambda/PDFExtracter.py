#******************************************************************************************
# Author - Nirmallya Mukherjee
# This lambda function will open an S3 trigger JSON, check the bucket and file details
# Use the S3 api to read the PDF file and use the PyPDF library to extract the text content
# Log the text content and metadata in cloudwatch
#
# Imp - This function will need a timeout of 2mins (depending on the PDF size) and mem of 256MB
#       Create a custom role for lambda with the following specifications
#       "lambda-multirole" with "CloudWatchFullAccess" and "AmazonS3FullAccess" policies
#
#******************************************************************************************
import boto3
import json
import os
import logging
import pypdf
from pypdf import PdfReader
from io import BytesIO
from io import StringIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info('********************** Environment and Event variables are *********************')
    logger.info(os.environ)
    logger.info(event)
    extract_content(event)

    return {
        'statusCode': 200,
        'body': json.dumps('Execution is now complete')
    }


def extract_content(event):
    try:
        #Read the target bucket from the lambda environment variable
        targetBucket = os.environ['TARGET_BUCKET']
    except:
        targetBucket = "skl-dest"
    print('Target bucket is', targetBucket)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print('The s3 bucket is', bucket, 'and the file name is', key)
    s3client = boto3.client('s3')
    response = s3client.get_object(Bucket=bucket, Key=key)
    pdffile = response["Body"]
    print('The binary pdf file type is', type(pdffile))

    reader = PdfReader(BytesIO(pdffile.read()))
    info = reader.metadata
    page = reader.pages[0]
    text = page.extract_text()
    print("Extracted text is ", text)
    print("Metadata is ", info)
    content = str(text)
    print('Content is', content)

    s3client.put_object(Bucket=targetBucket, Key=key+".txt", Body=content)

    print('All done, returning from extract content method')



