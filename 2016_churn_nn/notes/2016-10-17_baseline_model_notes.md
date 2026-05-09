---
date: 2016-10-17
source: meeting notes (self-email)
---

# Baseline Model — Meeting Notes (Oct 17, 2016)

## The Data Point Disposal Process

There are a lot of customers, and the service has over 2 years of data. For computational efficiency, the team samples 57 days only; this sampling includes both near-PPV and far-from-PPV dates (the sampling is only quasi-random, in that near-PPV dates are ensured to be present in the data set). To further reduce the data set prior to any potentially costly computational procedure, ~10% of the customer base is randomly sampled (e.g., as of now, the customer base has ~1 mil active subs, 3 mil total accounts). The data is then split 70%/30% into training and test data sets. Additional test sets are out-of-sample (same dates, but data from other 90%) and out-of-time (data from different dates).

---

## The Variable Disposal Process

The same basic variable disposal process is implemented for each model. Given an initial set of 700+ variables, the goal is to end up with 5-10 of the most important variables. This process can be viewed as a filter:

**1. The Massacre of Irrelevance: Information Value (IV) and Pearson Correlation**
- IV: 0.0–0.02 (useless), 0.02–0.1 (weak predictor), 0.1–0.3 (moderate), 0.3–0.5 (strong), >0.5 (suspiciously strong: probably too good to be true)
- Correlation: should be high with the target
- This typically takes features from ~700+ vars to ~50 vars for each classification model
- Side Note: also look at the component IVs at this stage (IV = Sum[i]{ IV[i] })
  - The sub IVs tell us whether or not the variable binning was well-chosen, whether a transformation should be applied (e.g., logarithm), whether a step function should be applied, etc.

**2. Death to Redundancy: Variable Clustering**
- In the reduced feature set, this checks for confounding/correlated features
- Correlated features are clustered and a candidate feature from each cluster is retained
- See VARCLUS section below

**3. The Fine-Tuning: Variance Inflation Factor**

---

## Model Development: Tuning the Logistic Regression

All of the baseline models are logistic regression models — though other techniques (e.g., random forests) have been used to contrast, all of which showed general agreement. By this point, we should only be working with 15–25 variables. The final feature selection step is implemented using stepwise/combinatorial linear regression, ultimately seeking out the best 6–10 variables for the logistic regression. (Currently done in SAS.)

### That's It!
Coefficients are computed, the model is tested on the test sets, and things are done for the time being. Any time new vars are considered/introduced, they are first subject to the various filtering/disposal techniques to see if they are even worth further consideration.

---

## The Models

**6-month Retention Model**
- WinBack Retention Model
- FirstOrders ("Uninterrupted Service") Retention Model

**1- and 3-Month Churn Models**
- Churn is for active subscription population only, but is split into:
  - (i) Voluntary Churn Model
  - (ii) Involuntary Churn Model
- Predictions: Which customers will likely be around in 30 days? in 90 days?
- The plan is to score this model weekly (not yet in production at time of notes)
- When training/developing the model, churn/retainment was defined like this:

| Payment Pattern | Month 1 | Month 2 | Month 3 | Label |
|---|---|---|---|---|
| Retained | 1 | 1 | 1 | Retained! |
| Grace period | 1 | 1 | 0 | {0\|1} Check 15-day grace period |
| Churned | 1 | 0 | 0 | Churned! |

**Important features** identified for predicting customer churn:

- `num_vol_losses` — how many times have they voluntarily canceled in the past?
- `tot_lin_days_new` — # days they've watched linear feed over lifetime of their account; possible interpretation: customers who often watch the linear feed *love* the universe and are generally willing to watch anything
- `tot_view_days_news` — # days customer has watched linear OR VOD over lifetime of account
  - SIDE NOTE: a similar variable for just VOD was not identified as important; if true, then `tot_view_days_new ~= tot_lin_days_new + NOISE`, which means this variable (1) has no further info than `tot_lin_days_new`; (2) the variable disposal process is not working as well as it should be (likely at the cluster-and-chuck phase)
- `num_invol_fail` — how many times have they involuntarily cancelled in the past?
- `no_view_90_days_flag` — binary: either they've watched in past 90 days or not
- `num_nc_em_rcvd_all_tm` — number of emails customer was sent about new content (ranges ~0–60); measured over lifetime of account; theoretically, if you're active, you're supposed to receive all these emails, but apparently the email provider has consistently messed this up inconsistently!

**Going Forward:**
- Do these models and variables still work?
- Will be assessing ongoing performance using the Character Stability Index (CSI) and Population Stability Index (PSI)

**Trial Conversion/Cancellation Model** — Will the free trial result in a paying customer?
- WinBack Model (very small, inconsequential population; i.e., even if we could get them all to convert, the revenue impact is near nil)

**WinBack Model** — under development

---

## Weight of Evidence (WOE) and Information Value (IV)

- Basically, WOE and IV are intimately related to logistic regression
- Both measure something about the relationship between an input/predictor variable and a binary output
- IV is widely used in credit risk modeling to assess whether or not an input/predictor var has predictive power
- For modeling, IV is used as a pre-screening filter — it is better to think of it as "variable disposal," not "variable selection"

**Estimation:**
1. If variable is continuous, define ~10 bins (decile bins work; recommended: ≥5% of data per bin, no bin with 0 bad or 0 good points, missing values binned separately)
2. For each bin, tally events/non-events and compute their percentages
3. `WOE[i] := ln( %good[i] / %bad[i] )`
4. `IV[i] := (%good[i] - %bad[i]) * WOE[i]`
5. `IV := SUM[i]{ IV[i] }`

**Ranking a variable's predictive power by IV:**
- 0.00–0.02: sucks
- 0.02–0.10: weak
- 0.10–0.30: decent
- 0.30–0.50: sweet!!!
- 0.50+: likely too good to be true (inconclusive)

**Is it in Python?** Sci-kit Learn has mutual information metrics, which is apparently a pretty close concept.

---

## Variable Clustering

**Purposes:** variable disposal, dimensionality reduction, redundancy reduction, detection and remedy of multicollinearity

> "When statisticians try to build models with a large number of variables, it becomes difficult to figure out the correct relationships between the dependent and independent variables. In fact, when redundant variables are included in some of the model building procedures, the model can degrade... [e.g., by] destabilizing the parameter estimates, increasing computation time, confounding the interpretation." — SAS PROC VARCLUS documentation

> "In high dimensional data sets, identifying irrelevant inputs is more difficult than identifying redundant inputs. A good strategy is to first reduce redundancy and then tackle irrelevancy in a lower dimension space."

Note: the existing approach does the opposite — scores relevancy of 700+ vars to trim ~650 vars, *then* clusters to further reduce.

**Similar Function to PCA:**
- "[Variable clustering] is closely related to PCA and can be used as an alternative method for eliminating redundant dimensions."
- "In a certain sense, it is more powerful than factor analysis (e.g. PCA) because it overcomes the orthogonality constraint between the factors."

**The Unsupervised Divisive Approach:**
1. All vars start in the same cluster; if eigVal[2] > threshold, split the parent cluster into two
2. Repeat on children, grandchildren, etc., until threshold is no longer violated along each branch
3. The dimensionality of the data set is estimated by the number of leaves

**Retained Variables:** One variable must be selected from each leaf cluster. Variance inflation factors (VIFs) can help choose this — specifically `VIF_ext / VIF_int`. You want to choose the variable within the leaf cluster that minimizes this ratio. Thinking in terms of VIF, ideally a variable is utterly uncorrelated with other variables outside its cluster (VIF_ext=1) and highly correlated with the variables inside its cluster (VIF_int → ∞), giving a small ratio.

---

## Variable Inflation Factor (VIF)

**Function/Purpose:** quantify the severity of multicollinearity in an OLS regression analysis.

**What exactly does it quantify?**
- How much uncertainty/variance in a variable's slope/coefficient estimate is due to the variable's non-orthogonal relationship with other inputs/predictors

`VIF[i] = 1 / (1 - R[i]^2)`

- If `VIF[i] = 1` then X[i] is orthogonal to all other inputs/predictors
- Rule of Thumb: If `VIF[i] > 10`, then X[i] is definitely linearly dependent on other inputs/predictors and should be considered for disposal
- In general: VIF[i] should be near 1, but an acceptable range might extend to 5–6
