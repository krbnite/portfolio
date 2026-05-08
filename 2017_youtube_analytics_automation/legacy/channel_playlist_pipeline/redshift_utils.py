"""Utility functions for connecting to and loading data into Redshift."""

from sqlalchemy import create_engine

def connect_to_redshift(user, password, host, db, port='5439'):
    """
    Written by Kevin Urban
    """
    conStr='postgresql://'+user+':'+password+'@'+host+':'+port+'/'+db
    con = create_engine(conStr)
    return con


def s3_to_redshift(
    con, s3_filename, s3_bucket, s3_keypath, 
    rs_schema, rs_tablename, iam_role_arn,
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