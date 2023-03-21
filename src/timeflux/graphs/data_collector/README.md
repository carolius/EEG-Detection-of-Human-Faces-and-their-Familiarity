# Demo of psychopy

The purpose of this demo is to:
- Show how psychopy works.
- Show how markers are sent over LSL.
- Show how data can be stored.
- Show how data is epoched based on markers.

Psychopy runs a stimuli program for a Motor Imagery experiment.
The EEG data is epoched and then saved through timeflux.


The image shows an overview of the setup.
Each subgraph (gray) is discussed in more detail below.

![Overview of example](main_demo_psychopy_1.png)


## PubSubBroker
The broker subgraph exchanges data between subgraphs.
Each transmitting graph has a publication node, and receiving graphs have a subscriber node.
The transmitting node sends data to a "topic" to which the subscriber subscribes.


## Receive LSL
The EEG headset is expected to send data over a LSL stream (Lab Streaming Layer) to which the 'eeg_LSL_receiver' node listens.
Markers from the stimuli program is also sent over a LSL stream to which the 'markers_LSL_receiver' node listens.
Both EEG data and Markers are sent to the broker.
The streaming of EEG data needs to be started separately (for Muse in a terminal window with `muselsl stream`).


## Monitor
The monitor graph shows the EEG signals in the timeflux web UI.
Events can be sent from the web UI as well.

**EEG raw:**
The monitor graph subscribes to raw EEG data from the broker.
It then shows this data in a web interface from timeflux UI.
It is useful to look at the web interface when adjusting the EEG headset to get a sense of the signal quality.

**Events:**
It is possible to send events from this web interface.
These are transmitted to the broker.
The events are not used in this example, but the functionality is there and ready for use.



## Processing graph
The process graph is where the EEG data is processed, in this case cut to epochs.
The functionality of each node is described below.

**sub-node:**
The subscribe node subscribes to the EEG data and events.

**epochs-node:**
Cut the data into epochs. The data is labeled based on the events.

**trim-node:**
Makes sure that all epochs are of the same size.

**pub_eeg_epochs-nodes:**
The publication nodes which sends the epoched data to the broker.


## PsychopyGraph
Runs the stimuli program created with psychopy and sends makers over LSL stream.
The experiment is a Motor Imagery experiment, meaning that the user should imagine moving their right or left hand depending on the prompt on the screen.

Psychopy has a window where 'right'/'left' is shown, indicating what arm to imagine moving.
The experiment is run forever in this demo and the right/left is randomly picked.

The following steps are done to show a stimuli for the user:
1. Randomly pick left/right
2. Create a marker that will be sent over LSL
3. Draw the stimuli text on the "back" of the psychopy window.
4. Get time now.
5. Flip the psychopy window to show the stimuli text.
6. Push the marker over LSL.
7. Wait while showing the stimuli.
8. Draw '' (=nothing) on the back of the psychopy window and flip the screen again.
9. Wait a bit before showing the next stimuli.




## Save graph
This graph saves the epoched data in hdf5 format.
There is an additional script showing how to open a hdf5 file (`read_saved_data.py`).
hdf5 files with recorded data can be used to replay a run in timeflux.
Read more in timeflux documentation for this.
