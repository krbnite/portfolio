# Churn Prediction Neural Network (2016–2017)

Binary classification model predicting 30-day subscriber churn for a streaming subscription service
with ~1M active customers. Inherited a logistic regression system built in SAS, replicated and
extended it to a neural network, and deployed a daily scoring pipeline that wrote churn probabilities
back to Redshift.

**Final validation AUC: 75.2%** (up from ~64% baseline)

---

## Background

The prior model was a logistic regression built by an outside analytics vendor using SAS — a
standard industry approach for churn at the time. The argument for logistic regression was
interpretability, but the feature selection pipeline (700+ variables filtered through Information
Value, variable clustering, and VIF) did not reduce the multicollinearity concern completely. With the interpretability advantage in question, the door was open to try a neural network.

The full intellectual history — how the project developed, what was tried, the key insights, and
how the architecture decisions were made — is in [HISTORY.md](HISTORY.md).

---

## Model

A feedforward neural network implemented in Keras (via `tf.contrib.keras`):

- **5 hidden layers**, 11 units each
- **GaussianNoise (σ=0.1)** after each dense layer — the primary regularizer, responsible for
  roughly half the total AUC gain over the baseline
- **BatchNormalization** on the first hidden layer only
- **ReLU** activations throughout
- **Sigmoid** output (churn probability)
- **Adam** optimizer, binary crossentropy loss

Architecture defined in [model.py](model.py).

---

## Features

22 features drawn from three groups:

| Group | Features |
|---|---|
| Core predictors | `num_vol_losses`, `pmt_pct_days_paid`, `pct_ppv1`, `no_view_90days_flag` |
| Viewership position | VOD and NXT viewing days in 0–30, 30–60, and 60–90 day windows (6 vars) |
| Big Four events | Days since Royal Rumble, WrestleMania, SummerSlam, Survivor Series (4 vars) |
| Seasonality | Monthly indicator variables: Jan–Dec (12 vars) |

Raw features are reciprocal-transformed (`-1/(x + nudge)`) then scaled to [−1, 1] before model
input. Full preprocessing logic in [preprocess.py](preprocess.py).

---

## Results

Trained on 711,604 subscribers; evaluated on a held-out validation set.

| Metric    | Training | Validation |
|-----------|----------|------------|
| ROC-AUC   | 75.9%    | 75.2%      |
| Precision | 59.8%    | 61.0%      |
| Recall    | 9.9%     | 9.9%       |
| PR-AUC    | 27.0%    | 27.1%      |
| F1        | 16.9%    | 17.1%      |

The churn rate in the training data was ~7%, so a naive classifier achieves 93% accuracy by always
predicting retention. AUC and decile gain charts were the operative evaluation metrics. Precision
of ~60% at the default threshold represents roughly 8× the random-selection rate.

---

## Production Pipeline

The model scored the full active subscriber base daily via cron and wrote results back to Redshift:

```
Redshift (features) → preprocess → model inference → Redshift (churn_prob)
```

Entry point: [pipeline.py](pipeline.py) — accepts an optional `--date` argument for backfills.

Supporting modules:

| File | Responsibility |
|---|---|
| [query.py](query.py) | Redshift connection and feature query |
| [preprocess.py](preprocess.py) | Transforms, scaling, feature set registry |
| [model.py](model.py) | Keras model architecture |
| [score.py](score.py) | Inference and score writing |

---

## Repository Layout

```
├── HISTORY.md                   # full project narrative
├── pipeline.py                  # daily scoring entry point
├── query.py                     # data access
├── preprocess.py                # feature engineering
├── model.py                     # model architecture
├── score.py                     # inference + write-back
│
├── model/                       # development notebooks
│   ├── 01_baseline_lr_rf.ipynb  # baseline LR and RF replication
│   ├── 02_nn_initial.ipynb      # first NN attempt (raw TF)
│   ├── 03_nn_tensorflow_verbose.ipynb
│   ├── 04_nn_tensorflow.ipynb
│   ├── 05_nn_tensorflow_v2.ipynb
│   ├── 06_nn_oop_refactor.ipynb
│   ├── 07_nn_keras.ipynb        # final Keras model
│   ├── history/                 # training run checkpoints
│   └── saved/                   # serialized model
│
├── evaluation/                  # post-training evaluation
│   ├── 01_model_eval.ipynb
│   ├── 02_scores_report.ipynb
│   ├── 03_decile_profiles.ipynb
│   ├── 04_gains_charts.ipynb
│   └── 05_roc_curve.ipynb
│
├── exploration/                 # feature selection work
│   ├── 01_univariate_feature_selection.ipynb
│   └── 02_variable_queries.ipynb
│
├── blogs/                       # posts written during development
└── notes/                       # meeting notes and reference material
```
