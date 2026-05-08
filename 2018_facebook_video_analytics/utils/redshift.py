"""Utility functions for connecting to and loading data into Redshift."""

from sqlalchemy import create_engine

def connect(user, password, host, db, port='5439'):
    """
    Written by Kevin Urban
    """
    conStr='postgresql://'+user+':'+password+'@'+host+':'+port+'/'+db
    con = create_engine(conStr)
    return con

def update(scrapes, con, schema, table, chunksize=150, not_a_test=False):
    if not_a_test:
        tbl = table
    else:
        tbl = f'{table}_test'
    print(f"Updating {schema}.{tbl} in Redshift")
    scrapes.to_sql(
        tbl, con, schema=schema, index=False, if_exists='append', chunksize=chunksize)
