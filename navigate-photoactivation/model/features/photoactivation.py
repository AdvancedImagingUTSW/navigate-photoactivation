# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import traceback
import time

# Third Party Imports
import nidaqmx
import nidaqmx.constants
import nidaqmx.task
import numpy as np

# Local Imports


class Photoactivation:
    """Photoactivation feature.

    Note
    ----
        For the config_table, the need_response parameter if set to True requires
        an image to be received by the camera before proceeding. If set to False,
        the feature will proceed without waiting for an image to be received.

    Note
    ----
        One-step indicates that the sequence will only be run once. A good example
        of one-step is snap-image, whereas z-stack is a good example of a multi-step
        feature. Multi-step functions always calls the end-func to see if all of the
        signals have been delivered.
    """

    def __init__(self, model, *args):
        """Initialize the feature.

        Parameters
        ----------
        model : Model
            The navigate Model instance.
        """
        #: dict: The configuration table for execution of the feature.
        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "main": self.in_func_signal,
                "cleanup": self.cleanup_func_signal,
            },
            "node": {
                "node_type": "one-step",
                "device_related": True,
                "need_response": False,
            },
        }

        #: Model: The navigate Model instance.
        self.model = model

        #: str: The type of stimulation. Currently only "point" is supported.
        self.pattern = "point"

        #: float: The offset of the photoactivation event in microns in the x direction.
        self.location_x = None

        #: float: The offset of the photoactivation event in microns in the y direction.
        self.location_y = None

        #: int: The laser wavelength
        self.wavelength = None

        #: str: The pinout for the laser switching galvo.
        self.laser_port_switcher = None

        #: str: The trigger for the photoactivation. Delivers TTL.
        self.photoactivation_trigger = None

        #: str: The trigger source for the DAQ. Receives TTL.
        self.photoactivation_source = None

        #: nidaqmx.Task: The master trigger task for the DAQ.
        self.photoactivation_trigger_task = None

        #: nidaqmx.Task: The digital output task for switching lasers.
        self.switch_task = None

        #: str: The pinout for the x galvo.
        self.x_pinout = None

        #: nidaqmx.Task: The analog output task for the x & y galvos.
        self.galvo_task = None

        #: float: The volts per micron for the x galvo.
        self.x_scaling_factor = None

        #: str: The pinout for the y galvo.
        self.y_pinout = None

        #: float: The volts per micron for the y galvo.
        self.y_scaling_factor = None

        #: int: The duration in milliseconds of the photoactivation.
        self.duration = None

        #: int: The number of samples for the photoactivation.
        self.n_samples = None

        #: float: The percentage laser power.
        self.laser_power = None

    def get_photoactivation_parameters(self):
        """Get the photoactivation parameters from the configuration."""
        # Galvo and laser switching pinouts.
        self.x_pinout = self.model.configuration["experiment"]["Photoactivation"]["x_pinout"]
        self.y_pinout = self.model.configuration["experiment"]["Photoactivation"]["y_pinout"]
        self.laser_port_switcher = self.model.configuration["experiment"]["Photoactivation"]["laser_port_switcher"]
        self.y_scaling_factor = self.model.configuration["experiment"]["Photoactivation"]["y_scaling_factor"]
        self.x_scaling_factor = self.model.configuration["experiment"]["Photoactivation"]["x_scaling_factor"]
        self.laser_power = self.model.configuration["experiment"]["Photoactivation"]["laser_power"]
        self.duration = self.model.configuration["experiment"]["Photoactivation"]["duration"]
        self.pattern = self.model.configuration["experiment"]["Photoactivation"]["pattern"]
        self.wavelength = self.model.configuration["experiment"]["Photoactivation"]["wavelength"]
        self.location_x = self.model.configuration["experiment"]["Photoactivation"]["location_x"]
        self.location_y = self.model.configuration["experiment"]["Photoactivation"]["location_y"]
        self.photoactivation_trigger = self.model.configuration["experiment"]["Photoactivation"]["photoactivation_trigger"]
        self.photoactivation_source = self.model.configuration["experiment"]["Photoactivation"]["photoactivation_source"]

    def prepare_laser_switching_task(self):
        """Prepare the laser switching task."""
        if not hasattr(self.model.active_microscope.daq, 'laser_switching_task'):
            create_task = True
        else:
            if self.model.active_microscope.daq.laser_switching_task is None:
                create_task = True
            else:
                create_task = False

        if create_task:
            self.switch_task = nidaqmx.Task(new_task_name='Laser Switching Task')
            self.switch_task.do_channels.add_do_chan(
                self.laser_port_switcher,
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES,
            )
        else:
            self.switch_task = self.model.active_microscope.daq.laser_switching_task
        self.switch_task.write(True, auto_start=True)
        time.sleep(0.1)

    def prepare_photoactivation_trigger_task(self):
        """Prepare the photoactivation trigger."""
        if self.photoactivation_trigger_task is None:
            self.photoactivation_trigger_task = nidaqmx.Task(
                new_task_name="Photoactivation Trigger"
            )
            self.photoactivation_trigger_task.do_channels.add_do_chan(
                self.photoactivation_trigger,
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES,
            )

    def prepare_galvo_tasks(self):
        """Prepare the galvo tasks for the photoactivation feature.

        Logic assumes that the tasks are not used for any standard navigate
        operations. If in the future they are shared with a standard navigate feature,
        such as the galvo, the logic will need to be updated to handle the shared
        tasks.

        The location_x and location_y values are absolute distances from the center of
        the image. The plugin uses the Volts per Micron - X and Volts per Micron - Y
        parameters to calculate the offset in volts necessary.

        # TODO: Assumes beam is perfectly aligned in the center of the beam.
                In reality, the offsets will need offsets.

        """
        # Calculate number of samples necessary for the duration of the photoactivation.
        sample_rate = self.model.active_microscope.daq.sample_rate
        self.n_samples = int(self.duration / 1000 * sample_rate)

        # Create analog output tasks for the x and y galvos.
        if self.galvo_task is None:
            self.galvo_task = nidaqmx.Task(new_task_name="X & Y Galvo - Photoactivation")
            self.galvo_task.ao_channels.add_ao_voltage_chan(self.x_pinout)
            self.galvo_task.ao_channels.add_ao_voltage_chan(self.y_pinout)
            self.galvo_task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan=self.n_samples,
            )

        # Location values are in microns from center of the image.
        x_voltage_offset = self.location_x * self.x_scaling_factor
        y_voltage_offset = self.location_y * self.y_scaling_factor

        # TODO: Should make sure that the values are between the min and max voltage.

        if self.pattern == "Point":
            x_waveform = np.hstack([x_voltage_offset] * self.n_samples)
            y_waveform = np.hstack([y_voltage_offset] * self.n_samples)
        elif self.pattern == "square":
            raise NotImplementedError
        elif self.pattern == "circle":
            raise NotImplementedError

        # 2 channels worth of waveforms.
        waveforms = np.vstack([x_waveform, y_waveform]).squeeze()

        # 1 channel worth of tasks.
        self.galvo_task.write(waveforms)
        self.galvo_task.triggers.start_trigger.cfg_dig_edge_start_trig(self.photoactivation_source)
        self.galvo_task.triggers.start_trigger.retriggerable = False
        self.galvo_task.start()

    def pre_func_signal(self):
        """Prepare the signal thread to run this feature.

        The photoactivation feature will take a position in the image, calculate the
        offset necessary to move the galvos to that position in X and Y, trigger the
        laser switching galvo and the image flipping mirror.
        """
        self.model.active_microscope.daq.stop_acquisition()
        self.get_photoactivation_parameters()
        self.prepare_laser_switching_task()
        self.prepare_photoactivation_trigger_task()
        self.prepare_galvo_tasks()

    def trigger_photoactivation_laser(self):
        """Turn on the laser for photoactivation.

        Sets the laser power and turns on the laser.
        """
        self.model.active_microscope.lasers[str(self.wavelength).rstrip("nm")].set_power(self.laser_power)
        self.model.active_microscope.lasers[str(self.wavelength).rstrip("nm")].turn_on()

    def perform_photoactivation(self):
        """Trigger the galvo tasks for the photoactivation feature.

        Only trigger the galvos and the laser. Do not trigger any other hardware. To do this, we use a separate trigger
        source than the master trigger.
        """
        self.photoactivation_trigger_task.write([False, True, True, True, False], auto_start=True)
        self.galvo_task.wait_until_done()

    def in_func_signal(self):
        """Turn on the lasers, perform the photoactivation, turn off the lasers."""
        self.trigger_photoactivation_laser()
        self.perform_photoactivation()
        self.model.active_microscope.lasers[str(self.wavelength).rstrip("nm")].turn_off()

    def cleanup_tasks(self):
        """Cleanup the tasks.

        The laser switching task is left open for subsequent use by navigate.
        """
        self.galvo_task.stop()
        self.galvo_task.close()
        self.switch_task.write(False, auto_start=True)
        self.switch_task.stop()
        self.photoactivation_trigger_task.stop()
        self.photoactivation_trigger_task.close()

    def cleanup_func_signal(self):
        """Cleanup. Called after the features are done, or if there is an error."""
        self.cleanup_tasks()
