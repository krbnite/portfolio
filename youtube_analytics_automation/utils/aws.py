"""Utility functions for connecting to and loading data into Redshift."""

import boto3
from sqlalchemy import create_engine

def connect_to_redshift(user, password, host, db, port='5439'):
    """
    Written by Kevin Urban
    """
    conStr='postgresql://'+user+':'+password+'@'+host+':'+port+'/'+db
    con = create_engine(conStr)
    return con


def s3_to_redshift(
    con, iam_role_arn, s3_filename, s3_bucket, s3_keypath, rs_schema, rs_tablename
):
    """
    Written by Kevin Urban
    """
    con.execute("""
        BEGIN;
        COPY """+ rs_schema + "." + rs_tablename +"""
        FROM 's3://"""+s3_bucket+'/' + s3_keypath + s3_filename+"""'
        IAM_ROLE '""" + iam_role_arn + """'
        CSV IGNOREHEADER 1;
        COMMIT;
    """)

def csv_to_s3(localfile, s3bucket, s3keypath):
    s3filename = localfile.split('/')[-1]
    s3r = boto3.resource('s3')
    s3r.meta.client.upload_file(
        localfile, 
        Bucket = s3bucket, 
        Key = s3keypath + s3filename,
        ExtraArgs={'ServerSideEncryption': 'AES256'})


def update_redshift(scrapes, con, schema, table, chunksize=150, not_a_test=False):
    if not_a_test: 
        tbl = table
    else:          
        tbl = f'{table}_test'
    print(f"Updating busgrp.{tbl} in Redshift")
    scrapes.to_sql(
        tbl, con, schema=schema, index=False, if_exists='append', chunksize=chunksize)