import tensorflow as tf

Sequential         = tf.contrib.keras.models.Sequential
Dense              = tf.contrib.keras.layers.Dense
Activation         = tf.contrib.keras.layers.Activation
GaussianNoise      = tf.contrib.keras.layers.GaussianNoise
BatchNormalization = tf.contrib.keras.layers.BatchNormalization


def build_model(n_features, n_hidden=11, depth=5, noise_std=0.1):
    """Build and compile the churn prediction neural network.

    Architecture: `depth` hidden layers, each Dense(n_hidden) → GaussianNoise →
    ReLU, with BatchNormalization on the first hidden layer only.
    Output: single sigmoid unit (binary churn probability).

    GaussianNoise between layers acts as a regularizer — empirically responsible
    for roughly half of the total AUC gain from ~0.64 to ~0.73 over the baseline.

    Args:
        n_features: number of input features.
        n_hidden:   units per hidden layer (default 11).
        depth:      number of hidden layers (default 5).
        noise_std:  standard deviation of injected Gaussian noise (default 0.1).

    Returns:
        Compiled Keras Sequential model.
    """
    model = Sequential()

    # First hidden layer — includes BatchNormalization
    model.add(Dense(n_hidden, input_dim=n_features))
    model.add(GaussianNoise(noise_std))
    model.add(BatchNormalization())
    model.add(Activation('relu'))

    # Remaining hidden layers
    for _ in range(depth - 1):
        model.add(Dense(n_hidden))
        model.add(GaussianNoise(noise_std))
        model.add(Activation('relu'))

    # Output layer
    model.add(Dense(1, activation='sigmoid'))

    model.compile(
        loss='binary_crossentropy',
        optimizer='adam',
        metrics=['accuracy'],
    )
    return model
