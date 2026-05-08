"""Utility for transferring data from CSV to S3"""
import boto3

def to_s3(localfile, s3bucket, s3keypath):
    s3filename = localfile.split('/')[-1]
    s3r = boto3.resource('s3')
    s3r.meta.client.upload_file(
        localfile, 
        Bucket = s3bucket, 
        Key = s3keypath + s3filename,
        ExtraArgs={'ServerSideEncryption': 'AES256'})