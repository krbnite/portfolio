PCA / ZCA Whitening:  
    * http://ufldl.stanford.edu/tutorial/unsupervised/PCAWhitening/
    * https://stats.stackexchange.com/questions/117427/what-is-the-difference-between-zca-whitening-and-pca-whitening
    
Factor Analysis:
* https://www.analyticsvidhya.com/blog/2015/11/8-ways-deal-continuous-variables-predictive-modeling/

Things to try
PCA / ZCA Whitening:  http://ufldl.stanford.edu/tutorial/unsupervised/PCAWhitening/

#### Class Imbalance...
Might I have a class imbalance problem?!
https://aqibsaeed.github.io/2016-08-10-logistic-regression-tf/

#### Some Helpful TF Pages
http://learningtensorflow.com/index.html

## TensorBoard
* Good for the hyperparameter search

```python
# Try a few learning rates
for learning_rate in [1e-1,5e-2,1e-2,5e-3]:
    # Play w/ varying number of hidden layers
    for use_sig_hl_w_7_nodes in [True, False]:
        for use_tanh_hl_w_7_nodes in [True, False]:
            # Construct a unique hyperparameter string for each run
            hparam_str = mk_hparm_str(learning_rate, use_sig_hl_w_7_nodes, use_tanh_hl_w_7_nodes)
            writer = tf.summary.FileWriter(logsDir + hparam_str)
            # Run Model w/ new settings
            churn_model(learning_rate, use_sig_hl_w_7_nodes, use_tanh_hl_w_7_nodes)
            # To see all runs in TensorBoard, point TB at parent directory (logs)
```

TensorBoard has a very useful feature: the embedding visualizer.  It allows you take very high-dim
data and project it onto 2 or 3 dims using PCA or t-SNE.  (See tutorial on TF website.)
