import boto3
from botocore.exceptions import ClientError


# Push the log to s3 daily

bucket = 'reeds-test-bucket'
s3_client = boto3.client(
            service_name='s3',
            aws_access_key_id='',
            aws_secret_access_key=''
        )
response = s3_client.upload_file('hello.log', bucket, 'hello.log')
print(response)