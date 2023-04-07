# Detection of Human Faces and their Familiarity

This project sets out to detect whether a face, displayed on a screen in front of the test subject, is familiar or not-familiar by using the EEG signals recorded from a Muse-S. The Muse-S has four electrodes, two temporal and two frontal (TP9, TP10 and AF7, AF8 respectively) and can be connected wirelessly via bluetooth. Another experiement involving the detection of images including a human face from those without a human face is also explored. 

In this repository you will find all the information and code necessary to run your own EEG experiment. This is the easiest way to ensure you have all the 
necessary dependancies to run the project, detailed instructions on how to set up a new conda environment are provided so that everything will run smoothly.

### First time setup:
1. Clone this git repository into a fresh directory.

2. If using conda, first create a new environment (here it is called bci3.7 since it uses python 3.7) and activate it. 

        conda create -n "bci3.7" python==3.7 git pip wxpython
        
        conda activate bci3.7

    Next clone the `eeg-notebooks` repository, using it to inform pip of all the packages needed.
           
        git clone https://github.com/NeuroTechX/eeg-notebooks
        
        cd eeg-notebooks
        
        pip install -e .

    Finally you need to install `timeflux` `timeflux-ui` `timeflux-dsp` and `liblsl`. 

        pip install timeflux

    This might return the following error message:
    >ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
    This behaviour is the source of the following dependency conflicts.
    muselsl 2.2.0 requires pylsl==1.10.5, but you have pylsl 1.15.0 which is incompatible.
    >

    To resolve this revert back to an earlier version of `timeflux`.

        pip install timeflux=0.10.1
        conda install -c conda-forge liblsl
        pip install timeflux-ui
        pip install timeflux-dsp

3. Link the `nodes_dev` folder and the `timeflux` installation with a symbolic link. 
    
        (linux)    
        ln -s ~/<path/to/repo>/group-b/src/timeflux/nodes_dev/ ~/miniconda3/envs/bci3.8/lib/python3.8/site-packages/timeflux
        
        (windows)
        mklnk /D C:\Users\<username>\miniconda3\envs\<envName>\Lib\site-packages\timeflux\nodes_dev C:\<path\to\repo>\group-b\src\timeflux\nodes_dev

### Collecting data:
First start the muselsl stream in a new terminal window using one of the commands below. This does not require being in a specific directory since `muselsl` should be attached to `PATH`. 

    muselsl stream
    muselsl stream -a 00:55:DA:BB:58:BE     #skip search for device
    muselsl stream -a 00:55:DA:BB:58:BE -b bgapi    #if using different backend

Activate the conda environment you created during the first time setup in your main terminal window. 

    conda activate bci3.7

Navigate the directory to the following folder `src\timeflux\graphs\data_collector\` and run one of the following commands;

    timeflux main_data_collector_FnF.yaml
    timeflux main_data_collector_FnF.yaml -d #debug
    timeflux main_data_collector_FnF.yaml -e SESSION="<name>" -e SUBJECT="<name>"  #sending parameters

If timeflux is exectuted from folder containing the yaml file data is saved at src/timeflux/data/

### Predicting in real time:
The live demo can be run by moving to the directory `scr\timeflux\graphs\live_demo\`. Once there, simply run the following command;

    timeflux main_live_demo.yaml

This application first display a series of images in order to generate a training dataset. Once collected, the ML model is trained, transitioning into the prediction phase.
For each subsequent image the application records the signal and makes a prediction about the class of the image displayed. Classification accuracy is reported as an average.

### Familiar Face Dataset
All'familiar-face' datasets have been removed for privacy reasons. If you wish to replicate this experiment feel free to upload your own folder of images to the same directory and update the psychopy file `rt_psychopy.py` found in `src\timeflux\nodes_dev`

Under the __init__() method in this file you can change the folder name to match the new folder you have added.

    class_1 = "Marcus Faces"
    class_2 = "non-face images"
    self.img_from_each_class = 5

Make sure that twice the amount of `self.img_from_each_class` is in each folder as the program creates a trainining and validation dataset.
