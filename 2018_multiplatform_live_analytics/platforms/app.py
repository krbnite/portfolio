from pandas import read_sql_query as qry


def app_numbers_live(con, event_date, start_time, end_time):
    event_start = event_date + " " + start_time
    event_end   = event_date + " " + end_time

    con.execute("""
    drop table if exists #app_tab;
    create table #app_tab as
    select max(active_users) as active_users from
    (select active_users, time
    from busgrp.ga_real_time_second_screen_viewers
    where time between \'""" + event_start + """\' and \'""" + event_end + """\');""")

    con.execute("""insert into #app_tab(active_users)
    select max(active_users) as active_users from
    (select active_users, time
    from busgrp.ga_real_time_second_screen_viewers_snapshot
    where time between \'""" + event_start + """\' and \'""" + event_end + """\');""")

    data = qry("""select max(active_users) from #app_tab""", con)
    active_users = int(data.loc[0][0])

    return active_users


def to_redshift(
    con,
    table,
    event_name,
    event_date,
    brand,
    app_metric,
):
    con.execute(f"""
        UPDATE busgrp.{table}
        SET app_metric={app_metric}
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand = '{brand}'
    """)
