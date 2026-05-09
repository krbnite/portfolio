"""
Churn scoring pipeline — daily entry point.

Scheduled via cron:
    0 6 * * * /path/to/venv/bin/python /path/to/pipeline.py

Flow:
    1. Connect to Redshift
    2. Pull today's active-subscriber feature set
    3. Load the trained Keras model
    4. Score every subscriber
    5. Write churn probabilities back to Redshift
"""

import argparse
import logging
from datetime import date

import query as q
import score as s
from preprocess import varnames

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

MODEL_PATH = 'model/saved/2017-06-20__keras_model'
FEATURES   = varnames('exl4', 'vod_pos', 'nxt_pos', 'months')


def run(as_on_dt=None):
    as_on_dt = as_on_dt or str(date.today())
    log.info(f'Starting churn scoring run for {as_on_dt}')

    log.info('Connecting to Redshift')
    con = q.connect()

    log.info('Querying features')
    df = q.query_features(con, as_on_dt=as_on_dt)
    log.info(f'  {len(df):,} subscribers loaded')

    log.info(f'Loading model from {MODEL_PATH}')
    model = s.load_model(MODEL_PATH)

    log.info('Scoring')
    scores = s.score(model, df, features=FEATURES)
    log.info(f'  mean churn probability: {scores.mean():.4f}')

    log.info('Writing scores to Redshift')
    s.write_scores(scores, con)

    log.info('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Daily churn scoring pipeline')
    parser.add_argument('--date', default=None, help='as_on_dt (YYYY-MM-DD); defaults to today')
    args = parser.parse_args()
    run(as_on_dt=args.date)
