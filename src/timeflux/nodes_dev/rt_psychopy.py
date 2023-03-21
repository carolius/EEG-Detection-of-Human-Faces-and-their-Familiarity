"""This module has nodes for psychopy with Timeflux."""

"""I have placed this in the timeflux_ui/nodes path. """


# Statuses in ml node.


from glob import glob
import os
from pathlib import Path
from turtle import update
from matplotlib.pyplot import pink
import numpy as np
from psychopy import visual, core, event
from sklearn.metrics import accuracy_score
from timeflux.helpers.port import get_meta
from timeflux.core.node import Node
from pylsl import StreamInfo, StreamOutlet
from time import time
import random
from pyriemann.estimation import XdawnCovariances
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from pyriemann.tangentspace import TangentSpace
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from timeflux.helpers.background import Task
from itertools import islice
from timeflux.helpers.port import make_event
import timeflux.core.logging
IDLE = 0
ACCUMULATING = 1
FITTING = 2
READY = 3


class MarkerStreams(object):
    '''
    Class that is used for a common marker outlet.

    Parameters:
        nbrChannels (int): How many channels to send.
        typeChannels (string): What type of data to send, e.g.'string', 'int32'
        channel_names (list of string): The names for the channels
        ch_units (dict of strigns): label:unit. Same labels as in channel_names. What unit for the channel
        ch_types (dict of strigns): label:type. Same labels as in channel_names. What type for the channel

    '''

    def __init__(self,
                 nbrChannels=2,
                 typeChannels="string",
                 channel_names=["label", "data"],
                 ch_units={"label": "misc", "data": "misc"},
                 ch_types={"label": "marker", "data": "marker"}
                 ):

        # Create info about stream
        _marker_StreamInfo = StreamInfo(
            name="MarkersPsychopy",
            type="Markers",
            channel_count=nbrChannels,
            nominal_srate=0,
            channel_format=typeChannels,
            source_id="MarkersPsychopyNode")

        # Set names on the chanels
        chns = _marker_StreamInfo.desc().append_child("channels")
        for label in channel_names:
            ch = chns.append_child("channel")
            ch.append_child_value("label", label)
            # Is this correct value?
            ch.append_child_value("unit", ch_units[label])
            # Is this correct value?
            ch.append_child_value("type", ch_types[label])

        # Create outlet
        self._marker_StreamOutlet = StreamOutlet(_marker_StreamInfo)

    def push_sample(self, markers, timestamp=time()):
        '''
        Send a marker over the LSL stream. 
        '''
        self._marker_StreamOutlet.push_sample(markers, timestamp)


# ==== Node - called and run from Timeflux ====
class MyPsychopyNode(Node):
    '''
    Realtime face vs object experiment. 
    '''

    def __init__(self): 
        # train and validation are both taken from the same folder; one after the other
        # setting self.img_from_each_class to 5 will draw 5-train and 5-validation from each class folder
        # in this case 10 images in each folder are needed!
        class_1 = "Marcus Faces"
        class_2 = "non-face images"
        self.img_from_each_class = 5
        self.status = ACCUMULATING
        # Create LSL outlet stream.
        self.stream_outlet = MarkerStreams()
        # Create psychopy windows and text objects.
        self.window = visual.Window(
            [900, 1000], monitor="testMonitor", units="deg", fullscr=False)
        self.stimObj = visual.TextStim(
            win=self.window, text="", color=[-1, -1, -1])
        self.stimObj.autoDraw = True  # Text is drawn on all flips.
        # get root path of git repo
        self.root_path = next(
            filter(lambda p: p.name == "group-b", Path.cwd().parents))
        self.datasets_path = self.root_path / "datasets"

        faces = (("face", self.generate_image_stim(path))
                 for path in (self.datasets_path / class_1).glob("*"))  # [0:3]
        faces_train = list(islice(faces, self.img_from_each_class))
        faces_val = list(islice(faces, self.img_from_each_class))
        objects = (("object", self.generate_image_stim(path)) for path in (
            self.datasets_path / class_2).glob("*"))  # [0:3]
        objects_train = list(islice(objects, self.img_from_each_class))
        objects_val = list(islice(objects, self.img_from_each_class))
        self.stimImg = objects_train + faces_train
        self.stimImg_validation = objects_val + faces_val
        random.shuffle(self.stimImg)
        random.shuffle(self.stimImg_validation)

        self._iti = 0.8  # Inter trial interval - time between stimuli
        self._soa = 1  # Stimulu onset asynchrony - time stimuli is shown
        self._jitter = 0.2   # Noise/unpredicted time between stimuli.
        # Random generator
        self.rng = np.random.default_rng()
        self._X_train = None
        self._y_train = None
        self.first_time = True
        self.correct_preds = []
        self._init_experiment()
        self._run_experiment()
        

    def update(self):
        self.display_prediction() # done first to make sure port is open when data arrives (should do nothing first time)
        self.logger.debug("update")
        self.o_status_events.data = make_event(
            "status", self.status, serialize=False)

        if self.status == FITTING:
            if self.first_time:
                self.wait_for_space("press space to enter prediciton mode")
                self.first_time = False
            else:
                self.collect_data_for_prediction()
                

    def collect_data_for_prediction(self):
        (mark, image) = random.choice(self.stimImg_validation)
        marker = ['stimuli_marker', mark]
        image.draw()
            # Timestamp for showing stimuli (Should be as close to window.flip() as possible)
        timestamp = time()
        self.window.flip()  # Show stimuli

            # push marker to outlet.
        self.stream_outlet.push_sample(marker, timestamp)

        core.wait(self._soa)  # Show stimuli for this time

        self.stimObj.text = ''  # Remove stimuli
        self.window.flip()

            # Wait a bit between stimuli
        core.wait(self._iti + self.rng.random() * self._jitter)
       

    def display_prediction(self):
        pred_port = self.i_predictions
        if pred_port.ready():
            df = pred_port.data
            prediction = df.iloc[0]['data']
            pred = prediction['prediction']
            actual = prediction['actual']
            self.correct_preds.append(pred == actual)
            accuracy = (sum(self.correct_preds) / len(self.correct_preds)) *100
            self.wait_for_space(
                f"Prediction = {pred}\nActual label = {actual}\n\nOverall accuracy = {round(accuracy,2)}%\n\nPress space to continue")
            

    def generate_image_stim(self, path):
        stim = visual.ImageStim(self.window, image=path)
        aspect = stim.size[0]/stim.size[1]
        # This unit is degrees from center of screen.
        stim.size = [10*aspect, 10]
        return stim

    def _init_experiment(self):
        '''Write instruction text and wait for space bar press. '''
        instruction_text = f"""
Welcome to the live demo for object vs face prediction

Focus your attention on the following {len(self.stimImg)} images.

Press spacebar to continue.
Press ctrl+C to quit."""

        self.wait_for_space(instruction_text)
        # wait a tiny bit before continuing to allow user to get hand away from spacebar.
        core.wait(0.4)

    def wait_for_space(self, text):
        self.stimObj.text = text # Set text
        self.stimObj.alignText = 'left'
        self.window.flip()  # Show text on screen

        while 'space' not in event.getKeys():  # Wait for spacebar.
            core.wait(0.1)

        self.stimObj.text = ''  # Remove text
        self.stimObj.alignText = 'center'
        self.window.flip()

    def _run_experiment(self):
        ''' 
        Run the MI experiment
        Push markers to LSL stream. 
        '''

        port = self.i_status_updates
        for (i, (mark, image)) in enumerate(self.stimImg):

            if i == 25:
                self.wait_for_space("pause, press space to continue")

            marker = ['stimuli_marker', mark]
            image.draw()
            # Timestamp for showing stimuli (Should be as close to window.flip() as possible)
            timestamp = time()
            self.window.flip()  # Show stimuli

            # push marker to outlet.
            self.stream_outlet.push_sample(marker, timestamp)

            core.wait(self._soa)  # Show stimuli for this time

            self.stimObj.text = ''  # Remove stimuli
            self.window.flip()

            # Wait a bit between stimuli
            core.wait(self._iti + self.rng.random() * self._jitter)

            if 'q' in event.getKeys():  # quit psychopy with q (useful if class is run outside timeflux. )
                self.stimObj.text = 'Quitting'

                self.window.flip()
                core.quit()
        #EXPERIMENT DONE
        self.status = FITTING

    

    def terminate(self):
        '''
        Called by timeflux when closing down
        '''
        self.window.close()
        # TODO - there is an ugly error when closing down due to the LSL stream being closed, I don't know what to do about it. It works but is ugly.


if __name__ == '__main__':
    n = MyPsychopyNode()
