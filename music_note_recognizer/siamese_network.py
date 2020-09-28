# basic imports
import glob, os
from itertools import combinations

# data processing
import librosa
import numpy as np
import pandas as pd

# modelling
from sklearn.model_selection import train_test_split

from tensorflow.keras import backend as K
from tensorflow.keras.layers import Activation
from tensorflow.keras.layers import Input, Lambda, Dense, Dropout, Flatten, Conv2D, MaxPooling2D
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.optimizers import RMSprop, Adam

# the data pair 
from itertools import combinations
from math import factorial

BASE_DIR = os.getcwd()
if not BASE_DIR.endswith("guitar_music_note_recognizer"):
    BASE_DIR = os.path.join(BASE_DIR, "..")

BASE_DIR = os.path.abspath(BASE_DIR)

# Set the path to the full dataset 
DATA_DIR = os.path.join(BASE_DIR, "data", "guitar_sample")

# for the audio vector
MAX_PAD_LEN = 400

INPUT_DIMENSION = (40, 400, 1)

def number_of_combinations(n, r):
    return int(factorial(n) / (factorial(n - r) * factorial(r)))


def get_featuresdf(data_dir=None):
    if data_dir is None:
        data_dir = DATA_DIR

    # feature list
    features = []

    # Iterate through each sound file and extract the features 
    for folder in os.listdir(data_dir):
        for file in os.listdir(os.path.join(data_dir, folder)):
            class_label = folder
            file_name = os.path.join(os.path.join(data_dir, folder, file))
            
            data = extract_features(file_name)
            features.append([data, class_label])

    # Convert into a Panda dataframe 
    featuresdf = pd.DataFrame(features, columns=['feature','class_label'])
    print('Finished feature extraction from ', len(featuresdf), ' files') 

    return featuresdf

def extract_features(file_name):
    try:
        audio, sample_rate = librosa.load(file_name, res_type='kaiser_fast') 
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
        pad_width = MAX_PAD_LEN - mfccs.shape[1]
        mfccs = np.pad(mfccs, pad_width=((0, 0), (0, pad_width)), mode='constant')
        mfccs = mfccs.reshape(tuple(list(mfccs.shape) + [1]))

    except Exception as e:
        print("Error encountered while parsing file: ", file_name, e)
        return None 
     
    return mfccs

def prepare_data_pair(X, y, label):
    label = f"1{label}"
    semilabel = f"0{label}"
    
    indices = np.array(list(range(len(y))))
    similar_indices = indices[y == label]
    train_half_size = number_of_combinations(len(similar_indices), 2)

    semisimilar_indices = indices[y == semilabel][:train_half_size]
    
    dissimilar_indices = indices[(y != label) & (y != semilabel)]
    np.random.shuffle(dissimilar_indices)
    
    dissimilar_indices = dissimilar_indices[:train_half_size - len(semisimilar_indices)]
    dissimilar_indices = np.concatenate([semisimilar_indices, dissimilar_indices])
    
    np.random.shuffle(dissimilar_indices)
    
    similar_indices_pair = []
    dissimilar_indices_pair = []

    size = 0
    it = iter(dissimilar_indices)
    
    for i, j in combinations(similar_indices, 2):
        size += 1
        similar_indices_pair.append([i, j])
        dissimilar_indices_pair.append([i, next(it)])
    
    # get the dimension of data based on combination
    dim = tuple([2, 2*size] + list(X.shape[1:]))
    
    # build the sim and dis-sim matrix
    new_X = np.empty(dim, dtype=float)
    new_y = np.concatenate([np.ones(size, dtype=float), np.zeros(size, dtype=float)])
    
    similar_indices_pair = np.array(similar_indices_pair)
    dissimilar_indices_pair = np.array(dissimilar_indices_pair)
    
    new_X[0, :size], new_X[1, :size] = X[similar_indices_pair[:, 0]], X[similar_indices_pair[:, 1]]
    new_X[0:, size:], new_X[1, size:] = X[dissimilar_indices_pair[:, 0]], X[dissimilar_indices_pair[:, 1]]
    
    all_indices = np.array(list(range(2*size)))
    np.random.shuffle(all_indices)
    
    return new_X[:, all_indices], new_y[all_indices]

def build_base_network(input_shape):
    model = Sequential()
    
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=input_shape))
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu'))
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Flatten())
    model.add(Dense(1024))
    model.add(Dropout(0.1))
    
    model.add(Dense(256))
    model.add(Dropout(0.1))
    
    model.add(Dense(128))
    return model


def euclidean_distance(vects):
    x, y = vects
    return K.sqrt(K.sum(K.square(x - y), axis=1, keepdims=True))

def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return (shape1[0], 1)

def distance(emb1, emb2):
    return np.sum(np.square(emb1 - emb2))


def model_predict(model, afs, y=None, threshold=0.5, verbose=False):
    score = 0
    preds = model.predict([afs[0], afs[1]])
    for i in range(len(preds)):
        p = preds[i][0]
        z = int(p < threshold)
        
        if y is None:
            continue

        if z == y[i]:
            score += 1
            
        if verbose:
            print(z, y[i], p)

    accuracy = score / len(preds)

    if y is not None:
        print(f'acc: {score} / {len(preds)} = {accuracy*100}%')
    
    return int(accuracy)


def contrastive_loss(y_true, y_pred):
    margin = 1
    return K.mean(y_true * K.square(y_pred) + (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))

def initialize_model():
    audio_input_a = Input(shape=INPUT_DIMENSION)
    audio_input_b = Input(shape=INPUT_DIMENSION)

    base_network = build_base_network(INPUT_DIMENSION)

    feat_vecs_a = base_network(audio_input_a)
    feat_vecs_b = base_network(audio_input_b)

    difference = Lambda(euclidean_distance, output_shape=eucl_dist_output_shape)([feat_vecs_a, feat_vecs_b])

    # initialize model params
    optimizer = Adam()

    # initialize the network
    model = Model(inputs=[audio_input_a, audio_input_b], outputs=difference)
    model.compile(loss=contrastive_loss, optimizer=optimizer)
    return model

def get_model(label, X=None, y=None, train=False, epochs=128, batch_size=64, verbose=1):
    # create model instance
    model = initialize_model()

    # weights path
    weights_path = os.path.join(BASE_DIR, 'weights', f'{label}_weights.h5')
    
    if train or not os.path.exists(weights_path):
        # split the dataset 
        x_train_indices, x_test_indices, y_train, y_test = train_test_split(np.arange(len(y)), y, test_size=0.2, random_state = 42)
        x_train, x_test = X[:, x_train_indices], X[:, x_test_indices]

        print(f"train_input_shape = {x_train.shape}, train_output_shape={y_train.shape}")
        print(f"test_input_shape = {x_test.shape}, test_output_shape={y_test.shape}")

        assert INPUT_DIMENSION == x_train.shape[2:]
        assert INPUT_DIMENSION == x_test.shape[2:]
        
        # train model
        model.fit(
            [x_train[0], x_train[1]], 
            y_train, 
            validation_split=0.4, 
            batch_size=batch_size, 
            verbose=verbose, 
            epochs=epochs
        )

        # save weights
        model.save_weights(weights_path)

        
        # model_predict
        model_predict(model, x_test, y_test)

    else:
        # load weights
        model.load_weights(weights_path)
    
    return model

def main():
    labels = ["A", "B", "D", "EL", "EH", "G"]
    # Convert into a Pandas dataframe 
    featuresdf = get_featuresdf()

    # Convert features and corresponding classification labels into numpy arrays
    X = np.array(featuresdf.feature.tolist())
    y = np.array(featuresdf.class_label.tolist())

    for label in labels:
        print("training for label", label)

        # prepare data set pairs (similar and dissimilar)
        X_label, y_label = prepare_data_pair(X, y, label)

        print(f"input_shape = {X_label.shape}, output_shape={y_label.shape}")

        # get model instance
        get_model(label=label, X=X_label, y=y_label, train=True)

if __name__ == '__main__':
    main()
 