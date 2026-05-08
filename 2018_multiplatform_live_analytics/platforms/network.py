import time
import datetime
from pandas import read_sql_query as qry


def get_live_global(
    con_write,
    con_read,
    event_date,
    start_time,
    end_time,
    account_name='NETWORK_ACCOUNT',
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

    command = """select max(max_value) as max_global_concurrents_network
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
    account_name='NETWORK_ACCOUNT',
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

    command = """select max(max_value) as max_global_concurrents_network
    from dwh_read_write.conviva_realtime
    where account_name='""" + account_name + """'
    and filter_id='""" + filter_id + """'
    and min_time_est> \'""" + event_start + """\' and min_time_est<\'""" + event_end + """\';"""

    if verbose:
        print("Fetching \n\n" + command + "\n\n")

    data = qry(command, con_read)
    live_us = data.loc[0][0]
    return live_us


def get_live_minutes(con, content_id, verbose=False):
    """
    Returns total live minutes watched for a given content ID.
    Queries the linear stream_type within the event's live window.
    Note: adjust the table and column names to match your schema.
    """
    command = """select sum(time_spent) as live_minutes
    from busgrp.viewership_table
    where content_id = \'""" + content_id + """\' and stream_type='linear'
    and min_time between live_start and live_end;"""

    if verbose:
        print("Fetching \n\n" + command + "\n\n")

    data = qry(command, con)
    live_global = data.loc[0][0]
    return live_global


def get_live_vod_global(con, content_id, verbose=False):
    command = """select count(distinct user_id) as debut_date,
    sum(time_spent) as debut_minutes from busgrp.viewership_table
    where content_id = \'""" + content_id + """\' and min_time between to_date(first_stream,'yyyy-mm-dd') and (to_date(first_stream,'yyyy-mm-dd') + 1)||' 02:59:59';"""

    if verbose:
        print("Fetching \n\n" + command + "\n\n")

    data = qry(command, con)
    network_streams = data.loc[0][0]
    network_total_minutes_watched = round(data.loc[0][1])

    print(network_streams, network_total_minutes_watched)

    return network_streams, network_total_minutes_watched


def get_live_vod_us(con, content_id):
    command = """select count(distinct user_id) as debut_date,
    sum(time_spent) as debut_minutes from busgrp.viewership_table
    where content_id = \'""" + content_id + """\' and min_time between to_date(first_stream,'yyyy-mm-dd') and
    (to_date(first_stream,'yyyy-mm-dd') + 1)||' 02:59:59' and billing_country='United States';"""

    print("Fetching \n\n" + command + "\n\n")

    data = qry(command, con)
    network_streams_us = data.loc[0][0]
    network_total_minutes_watched_us = round(data.loc[0][1])

    print(network_streams_us, network_total_minutes_watched_us)

    return network_streams_us, network_total_minutes_watched_us


def to_redshift(
    con,
    table,
    event_name,
    event_date,
    brand,
    network_max_concurrents,
    network_max_concurrents_us,
):
    con.execute(f"""
        UPDATE busgrp.{table}
        SET network_max_concurrents={network_max_concurrents},
        network_max_concurrents_us={network_max_concurrents_us}
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand = '{brand}'
    """)
