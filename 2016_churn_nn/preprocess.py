from scipy.stats import boxcox
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Feature set registry
# ---------------------------------------------------------------------------

FEATURE_SETS = {
    'nvl':          ['num_vol_losses'],
    'ppd':          ['pmt_pct_days_paid'],
    'ppv':          ['pct_ppv1'],
    'nif':          ['num_invol_fail'],
    'nv90d':        ['no_view_90days_flag'],
    'vod30d':       ['vod_lst_30days'],
    'nxt90d':       ['nxt_view_ep_lst_90days'],
    'exl':          ['num_vol_losses', 'pmt_pct_days_paid', 'pct_ppv1', 'num_invol_fail',
                     'vod_lst_30days', 'nxt_view_ep_lst_90days', 'no_view_90days_flag'],
    'exl4':         ['num_vol_losses', 'pmt_pct_days_paid', 'pct_ppv1', 'no_view_90days_flag'],
    'exl_no_nif':   ['num_vol_losses', 'pmt_pct_days_paid', 'pct_ppv1',
                     'vod_lst_30days', 'nxt_view_ep_lst_90days', 'no_view_90days_flag'],
    'exl_no_vod':   ['num_vol_losses', 'pmt_pct_days_paid', 'pct_ppv1', 'num_invol_fail',
                     'nxt_view_ep_lst_90days', 'no_view_90days_flag'],
    'exl_no_nxt':   ['num_vol_losses', 'pmt_pct_days_paid', 'pct_ppv1', 'num_invol_fail',
                     'vod_lst_30days', 'no_view_90days_flag'],
    'b4':           ['rumble30', 'mania30', 'slam30', 'survivor30'],
    'months':       ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                     'jul', 'aug', 'sep', 'oct', 'nov', 'dec'],
    'months11':     ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                     'jul', 'aug', 'sep', 'oct', 'nov'],
    'nxt_pos':      ['nxt_view_ep_lst_30days', 'nxt_lst_30to60days', 'nxt_lst_60to90days'],
    'vod_pos':      ['vod_lst_30days', 'vod_lst_30to60days', 'vod_lst_60to90days'],
    'rebuf306090':  ['avg_rebuf_ratio_lst_30days', 'avg_rebuf_ratio_lst_60days',
                     'avg_rebuf_ratio_lst_90days'],
    'fortnights':   [f'fortnight{i+1:02d}' for i in range(26)],
    'fortnights25': [f'fortnight{i+1:02d}' for i in range(25)],
}


def varnames(*args):
    """Return a sorted, deduplicated list of feature column names.

    Usage:
        varnames('exl4', 'vod_pos', 'nxt_pos', 'months')
    """
    output = []
    for name in args:
        output += FEATURE_SETS[name]
    return sorted(set(output))


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------

def tukey(df):
    cols = df.columns.tolist()
    summaries = [np.percentile(df[col], [0, 25, 50, 75, 100]) for col in cols]
    return cols, summaries


# ---------------------------------------------------------------------------
# Transformations
# ---------------------------------------------------------------------------

def _make_pos_def(var):
    return var - var.min() + 1


def _box_tr(var, L=None):
    return boxcox(_make_pos_def(var), L)


def _log_tr(var):
    return np.log(_make_pos_def(var))


def _rec_tr(var):
    return -1.0 / _make_pos_def(var)


def condition_data(x_train, x_valid, x_test, trans='box', threshold=5, verbose=False):
    """Apply a monotonic transformation to continuous features.

    trans: 'box' (Box-Cox), 'log', or 'rec' (reciprocal).
    threshold: minimum number of unique values required before transforming a feature.
    """
    trans = trans.lower()[:3]
    xcols = x_train.drop(['cust_guid', 'as_on_dt'], axis=1).columns

    for col in xcols:
        if x_train[col].nunique() <= threshold:
            continue
        if verbose:
            print(col)

        nudge = 1 - min(x_train[col].min(), x_valid[col].min(), x_test[col].min())

        if trans == 'log':
            for df in (x_train, x_valid, x_test):
                df.loc[:, col] = np.log(df.loc[:, col] + nudge)
        elif trans == 'rec':
            for df in (x_train, x_valid, x_test):
                df.loc[:, col] = 1.0 / (df.loc[:, col] + nudge)
        else:
            x_train.loc[:, col], L = boxcox(x_train.loc[:, col] + nudge)
            x_valid.loc[:, col]    = boxcox(x_valid.loc[:, col] + nudge, L)
            x_test.loc[:,  col]    = boxcox(x_test.loc[:,  col] + nudge, L)

    for col in xcols:
        for df in (x_train, x_valid, x_test):
            df[col] = df[col].astype('float32')

    return x_train, x_valid, x_test


# ---------------------------------------------------------------------------
# Feature scaling
# ---------------------------------------------------------------------------

def zscore(data, mean=None, std=None):
    if mean is None: mean = data.mean()
    if std  is None: std  = data.std()
    return (data - mean) / std, mean, std


def halfz(data, mean=None, std=None):
    scaled, mean, std = zscore(data, mean, std)
    return 0.5 * scaled, mean, std


def fn01(data, mn=None, mx=None):
    """Scale to [0, 1]."""
    if mn is None: mn = data.min()
    if mx is None: mx = data.max()
    return (data - mn) / (mx - mn), mn, mx


def fn11(data, mn=None, mx=None, bins=False):
    """Scale to [-1, 1]."""
    if mn is None: mn = data.min()
    if mx is None: mx = data.max()
    scaled = (2 * data - (mx + mn)) / (mx - mn)
    if bins:
        scaled = pd.cut(scaled, [-1.0, -0.7, -0.25, 0.25, 0.7, 1.0],
                        labels=[-1, -0.5, 0, 0.5, 1], include_lowest=True)
    return scaled, mn, mx


def rescale_data(x_train, x_valid, x_test, fnorm='fn11', threshold=2, bins=False, verbose=False):
    """Rescale all continuous features using training-set statistics.

    fnorm: 'fn11' ([-1,1]), 'fn01' ([0,1]), 'hal' (half-z), or 'zsc' (z-score).
    """
    fnorm_key = fnorm.lower()[:3]
    scale_fn = {'fn1': fn11, 'fn0': fn01, 'hal': halfz, 'zsc': zscore}[fnorm_key]

    xcols = x_train.drop(['cust_guid', 'as_on_dt'], axis=1).columns

    for col in xcols:
        if x_train[col].nunique() <= threshold:
            continue
        if verbose:
            print(col)
        x_train.loc[:, col], p1, p2 = scale_fn(x_train.loc[:, col], bins=bins)
        x_valid.loc[:, col]          = scale_fn(x_valid.loc[:, col], p1, p2, bins=bins)[0]
        x_test.loc[:,  col]          = scale_fn(x_test.loc[:,  col], p1, p2, bins=bins)[0]

    for col in xcols:
        for df in (x_train, x_valid, x_test):
            df[col] = df[col].astype('float32')

    return x_train, x_valid, x_test
