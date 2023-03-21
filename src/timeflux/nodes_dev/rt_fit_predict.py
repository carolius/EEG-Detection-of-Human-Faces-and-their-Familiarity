from glob import glob
from pathlib import Path
import numpy as np
from timeflux.helpers.port import get_meta, make_event
from timeflux.core.node import Node

from pyriemann.estimation import XdawnCovariances
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from pyriemann.tangentspace import TangentSpace
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from zmq import EVENT_CLOSE_FAILED


# Statuses in ml node.
IDLE = 0
ACCUMULATING = 1
FITTING = 2
READY = 3


# ==== Node - called and run from Timeflux ====
class Pipeline(Node):
    '''
     fitting and prediciting
    '''

    def __init__(self):
        self.status = 1
        self._pipeline = None
        # Random generator
        self.rng = np.random.default_rng()
        self._X_train = None
        self._y_train = None
        # self.port = self.i_eeg_epochs

    def update(self):
        self.logger.debug("update")
        # self.clear()
        status_port = self.i_status_events
        
        if status_port.ready():
            df = status_port.data
            self.status = df.iloc[0]['data']

        if self.status == ACCUMULATING:
            port = self.i_epochs_in
            # self.logger.debug(f"rt_fit port state:  {port.ready()}")
            if self.i_epochs_in.ready():
                data = port.data.values
                # transpose data to match scikit learn input
                data = data.transpose(1, 0)
                # get label of epoch
                label = get_meta(port, "epoch")

                if self._X_train is None:
                    self._X_train = np.array([data])
                else:
                    self._X_train = np.vstack((self._X_train, [data]))

                if self._y_train is None:
                    self._y_train = np.array([label])
                else:
                    self._y_train = np.append(self._y_train, [label])

        elif self.status == FITTING:
            if self._pipeline == None:
                self._fit_model()

            self._predict()

    def _fit_model(self):

        self._pipeline = make_pipeline(
            XdawnCovariances(4, estimator="lwf", xdawn_estimator="scm"),
            TangentSpace(metric="riemann"),
            StandardScaler(),
            LDA(solver="lsqr", shrinkage="auto"),
        )

        # changing string markers to 0 or 1
        y_train_transformed = np.array([1 if t['context'] ==
                                        'face' else 0 for t in self._y_train])
        self._pipeline.fit(self._X_train, y_train_transformed)

    def _predict(self):
        port = self.i_epochs_in
        if port.ready():
            data = port.data.values
            # transpose data to match scikit learn input
            data = data.transpose(1, 0)
            label = get_meta(port, "epoch")  # get label of epoch

            X = np.array([data])
            y = label

            pred = self._pipeline.predict(X)
            self.display_prediction(y, pred)

    def display_prediction(self, y, pred):
        prediction = 'face' if pred[0] == 1 else 'object'
        self.o_predictions.data = make_event(
            "prediction", {"prediction":prediction,"actual":y["context"]}, serialize=False)

    def terminate(self):
        '''
        Called by timeflux when closing down
        '''
        # TODO - there is an ugly error when closing down due to the LSL stream being closed, I don't know what to do about it. It works but is ugly.


if __name__ == '__main__':
    n = Pipeline()
