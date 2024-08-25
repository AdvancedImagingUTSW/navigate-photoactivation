<h1 align="center">
navigate-photoactivation

<h2 align="center">
	Event-Driven Photoactivation.
</h2>
</h1>


**navigate-photoactivation** is a plugin for
[navigate](https://github.com/TheDeanLab/navigate), the open-source Python package
designed for the control of  light-sheet microscopes. **navigate** offers easily
reconfigurable hardware setups  and automated acquisition routines, making it a
powerful tool for advanced imaging techniques.

With **navigate-photoactivation**, users can perform targeted photo-stimulation of
optogenetic biosensors, execute localization microscopy routines, and conduct
fluorescence recovery after photobleaching (FRAP) and photo-switching experiments.
The plugin allows these processes to be performed in response to user-specified
criteria, enhancing the flexibility and precision of your imaging experiments.

## Quick Install
To get started, follow these steps:

1. Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
2. Create a new environment and activate it:

   ```bash
   conda create -n navigate python=3.9.7
   conda activate navigate
   pip install navigate-micro navigate-photoactivation
   navigate
   ```

## Design
**navigate-photoactivation** is designed to operate as a feature in **navigate**.
Currently, it performs photoactivation by raster scanning a region of interest (ROI)
with two linear galvanometer mirrors. The user specifies the location where
photoactivation should occur by right-clicking on the image and selecting
'Photoactivate Here'. Photoactivation can be triggered by a variety of events, can
be performed in point, square, circular, and user-specific shapes, and can be
repeated at user-defined intervals.

## Requirements
Currently, only designed to work with National Instrument's based data acquisition
cards and linear galvanometers.

## Documentation
To learn more about **navigate** and **navigate-photoactivation**, please refer to the
[documentation](https://thedeanlab.github.io/navigate/).
