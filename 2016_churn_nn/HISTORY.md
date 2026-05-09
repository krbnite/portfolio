---
assembled: 2026-05-08
sources: notebooks, blogs, meeting notes, self-emails (updated with 5 additional blog posts)
---

# Historical Overview — Churn Neural Network Project (2016–2017)

This document pieces together the narrative from notebooks, blog posts, and notes written throughout
the project — a chronological intellectual history of how a logistic regression model became a
production neural network.

---

## The Baseline: What Was Inherited (October 2016)

The project began with an inherited system. The prior analyst at an outside vendor (EXL) had built
three logistic regression models in SAS covering overall, voluntary, and involuntary one-month churn,
plus a six-month retention model and a trial conversion model. The customer base sat around one million
active subscribers with three million total accounts and two-plus years of data.

Meeting notes from October 17, 2016 describe their methodology in detail. Given an initial set of 700+
variables, the goal was to end up with 5–10 of the most important ones through a multi-stage filter:

1. **Information Value (IV) and Pearson Correlation** — IV < 0.02 meant useless; > 0.3 was strong.
   This reduced ~700 features to ~50. At this stage the component IVs were also examined to decide
   whether variable binning was well-chosen, whether a log transform was warranted, and so on.

2. **Variable Clustering (VARCLUS)** — Checked the reduced set for confounded/correlated features.
   Correlated variables were clustered and one candidate from each cluster was retained. The SAS
   documentation was quoted directly: *"When statisticians try to build models with a large number of
   variables, it becomes difficult to figure out the correct relationships... redundant variables can
   degrade the model by destabilizing parameter estimates, increasing computation time, confounding
   interpretation."*

3. **Variance Inflation Factor (VIF)** — `VIF[i] = 1/(1-R²)`. Rule of thumb: VIF > 10 means the
   variable is linearly dependent on others and should be reconsidered.

The most important features the prior model had identified:

- `num_vol_losses` — number of times the customer had voluntarily canceled in the past
- `tot_lin_days_new` — days watched linear feed over account lifetime; interpreted as a signal that
  the customer genuinely loves the programming universe
- `no_view_90_days_flag` — binary: watched anything in the last 90 days or not
- `num_invol_fail` — historical involuntary cancellations
- `num_nc_em_rcvd_all_tm` — emails about new content received (an imperfect variable; the email
  provider had been inconsistently missing deliveries)

The prior analyst ran stepwise combinatorial logistic regression in SAS to narrow to the best 6–10
features, fit coefficients, and tested on held-out data and out-of-time periods.

---

## Challenging the Baseline (Late 2016)

The question was straightforward: *do these models and variables still work?* The plan was to assess
ongoing performance using Character Stability Index (CSI) and Population Stability Index (PSI).

But there was a deeper issue. The argument for sticking with logistic regression was its
interpretability — you can read the coefficients. However, the feature selection methodology
employed VARCLUS to reduce multicollinearity, then still ran stepwise selection. If VARCLUS was
doing its job perfectly, there would be no multicollinearity left and the LR coefficient estimates
would be clean. But if it wasn't — and the notes flag this explicitly, noting that `tot_view_days_new`
was approximately `tot_lin_days_new + NOISE` suggesting the clustering step was imperfect —
then the interpretability argument weakened considerably.

The idea: if the interpretability advantage of LR was questionable anyway, what would a neural network
give up by comparison — and what might it gain?

---

## The Replication: Building the Baseline in Python (Late 2016)

The first notebook (`01_baseline_lr_rf.ipynb`) set out to replicate the prior model using scikit-learn
and TensorFlow, verifying that the feature set and preprocessing pipeline matched the documented SAS
outputs. Data was pulled from Redshift: roughly 71 MB, a manageable size.

Then came a moment that reoriented the evaluation approach entirely. Looking at the churn label
distribution in the training data:

> *"Customers who churn in 1 month: **6.83%** of the training set."*

And then, immediately:

> **"WTF?!?!?! Might I have a class imbalance problem?!"**

With 93.17% of customers retained, a model that just predicted "retained" for every single customer
would achieve 93% accuracy. The next line in the notebook made this concrete:

> *"Shot-Calling Accuracy: 93.21%, 93.18%, and 93.16% of y_train, y_valid, and y_test...
> it is unclear then if 94% accuracy is anything to brag about, or how much better is 95% accuracy
> than 94% accuracy?"*

The answer was: not much. AUC (area under the ROC curve) became the primary metric from this point
forward. The baseline logistic regression achieved AUC ~0.64. The random forest agreed closely with
this number — useful confirmation that both methods were seeing the same signal.

---

## Parallel Track: Learning TensorFlow and Deep Learning (Early 2017)

Simultaneously, a parallel learning track was underway. The wrap-up post from July 2017 gives the
origin story: it started with a chance conversation where someone asked, "Do you know anything about
neural networks?" The honest answer was "sort of." The next morning there was an email from Udacity
promoting the first run of their Deep Learning NanoDegree Foundation. Timing was perfect; enrollment
was immediate.

The nanodegree ran January through July 2017, directly concurrent with the churn neural network
project. A physics background helped — "it was fun to think of the unfamiliar constructs and
terminology in terms of things I knew from my past: topology and manifolds, Lagrangians and
Hamiltonians, time series and spectral analysis." The language of reinforcement learning (states,
actions, policies, geodesics) mapped naturally to Lagrangian mechanics. The language of autoencoders
(latent variables, prior distributions, observables) mapped naturally to quantum mechanics.

It also marked a professional transition. Before the nanodegree, most work was in R/RStudio — having
learned R from Roger Peng and Jeff Leek's early Coursera courses and spent years on it. After: "I am
now nearly 100% pythonista. Before, I was doing all my modeling, statistical analyses, reports, and
presentations in R/RStudio. After, R has become somewhat of a 'library' that I sometimes call from
within a Jupyter Notebook."

This produced blog posts as a way of cementing what was being learned.

**"Linear Regression in TensorFlow" (March 2017)** — This post laid out a key conceptual anchor:

> *"One can get a sense that neural nets may serve as a generalized framework for data analysis in
> general, encompassing techniques such as linear and logistic regression, principle component
> analysis (PCA), and deep neural nets like convolutional neural networks (CNNs) and recursive
> neural networks (RNNs)."*

The post also includes careful explanations of TensorFlow's tensor types and why normalization means
something very different in the linear algebra sense versus the statistical sense — and why the NN
context is closer to the former.

Then, in a 6:36 AM email to self on March 7, 2017, a chain of realizations:

> *"CNNs are like windowed Fourier analysis or wavelets or specialized filters, but instead of
> pre-specifying the window/filter/wavelet, a CNN just learns/fits such windows/filters to the data.
> So you might get wavelet-like filters, or Fourier-resembling ones, etc, but only if those help
> decompose the signal/image into best-fit, knowledge-rich components..."*
>
> *"This realization for me brought on another realization: 'Wait, if CNNs are like an empirical
> component analysis...is it possible that PCA, SVD, and so on can be rewritten as neural nets?
> Linear and logistic regression can both be written like neural nets... Is it possible that NNs
> are just a framework, like wave vs matrix mechanical approaches to quantum mechanics?'"*
>
> *"So I started googling, and sure as shit there has been some work done (in the 80s/90s no less)
> showing how to rewrite PCA as NN algorithms."*

This was not academic curiosity. The unifying-framework lens justified why building a neural network
for churn prediction was a natural extension of the existing logistic regression work, not a departure
from it.

---

## Building the Neural Network in TensorFlow (Early–Mid 2017)

The second notebook (`02_nn_initial.ipynb`) began the first real neural network attempts using the
raw TensorFlow API. The feature set was expanded beyond the original 4–6 baseline variables to 19
features including month dummies and VOD/NXT viewership positional variables.

By the time of `03_nn_tensorflow_verbose.ipynb`, the preprocessing pipeline was documented
thoroughly. One notable observation from examining the prior model's floor-cap treatment:

> *"The remaining NaNs made me uncomfortable, seeming suggestive of having queried for the wrong
> data. However, these NaNs make sense based on how the data set was built. For `num_invol_fail`,
> these are people who have 0 involuntary failures (you will notice there are no 0's in this
> feature), so zero-filling the NaNs is appropriate."*

The reciprocal transform (`-1/(x + nudge)`) was settled on as the monotonic transformation for
continuous features, chosen over Box-Cox and log transforms through empirical comparison. The `fn11`
scaling function (to [-1, 1]) was used throughout.

This verbose notebook produced AUC **0.722** on the validation set — a substantial lift over the
baseline's ~0.64, achieved purely from the NN architecture and the expanded feature set, before any
regularization.

**TensorBoard as the hyperparameter search tool** — The notebooks contain a systematic grid search
over learning rates (1e-1, 5e-2, 1e-2, 5e-3), hidden layer activation functions (sigmoid vs. tanh),
and number of layers, logged to TensorBoard for visual comparison. The embedding visualizer was also
noted as valuable for projecting the high-dimensional customer feature space into 2D/3D via PCA or
t-SNE.

---

## Concurrent Explorations: May–June 2017

The months between getting the initial TF model working and the final Keras model were busy with
parallel threads of exploration that leave traces in the blogs.

**"Artificial Funklord" (May 11, 2017)** — An attempt to generate Toe Jam & Earl-style music using
a recurrent neural network. The blog entry ends mid-thought ("Have to get back to work."), which
captures the moment perfectly: ideas were everywhere and there was only so much time. The post
introduced RNNs through a vivid analogy — your mind as an RNN, where each moment's memories and
recent actions feed into the next action, which becomes a memory, which may be something you wish to
forget "or something you wish to tell and re-tell, and maybe embellish a little bit."

**"ReLU vs Sigmoid vs Tanh" (May 22, 2017)** — A close reading of Glorot & Bengio's research on
activation functions. The conclusion, from two papers: sigmoid is "unsuited for deep networks with
random initialization" because of saturation; tanh is better but still doesn't have biological
plausibility in terms of activation sparsity; ReLU wins because only a subset of neurons are active
at any time, enforcing sparsity and creating a network that "can be seen as an exponential number of
linear models that share parameters."

This research directly informed the final architecture's use of ReLU throughout. There's also a candid
note about BatchNormalization: *"this is probably why batch norms don't work well for me; extra
degrees of freedom mean, at the least, more training epochs; at worst, I'm not using enough data."*
That's the explanation for why BatchNorm appears only on the first hidden layer in the final model —
it was tried more aggressively and found to underperform.

**"Exploring and Exploiting Markovia" (June 15, 2017)** — Notes on reinforcement learning:
Q-learning, policy gradients, deep Q-networks, and the exploration-exploitation tradeoff. The Markov
property — future state depends only on current state, not history — was explained through the lens of
Lagrangian physics ("states, configuration space, phase spaces, and geodesics"). Though RL wasn't
applied to the churn problem directly, thinking about customer behavior as a stochastic process over a
state space was clearly in the background.

**"Notes on Autoencoders" (June 26, 2017)** — This one is the most significant to the churn project.
Autoencoders are trained to reconstruct their input while resisting memorization through
regularization or constraint — they learn "useful representations" rather than perfect identity.
The post traces the connection to Fourier analysis and PCA explicitly:

> *"A simple autoencoder can be used to mimic PCA (that is, to find a set of basis vectors that span
> the same space as the orthogonal basis identified in PCA)."*

More directly relevant: the section on **denoising autoencoders**, which inject noise into the input
during training and then have the network reconstruct the clean original. The purpose is to force the
network to learn robust representations that generalize beyond the specific noise patterns it was
trained on. The code shows `noisy_imgs = imgs + noise_factor * np.random.randn(*imgs.shape)` fed as
input while the clean `imgs` serve as targets. This is conceptually the same principle as the GaussianNoise layers in the churn model. The
autoencoder post appeared just weeks before the Keras model was finalized — encountered both through
the nanodegree and through a deliberate research quest triggered by the earlier personal revelation
about noise as a regularizer.

---

## Getting GPU Access on AWS (May 2017)

**"Accessing Jupyter Notebooks and TensorBoard on AWS" (May 2017)** documented the process of
getting GPU-accelerated training running — both on a personal account and on a work account with a
private IP (requiring SSH tunneling). The motivation:

> *"Richard Feynman is quoted as saying, 'Physics is to mathematics like sex is to masturbation.'
> This basically is what a GPU is to deep learning. Have you ever trained on a GPU after only ever
> training on your laptop's CPU?"*

The business case for the work GPU was made on the basis of 3–5x runtime reduction, enabling faster
exploration of the feature, parameter, and hyperparameter spaces. *"Unsurprisingly, it was a fairly
easy sell."* The bureaucratic path to actually getting it set up — negotiations, permission errors,
CUDA misconfiguration — was less easy. A follow-up post in July 2017 documented the recovery
procedure when the EC2 Conda environment broke, with `conda install tensorflow-gpu` as the fix that
the official TF docs didn't suggest.

---

## The Gaussian Noise Insight (Mid 2017)

The most consequential architectural decision was the introduction of `GaussianNoise` layers between
the dense hidden layers. The insight was personal: while thinking and developing, white noise and
soundscapes were a constant — they helped reduce mental clutter and made it easier to think clearly.
That habit led to a direct question: "Maybe injecting noise at input and between layers could help
this neural net as well." So that's what was tried, and it worked. Only afterward came the research
quest that turned up the existing literature — Gaussian noise injection, dropout, denoising
autoencoders — confirming that the idea had been documented, just not the specific motivation behind
arriving at it independently.

Empirically, the noise injection was responsible for roughly half of the total AUC improvement from
~0.64 to ~0.752 over the baseline.

The final architecture, as it appears in `07_nn_keras.ipynb`:

```python
model.add(Dense(11, input_dim=n_features))
model.add(GaussianNoise(0.1))
model.add(BatchNormalization())   # first layer only
model.add(Activation('relu'))
# ... repeated 4 more times without BatchNorm
model.add(Dense(1, activation='sigmoid'))
```

5 hidden layers, 11 units each, Gaussian noise (σ=0.1) after each dense layer, BatchNorm on the
first hidden layer only, ReLU activations throughout, sigmoid output, Adam optimizer, binary
crossentropy loss. The feature set expanded to 22 variables: 4 core baseline predictors, 9 VOD/NXT
positional engagement variables, and 12 monthly seasonality dummies. The training set had 711,604
rows.

---

## Final Results

| Metric     | Training | Validation |
|------------|----------|------------|
| ROC-AUC    | 75.9%    | 75.2%      |
| Precision  | 59.8%    | 61.0%      |
| Recall     | 9.9%     | 9.9%       |
| PR-AUC     | 27.0%    | 27.1%      |
| F1 Score   | 16.9%    | 17.1%      |

The training/validation gap is small — a sign that regularization (Gaussian noise) was working.
Precision of ~60% is strong for a 7% base rate: the model identifies churners at roughly 8× the
random rate. Low recall is expected in this regime given the threshold; in practice the model was
used to rank-order customers by churn probability for retention interventions, where the gain charts
(decile analysis) showed strong lift in the top two or three deciles.

The model was saved on June 20, 2017 and the production pipeline was set to score the full active
subscriber base daily via cron, writing churn probabilities back to Redshift.

---

## What Was Going On Intellectually

Reading across all the notebooks and notes, a few threads run through the project:

**The unified-framework idea.** From the March 2017 email to the linear regression blog post to
the architecture of the final model, there is a consistent thread of treating neural networks not
as black-box magic but as a framework that subsumes familiar tools — linear regression, logistic
regression, PCA — and generalizes them. This made the project feel less like "trying a new thing"
and more like "doing the same thing, but properly."

**Honest reckoning with the baseline.** The shot-calling accuracy observation — that 93% accuracy
means almost nothing when 93% of customers retain — shows up identically in at least three different
notebooks. It keeps getting re-derived, each time as a checkpoint before running a model. There
is something careful about that: the refusal to let a good-looking number go unexamined.

**The stats-in-use notes.** The file `stats_in_use.txt` (dated February 2017) is a personal
reference document on AUC, concordant/discordant pairs, Goodman-Kruskal Gamma, Kendall's Tau,
Somers' D, the Wald test, VIF, and ordinal association — the entire evaluation vocabulary being
assembled from scratch. Written in the voice of someone who has just looked these things up and is
explaining them to themselves.

**Feature engineering as signal detection.** The viewership position variables (`vod_lst_30days`,
`vod_lst_30to60days`, `vod_lst_60to90days`, and their NXT equivalents) encode not just engagement
level but its *trajectory* across three 30-day windows. The Big Four event indicator variables
(`rumble30`, `mania30`, `slam30`, `survivor30`) capture whether the customer subscribed in the shadow
of a marquee pay-per-view — a proxy for fair-weather fandom that the baseline model had not
represented. These were added after examining the model's residuals against the content calendar.

**The physics background as a translation layer.** The wrap-up post and the RL/autoencoder posts show
a consistent habit of mapping unfamiliar ML concepts onto known physics analogies: CNNs as windowed
Fourier analysis, RNNs as Markov processes, autoencoders as projection operators, VAEs as generative
probabilistic models analogous to quantum mechanics. This wasn't decoration — it was a genuine
scaffold for understanding. The March 2017 "unified framework" email is probably the clearest
expression of this: the question "are NNs just a framework, like wave vs. matrix mechanical
approaches to quantum mechanics?" is the kind of question only someone trained in physics would think
to ask, and it turned out to be the right question.

**The noise-as-regularization idea: personal revelation first, then a research quest.** The insight
came first from a personal habit of working to white noise and soundscapes — noticing that it reduced
mental clutter and helped think more clearly, then asking whether the same might be true for the
network. That personal revelation then launched a deliberate
search for existing work on the idea, which turned up a landscape of related techniques: named
Gaussian noise injection, dropout, and denoising autoencoders, among others. The nanodegree was
another channel through which the denoising autoencoder specifically was encountered. The point is
that the idea originated independently and was subsequently validated by finding that the literature
had arrived at the same principle from multiple directions — not the other way around.
