#!/usr/bin/env python
import os

import librosa
from tqdm import tqdm

import numpy as np
from scipy import signal as sig

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import confusion_matrix, classification_report

from .models import AUDIO_SAMPLES_DIR
from django.conf import settings


def extract_features(filepath):
    # Extract data and sampling rate from file
    recording, sr = librosa.load(filepath, sr=2**12, duration=2, mono=True)

    stft = librosa.stft(recording, n_fft=512, window=sig.windows.hamming)
    stft = np.absolute(stft).mean(1)
    return stft


def get_data(data_dir: str, callback=lambda x: x) -> np.array:
    # feature list
    input_data, output_data = [], []

    # Iterate through each sound file and extract the features
    for folder in tqdm(os.listdir(data_dir)):
        class_label = folder

        for file in os.listdir(os.path.join(data_dir, folder)):
            file_name = os.path.join(os.path.join(data_dir, folder, file))

            input_data.append(callback(file_name))
            output_data.append(class_label)

    input_data, output_data = map(np.array, [input_data, output_data])
    return input_data, output_data


def evaluate_model(data_dir, feature_extractor):
    model = initialize_model()
    x, y = get_data(data_dir, feature_extractor)

    # split train and test data
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=100)
    x_train = x_test = y_train = y_test = []

    for train_index, test_index in sss.split(x, y):
        x_train, x_test = x[train_index], x[test_index]
        y_train, y_test = y[train_index], y[test_index]

    # train model
    model.fit(x_train, y_train)

    print(f"training accuracy = {model.score(x_train, y_train):.2f}")
    print(f"test accuracy = {model.score(x_test, y_test):.2f}")

    y_pred = model.predict(x_test)
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))


def initialize_model():
    return KNeighborsClassifier(n_neighbors=3, weights="distance", algorithm="ball_tree")


def get_model(data_dir, feature_extractor):
    x, y = get_data(data_dir, feature_extractor)

    model = initialize_model()
    model.fit(x, y)

    return model


def recognize(model, filepath):
    return model.predict([extract_features(filepath)])[0]


# DATA_DIR = os.path.join("..", "guitar_audio_sample_detection", "data", "guitar_sample")
DATA_DIR = os.path.join("..", settings.MEDIA_ROOT, AUDIO_SAMPLES_DIR)
evaluate_model(data_dir=DATA_DIR, feature_extractor=extract_features)
