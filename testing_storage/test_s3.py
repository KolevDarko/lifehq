
import boto3

# Create an S3 client
s3 = boto3.client('s3')

# Call S3 to list current buckets
def list_buckets():
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    print("Bucket List: %s" % buckets)


def create_bucket():
    print("creating bucket")
    result = s3.create_bucket(Bucket='lifehq-bucket-1', CreateBucketConfiguration={
        'LocationConstraint': 'us-west-1'
    },)
    print(result)

def upload_object():
    print("creating object")
    result = s3.upload_file("evening-out.html", 'lifehq-bucket-1', 'evening-template.html')
    print(result)

import botocore

def download_object():
    BUCKET_NAME = 'lifehq-bucket-1' # replace with your bucket name
    KEY = 'evening-template.html' # replace with your object key
    s3_resource = boto3.resource('s3')
    try:
        print("getting object")
        downloaded = s3_resource.Bucket(BUCKET_NAME).download_file(KEY, KEY)
        print(downloaded)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

def list_objects():
    BUCKET_NAME = 'lifehq-bucket-1'
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(BUCKET_NAME)
    for object in my_bucket.objects.all():
        object_key = object.key
        print("Got object: " + object_key)



