from sqlalchemy import create_engine
from pandas import read_sql_query as qry
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np


def connect(host='<redshift-host>', db='<database>', user='<username>', password='<password>', port=5439):
    conn_str = f'postgresql://{user}:{password}@{host}:{port}/{db}'
    return create_engine(conn_str)


def query_features(con, as_on_dt=None):
    """Pull churn feature set from Redshift. Returns a DataFrame with one row
    per (customer, as_on_date) and a binary `churn` label."""

    rumble   = ['2015-01-25', '2016-01-24', '2017-01-29']
    slam     = ['2015-08-23', '2016-08-21', '2017-08-20']
    survivor = ['2015-11-22', '2016-11-20', '2017-11-19']
    mania    = ['2015-03-29', '2016-04-03', '2017-04-02']

    def _in_window(col, dates):
        clauses = [
            f"({col} BETWEEN '{d}'::date AND '{d}'::date + '1 month'::interval)"
            for d in dates
        ]
        return ' OR '.join(clauses)

    where = "WHERE current_state='Active Paid' AND latest_active_period > 29 AND current_rc_payer = 0 AND pmt1_aftr_as_on IS NOT NULL"
    if as_on_dt:
        where += f" AND as_on_dt = '{as_on_dt}'"

    sql = f"""
        SELECT
            vod_lst_30to60days - vod_lst_30days                                 AS vod_v1,
            vod_lst_60to90days - vod_lst_30to60days                             AS vod_v2,
            (vod_lst_60to90days - vod_lst_30to60days)
                - (vod_lst_30to60days - vod_lst_30days)                         AS vod_acc,
            nxt_lst_30to60days - nxt_view_ep_lst_30days                         AS nxt_v1,
            nxt_lst_60to90days - nxt_lst_30to60days                             AS nxt_v2,
            (nxt_lst_60to90days - nxt_lst_30to60days)
                - (nxt_lst_30to60days - nxt_view_ep_lst_30days)                 AS nxt_acc,
            *
        FROM (
            SELECT
                as_on_dt,
                cust_guid,
                CASE WHEN ram_country = 'us' THEN 1 ELSE -1 END                AS domestic,
                num_vol_losses,
                pmt_pct_days_paid,
                num_pmts,
                pct_ppv1,
                CASE WHEN pct_ppv1 > 0.69999 THEN 1 ELSE 0 END                AS ppv1_completer,
                num_invol_fail,
                vod_lst_30days,
                COALESCE(vod_lst_60days  - vod_lst_30days,  0)                 AS vod_lst_30to60days,
                COALESCE(vod_lst_90days  - vod_lst_60days,  0)                 AS vod_lst_60to90days,
                nxt_view_ep_lst_90days,
                nxt_view_ep_lst_30days,
                COALESCE(nxt_view_ep_lst_60days - nxt_view_ep_lst_30days, 0)   AS nxt_lst_30to60days,
                COALESCE(nxt_view_ep_lst_90days - nxt_view_ep_lst_60days, 0)   AS nxt_lst_60to90days,
                CASE WHEN no_view_30days_flag = 0 THEN -1 ELSE no_view_30days_flag END AS no_view_30days_flag,
                CASE WHEN no_view_60days_flag = 0 THEN -1 ELSE no_view_60days_flag END AS no_view_60days_flag,
                CASE WHEN no_view_90days_flag = 0 THEN -1 ELSE no_view_90days_flag END AS no_view_90days_flag,
                num_strms_vshp_all,
                vod_num_strms,
                num_nc_em_rcvd_1st_60days,
                overall_num_device_types,
                num_strms_vshp_net_orig,
                num_strms_vshp_ring,
                avg_rebuf_ratio_lst_30days,
                avg_rebuf_ratio_lst_60days,
                avg_rebuf_ratio_lst_90days,
                CASE WHEN ({_in_window('as_on_dt', rumble)})   THEN 1 ELSE -1 END AS rumble30,
                CASE WHEN ({_in_window('as_on_dt', slam)})     THEN 1 ELSE -1 END AS slam30,
                CASE WHEN ({_in_window('as_on_dt', survivor)}) THEN 1 ELSE -1 END AS survivor30,
                CASE WHEN ({_in_window('as_on_dt', mania)})    THEN 1 ELSE -1 END AS mania30,
                CASE WHEN date_part('month', as_on_dt::date) =  1 THEN 1 ELSE -1 END AS jan,
                CASE WHEN date_part('month', as_on_dt::date) =  2 THEN 1 ELSE -1 END AS feb,
                CASE WHEN date_part('month', as_on_dt::date) =  3 THEN 1 ELSE -1 END AS mar,
                CASE WHEN date_part('month', as_on_dt::date) =  4 THEN 1 ELSE -1 END AS apr,
                CASE WHEN date_part('month', as_on_dt::date) =  5 THEN 1 ELSE -1 END AS may,
                CASE WHEN date_part('month', as_on_dt::date) =  6 THEN 1 ELSE -1 END AS jun,
                CASE WHEN date_part('month', as_on_dt::date) =  7 THEN 1 ELSE -1 END AS jul,
                CASE WHEN date_part('month', as_on_dt::date) =  8 THEN 1 ELSE -1 END AS aug,
                CASE WHEN date_part('month', as_on_dt::date) =  9 THEN 1 ELSE -1 END AS sep,
                CASE WHEN date_part('month', as_on_dt::date) = 10 THEN 1 ELSE -1 END AS oct,
                CASE WHEN date_part('month', as_on_dt::date) = 11 THEN 1 ELSE -1 END AS nov,
                CASE WHEN date_part('month', as_on_dt::date) = 12 THEN 1 ELSE -1 END AS dec,
                CASE WHEN pmt1_aftr_as_on  = 0 THEN 1
                     WHEN pmt1_aftr_as_on >= 1 THEN 0
                     ELSE NULL END                                              AS churn
            FROM <schema>.<churn_table>
            {where}
        )
    """
    df = qry(sql, con)
    return df.fillna(0)


def split_train_valid_test(df, train_size=0.8, valid_frac=0.5, seed_1=42, seed_2=31):
    """Split a feature DataFrame into train / validation / test sets.
    Default split: 80% train, 10% validation, 10% test.
    Returns (x_train, y_train, x_valid, y_valid, x_test, y_test).
    """
    df = df.fillna(0)
    y = pd.DataFrame(np.array([df['churn']]).T)
    x = df.drop('churn', axis=1)

    x_train, x_vt, y_train, y_vt = train_test_split(x, y, train_size=train_size, random_state=seed_1)
    x_valid, x_test, y_valid, y_test = train_test_split(x_vt, y_vt, test_size=valid_frac, random_state=seed_2)
    return x_train, y_train, x_valid, y_valid, x_test, y_test


def save_splits(splits, prefix=''):
    names = ('x_train', 'y_train', 'x_valid', 'y_valid', 'x_test', 'y_test')
    for name, df in zip(names, splits):
        pd.DataFrame(df).to_pickle(prefix + name)


def load_splits(prefix=''):
    names = ('x_train', 'y_train', 'x_valid', 'y_valid', 'x_test', 'y_test')
    return [pd.read_pickle(prefix + name) for name in names]
