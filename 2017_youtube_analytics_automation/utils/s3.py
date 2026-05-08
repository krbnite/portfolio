"""Utility for transferring data from S3 to Redshift"""

def to_redshift(
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