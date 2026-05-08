import time
import datetime
from pandas import read_sql_query as qry


def get_live_global(
    con_write,
    con_read,
    event_date,
    start_time,
    end_time,
    account_name='DOTCOM_ACCOUNT',
    filter_id='0',
    verbose=False,
):
    if con_read is None:
        con_read = con_write

    event_start = event_date + " " + start_time
    event_end   = event_date + " " + end_time
    e_timestamp = time.mktime(
        (datetime.datetime.strptime(event_start, "%Y-%m-%d %H:%M:%S") +
         datetime.timedelta(minutes=1)).timetuple()
    )
    event_start = datetime.datetime.fromtimestamp(int(e_timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    command = """select sum(max_value) as max_global_plays_dotcom
    from dwh_read_write.conviva_realtime
    where account_name='""" + account_name + """'
    and filter_id='""" + filter_id + """'
    and min_time_est> \'""" + event_start + """\' and min_time_est<\'""" + event_end + """\';"""

    if verbose:
        print("Fetching \n\n" + command + "\n\n")

    data = qry(command, con_read)
    live_global = data.loc[0][0]
    return live_global


def get_live_us(
    con_write,
    con_read,
    event_date,
    start_time,
    end_time,
    account_name='DOTCOM_ACCOUNT',
    filter_id='0',
    verbose=False,
):
    if con_read is None:
        con_read = con_write

    event_start = event_date + " " + start_time
    event_end   = event_date + " " + end_time
    e_timestamp = time.mktime(
        (datetime.datetime.strptime(event_start, "%Y-%m-%d %H:%M:%S") +
         datetime.timedelta(minutes=1)).timetuple()
    )
    event_start = datetime.datetime.fromtimestamp(int(e_timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    command = """select sum(max_value) as max_global_plays_dotcom
    from dwh_read_write.conviva_realtime
    where account_name='""" + account_name + """'
    and filter_id='""" + filter_id + """'
    and min_time_est> \'""" + event_start + """\' and min_time_est<\'""" + event_end + """\';"""

    if verbose:
        print("Fetching \n\n" + command + "\n\n")

    data = qry(command, con_read)
    live_us = data.loc[0][0]
    return live_us


def to_redshift(
    con,
    table,
    event_name,
    event_date,
    brand,
    dotcom_plays,
    dotcom_plays_us,
):
    con.execute(f"""
        UPDATE busgrp.{table}
        SET dotcom_plays={dotcom_plays},
          dotcom_plays_us={dotcom_plays_us}
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand = '{brand}'
    """)
