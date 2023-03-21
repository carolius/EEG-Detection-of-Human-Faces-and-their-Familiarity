"""timeflux.nodes_dev.push_events"""



# A node that publishes data

import numpy as np
import signal
import pandas as pd
import timeflux.helpers.clock as clock
import sys
import os
import time
import warnings
from time import time,sleep
from timeflux.core.exceptions import WorkerInterrupt, WorkerLoadError
from timeflux.core.node import Node
from pandas import DataFrame
from pylsl import StreamInfo, StreamOutlet, StreamInlet

class Push(Node):
    """Push Event.

    Simple example node for pushing event. Only used as an exampel for student at the moment.
    This was/is originally embedded into the psychopy nodes where events are created.
    THIS IS ESSENTIALLY DOING THE SAME AS the "class Send(Node)" in nodes_dev/lsl.py

    Creates a marker with 2 channels. Each marker sent with a timestamp adn have
    the following structure:

                --------------------------------
                |   label      |   data        |
    --------------------------------------------
    'timestamp' |   'ID'       |   'PAYLOAD'   |
    --------------------------------------------


    Args:
        label (string): Name of the event that will trigger the Epoch.

    """

    def __init__(self, event_trigger=None):

        self._event_trigger = str(event_trigger)
        nbrChannels = 2
        typeChannels = "string"
        channel_names = ["label", "data"]
        ch_units = {"label":"misc","data":"misc"}
        ch_types = {"label":"marker","data":"marker"}

         # Create info about stream
        _marker_StreamInfo = StreamInfo(
        name="MarkersPsychopy",
        type="Markers",
        channel_count = nbrChannels,
        nominal_srate = 0,
        channel_format = typeChannels,
        source_id = "MarkersPsychopyNode")

        # Set names on the chanels
        chns = _marker_StreamInfo.desc().append_child("channels")
        for label in channel_names:
            ch = chns.append_child("channel")
            ch.append_child_value("label", label)
            ch.append_child_value("unit", ch_units[label]) # Is this correct value?
            ch.append_child_value("type", ch_types[label]) # Is this correct value?

        # Create outlet
        self._marker_StreamOutlet = StreamOutlet(_marker_StreamInfo)

        """
        # Push outlet
        n = 1
        #_n_stimuli = 5 #trials?
        #array=np.random.randint(0,5,_n_stimuli)
        marker = [self._event_trigger,str(n)]
        #marker = ["start_epoching",str(n)]
        timestamp = time()
        self._marker_StreamOutlet.push_sample(marker, timestamp)
        """

        #self.logger.debug("Push_events: at least I tried")

    # The update() function executed in the same rate as the graph containing it.
    def update(self):

        # Push outlet
        n = 1
        #_n_stimuli = 5 #trials?
        #array=np.random.randint(0,5,_n_stimuli)
        markers = [self._event_trigger, str(n)]
        timestamp = time()
        self._marker_StreamOutlet.push_sample(markers, timestamp)
        #self.logger.debug("Push_events: at least I tried (again)")
