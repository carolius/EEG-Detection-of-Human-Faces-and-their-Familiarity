import numpy as np
from numpy import percentile
from pathlib import Path

from sklearn.preprocessing import StandardScaler

def objmap(n):
    if (n=="face"):
        return 1
    else:
        return 0
def FNFmap(n):
    if (n=="familiar"):
        return 1
    else:
        return 0
    
def Targetmap(n):
    if (n=="Target"):
        return 1
    else:
        return 0

#Combined test subjects and sessions
def dataset_array(subjects,sessions):

    data_dir = Path("../timeflux/data/")
    paths = np.array([[data_dir / f"{subj}" / f"{sesh}" for sesh in sessions] for subj in subjects]).flatten()
    #print(paths)
    X = np.empty((0,4,256)) # Placeholder for data
    y = np.empty((0)) # Placeholder for data
    for path in paths:
        for file in path.glob("data_*.npz"):
            with open(file, "rb") as npz:
                archive = np.load(npz, allow_pickle=True)
               # print(archive["X"].shape)
                if archive["X"].shape == (50, 4, 256):
                    X = np.concatenate((X, archive["X"]))
                    y = np.concatenate((y, archive["y"]))
    return X,y

## spliting dataset into 2 or 3 sub datasets, for training, validation and test

# since data is of time-series type, it should not be splitted randomly, but in a temporal way
# 2/3 of data as training set and 1/3 as validation set to have cross-session satisfied

def spliter(x,y,split_ratio):
    num_trials = np.size(y)
    train_index=int(split_ratio*num_trials)

    X_train= x[:train_index,:,:]
    X_validation= x[train_index : ,:,:]

    y_train= np.asarray( y[:train_index])
    y_validation= np.asarray(y[train_index : ])

    return X_train, X_validation, y_train, y_validation


## Preprosessing should be seperately done on training and validation data sets, for they do not effect on each other

# outliers removal via Interquartile Range Method as EEG signals are not Gaussian distributed

def outlier_free(x):
    train_trial, train_channel, train_time_sample = np.shape(x)
    index = 0
    for trial in x :
        for channel in range(train_channel):
            # calculate interquartile range
            samples = trial[channel]
            q25,q50, q75 = percentile(samples, 25), percentile(samples, 50), percentile(samples, 75)
            iqr = q75 - q25

            # calculate the outlier cutoff
            cut_off = iqr * 1.5
            lower, upper = q25 - cut_off, q75 + cut_off

            # replacing outliers with MEDIAN as they are less sensetive than mean values towards outliers
            x[index][channel] = [sample if (sample >= lower and sample <= upper) else q50 for sample in samples] 
        index +=1
    return x


# data normalization for each trial in each channel separately using StandardScalar class to get the data into zero mean and unit variance
def rescalar(x):
    index = 0
    for trial in x :
        x [index]= StandardScaler().fit_transform(trial)
        index +=1
    return x

# reshaping the training annd validation data sets into (N,ch,sample,1), where N is the number of trails, ch is the number of channels, sample 
# is the number of time samples in each epoch, for the input shape into the EEGNet model is (ch,sample,1)
def reshaper(x):
    N, ch, time_sample = x.shape

    x = x.reshape(N, ch, time_sample,1)

    
    return x