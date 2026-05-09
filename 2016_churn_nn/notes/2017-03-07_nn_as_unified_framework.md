---
date: 2017-03-07
source: self-email (6:36 AM)
---

# Neural Networks as a Unified Framework — Notes (Mar 7, 2017)

CNNs are like windowed Fourier analysis or wavelets or specialized filters, but instead of pre-specifying the
window/filter/wavelet, a CNN just learns/fits such windows/filters to the data. So you might get wavelet-like
filters, or Fourier-resembling ones, etc, but only if those help decompose the signal/image into best-fit,
knowledge-rich components....

This realization for me brought on another realization: "Wait, if CNNs are like an empirical component
analysis...is it possible that PCA, SVD, and so on can be rewritten as neural nets? Linear and logistic
regression can both be written like neural nets... Is it possible that NNs are just a framework, like wave vs
matrix mechanical approaches to quantum mechanics?"

So I started googling, and sure as shit there has been some work done (in the 80s/90s no less) showing how to
rewrite PCA as NN algorithms..

Here's more info: https://www.cs.purdue.edu/homes/dgleich/projects/pca_neural_nets_website/
