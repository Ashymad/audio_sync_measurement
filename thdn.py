from scipy import fftpack
import numpy as np


def rms(a):
    return np.sqrt(np.mean(np.square(a)))

def fftfilt(signal, frequency, fs, Q):
    ff = fftpack.rfft(signal)
    N = len(ff)
    pos = (int(np.floor((1-1/(2*Q))*N*frequency/(fs/2))),
           int(np.ceil((1+1/(2*Q))*N*frequency/(fs/2))))
    for ps in np.arange(pos[0], pos[1]+1):
        ff[ps] = 0
    return fftpack.irfft(ff)

    
def thdn(signal, fundamental, fs, Q=30):
    return rms(fftfilt(signal, fundamental, fs, Q)) / rms(signal)
