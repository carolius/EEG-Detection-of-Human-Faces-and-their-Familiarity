"""This module has nodes for psychopy with Timeflux."""

"""I have placed this in the timeflux_ui/nodes path. """


# Statuses in ml node.

from pathlib import Path
import signal
import os
import sys
from multiprocessing.managers import BaseManager
from multiprocessing import Process, Manager
import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event
from timeflux.core.node import Node
from timeflux.nodes_dev.helpers import get_data
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop
from time import time, sleep
import random
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
    Runs a Motor imagery experiment forever. 
    '''

    def __init__(self):

        # Create LSL outlet stream.
        self.stream_outlet = MarkerStreams()

        # Create psychopy windows and text objects.
        self.window = visual.Window(
            [900, 1000], monitor="testMonitor", units="deg", fullscr=True)
        self.stimObj = visual.TextStim(
            win=self.window, text="", color=[-1, -1, -1])
        self.stimObj.autoDraw = True  # Text is drawn on all flips.
        # get root path of git repo
        self.root_path = next(
            filter(lambda p: p.name == "group-b", Path.cwd().parents))
        self.datasets_path = self.root_path / "datasets"

        #self.nonfaces_generator = (map(self.generate_image_stim, (self.datasets_path/"non-face images").glob("*")))
        #self.faces_generator = (map(self.generate_image_stim, (self.datasets_path/"Amins familiar faces").glob("*")))
        faces = [("face", self.generate_image_stim(path))
                 for path in (self.datasets_path/"marcus faces").glob("*")][0:25]
        self.stimImg = [("object", self.generate_image_stim(path)) for path in (
            self.datasets_path/"non-face images").glob("*")][0:25] + faces
        random.shuffle(self.stimImg)

        # Show infotext on screen
        self._init_experiment()

        # Run experiment
        self._run_experiment()

    def generate_image_stim(self, path):
        stim = visual.ImageStim(self.window, image=path)
        aspect = stim.size[0]/stim.size[1]
        # This unit is degrees from center of screen.
        stim.size = [10*aspect, 10]
        return stim

    def _init_experiment(self):
        '''Write instruction text and wait for space bar press. '''
        instruction_text = """
Welcome to the Human-Face ERP Experiment

Focus your attention on the following images.

Press spacebar to continue.
Press ctrl+C to quit."""

        self.stimObj.text = instruction_text  # Set text
        self.stimObj.alignText = 'left'
        self.window.flip()  # Show text on screen

        while 'space' not in event.getKeys():  # Wait for spacebar.
            core.wait(0.1)

        self.stimObj.text = ''  # Remove text
        self.stimObj.alignText = 'center'
        self.window.flip()

        # Wait a tiny bit before continuing to allow user to get hand away from spacebar.
        core.wait(0.4)

    def _run_experiment(self):
        ''' 
        Run the MI experiment
        Push markers to LSL stream. 
        '''

        _iti = 0.0     # Inter trial interval - time between stimuli
        _soa = 0.6     # Stimulu onset asynchrony - time stimuli is shown
        _jitter = 0.2  # Noise/unpredicted time between stimuli.

        # Random generator
        rng = np.random.default_rng()

        for (i, (mark, image)) in enumerate(self.stimImg):

            if i == 25:
                self.stimObj.text = "pause, press space to continue"  # Set text
                self.stimObj.alignText = 'left'
                self.window.flip()  # Show text on screen

                while 'space' not in event.getKeys():  # Wait for spacebar.
                    core.wait(0.1)

                self.stimObj.text = ''  # Remove text
                self.stimObj.alignText = 'center'
                self.window.flip()

            marker = ['stimuli_marker', mark]
            image.draw()
            
            # Timestamp for showing stimuli (Should be as close to window.flip() as possible)
            timestamp = time()
            self.window.flip()  # Show stimuli

            # push marker to outlet.
            self.stream_outlet.push_sample(marker, timestamp)
            core.wait(_soa)  # Show stimuli for this time

            self.stimObj.text = ''  # Remove stimuli
            self.window.flip()

            # Wait a bit between stimuli
            core.wait(_iti + rng.random() * _jitter)

            if 'q' in event.getKeys():  # quit psychopy with q (useful if class is run outside timeflux. )
                self.stimObj.text = 'Quitting'

                self.window.flip()
                core.quit()

        core.quit()

    def update(self):
        """
        Called by timeflux in each iteration.
        """
        pass  # No input to react to in this example.

    def terminate(self):
        '''
        Called by timeflux when closing down
        '''
        self.window.close()
        # TODO - there is an ugly error when closing down due to the LSL stream being closed, I don't know what to do about it. It works but is ugly.


if __name__ == '__main__':
    n = MyPsychopyNode()
