import os
import math

import librosa
import numpy as np


def fft(f):
	""" fast fourier transform """

	Ni = len(f)
	Mi = int(Ni / 2)
	if Mi <= 2:
		return [
			f[0] + f[1] + f[2] + f[3],
			f[0] - 1j * f[1] - f[2] + 1j * f[3],
			f[0] - f[1] + f[2] - f[3],
			f[0] + 1j * f[1] - f[2] - 1j * f[3],
		]

	wn = math.cos(2 * math.pi / Ni) - 1j * math.sin(2 * math.pi / Ni)
	fe = [f[i] for i in range(Ni) if i % 2 == 0]
	fo = [f[i] for i in range(Ni) if i % 2 == 1]
	Fe = fft(fe)
	Fo = fft(fo)
	return [np.around(Fe[i] + (wn ** i) * Fo[i], decimals=10) for i in range(Mi)] + [
		np.around(Fe[i] - (wn ** i) * Fo[i], decimals=10) for i in range(Mi)
	]


def get_pressed(f, spectrum):
	""" check which note was pressed """
	fh = [329, 247, 196, 147, 110, 82]
	notes = ["EH", "B", "G", "D", "A", "EL"]

	f, spectrum = zip(*sorted(zip(f, spectrum), key=lambda x: x[1], reverse=True))
	f1 = f[0]
	f2 = None
	for fi in f:
		if abs(fi - f1) >= 200:
			f2 = fi
			break

	f1, f2 = min(f1, f2), max(f1, f2)
	rows, rows_delta = zip(
		*sorted(
			zip([i for i in range(len(fh))], [abs(f1 - fi) for fi in fh]),
			key=lambda x: x[1],
		)
	)

	
	row = rows[0]
	row_delta = rows_delta[0]

	print(f"  Frequencies detected {notes[row]}[{row_delta}]: {f1}Hz, {f2}Hz.")

	if row_delta <= 5:
		return notes[row]


def get_audio_data(filename=None, quiet=True):
	fs = 2 ** 12  # sample rate
	tp = 4  # sampling duration
	N = n = fs * tp  # number of samples
	
	# Extract data and sampling rate from file
	recording, fs = librosa.load(filename, sr=fs, duration=2)
	recording = recording.reshape(-1, 1)
	N = n = len(recording)

	tp = int(n / fs)
	if tp < 2:
		if not quiet:
			print("Less than two seconds")
		return

	tp = 2
	N = fs * tp  # number of samples

	x = [round(float(recording[i]), 10) for i in range(n)]  # input sequence
	return x, tp, N


def get_frequency_amplitude(x, tp, N):
	_X = fft(x)  # discrete Fourier transform
	X = [round(Xi / N, 10) for Xi in _X]  # frequency spectrum
	X_amp = [np.absolute(Xi) for Xi in X]  # amplitude spectrum

	M = int(N / 2)
	ti = [i * tp / N for i in range(N)]
	fi = [i / tp for i in range(M)]
	X_amp = np.array(X_amp[:M]) * 2

	return ti, fi, X_amp


def detect_note(filepath):
	audio_features = get_audio_data(filepath, quiet=True)
	if not audio_features:
		return

	x, tp, N = audio_features
	ti, fi, X_amp = get_frequency_amplitude(x, tp, N)

	return get_pressed(fi, X_amp)
