import numpy as np
import pandas as pd
import tensorflow as tf

from preprocess import varnames, condition_data, rescale_data
import query as q


def load_model(path):
    """Load a saved Keras model from disk."""
    return tf.contrib.keras.models.load_model(path)


def score(model, x, features=None, trans='rec', fnorm='fn11', threshold=2):
    """Generate churn probability scores for a feature DataFrame.

    Applies the same preprocessing pipeline used during training
    (reciprocal transform → [-1,1] scaling), then runs inference.

    Args:
        model:     loaded Keras model.
        x:         DataFrame of raw features (as returned by query.query_features).
        features:  list of column names to use; defaults to varnames('exl4','vod_pos','nxt_pos','months').
        trans:     monotonic transform to apply ('rec', 'log', or 'box').
        fnorm:     scaling method ('fn11', 'fn01', 'hal', or 'zsc').
        threshold: min unique values required before transforming a feature.

    Returns:
        Series of churn probabilities indexed by cust_guid.
    """
    if features is None:
        features = varnames('exl4', 'vod_pos', 'nxt_pos', 'months')

    # Preprocessing expects three splits; pass x as all three and ignore valid/test
    x_proc, _, _ = condition_data(x.copy(), x.copy(), x.copy(), trans=trans, threshold=threshold)
    x_proc, _, _ = rescale_data(x_proc, x.copy(), x.copy(), fnorm=fnorm, threshold=threshold)

    x_arr = x_proc.loc[:, features].values.astype('float32')
    probs = model.predict(x_arr)[:, 0]
    return pd.Series(probs, index=x['cust_guid'], name='churn_prob')


def write_scores(scores, con, table='<schema>.<churn_scores_table>', if_exists='append'):
    """Write a Series of churn scores back to Redshift.

    Args:
        scores:     Series with cust_guid index and churn_prob values.
        con:        SQLAlchemy engine (from query.connect()).
        table:      destination Redshift table.
        if_exists:  'append' or 'replace'.
    """
    df = scores.reset_index()
    df.columns = ['cust_guid', 'churn_prob']
    df['scored_at'] = pd.Timestamp.utcnow()
    df.to_sql(table, con, index=False, if_exists=if_exists, method='multi')
