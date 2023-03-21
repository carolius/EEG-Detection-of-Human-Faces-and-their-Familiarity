"""Save data as Numoy array"""

import numpy as np
import pandas as pd
from timeflux.core.node import Node
from timeflux.core.exceptions import WorkerInterrupt
from timeflux.helpers.port import get_meta

import os
from datetime import datetime
import pickle



class SaveNumpy(Node):
    """Save to nympy arrays

        Explaination goes here

    Attributes:
        i (Port): Default data input, expects DataFrame.
        i_events (Port): Event input, expects DataFrame.
        o (Port): Default output, provides DataFrame and meta.
        o_* (Port): Dynamic outputs, provide DataFrame and meta.

    Args:
        save_data (?): ?
        session (?): ?
        subject (?): ?
        data_folder (?): ?

    Example:


    """

    def __init__(
        self,
        save_data=True,
        session="session0001",
        subject="subject0001",
        data_folder=".",
    ):

        # Parameters set by user
        self._save_data = save_data
        self._session = session
        self._subject = subject
        self._data_folder = data_folder

        # Parameters NOT ser by user
        self._shape = None
        self._X_train = None
        self._y_train = None
        self.meta_label = ("epoch", "context")

    def update(self):

        port = self.i
        if port.ready():

            index = port.data.index.values[0] # earliest timestamp of recieved epoch # NOT USED ATM?


            data = port.data.values
            data = data.transpose(1,0) # transpose data to match scikit learn input
            label = get_meta(port, self.meta_label) # get label of epoch

            # Check shape of epoch
            if self._shape and (data.shape != self._shape):
                self.logger.warning("Invalid shape")
            if self.meta_label is not None and label is None:
                self.logger.warning("Invalid label")


            # If _X_train is None: create array, else: append to _X_train
            if self._X_train is None:
                self._X_train = np.array([data])
                self._shape = self._X_train.shape[1:]
                # self._shape = (self._shape[0], 1024) # REMOVE THIS (SHOULD NOT MAKE A DIFFERENCE)?
            else:
                self._X_train = np.vstack((self._X_train, [data]))
            #indices = np.append(indices, index)
            # print("Indices shape: ", indices.shape) # This is probalt interesting to look at if the epochs are overlaping. Try this.

            # If _y_train is None: create array, else: append to _y_train
            if label is not None:
                if self._y_train is None:
                    self._y_train = np.array([label])
                else:
                    self._y_train = np.append(self._y_train, [label])


    def terminate(self):
        # Pickle training data
        # TODO: How do we want to set these timestamps? Based on timeflux clock or local time (currently - local time)
        if self._save_data:
            folder = '{}/{}/{}'.format(self._data_folder, self._subject, self._session)
            try:
                os.makedirs(folder)
            except OSError as e:
                pass
            self._time_lastest_fitting = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            np.savez(f"{folder}/data_{self._time_lastest_fitting}",X=self._X_train, y=self._y_train)
