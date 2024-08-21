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

# Third Party Imports
import nidaqmx
import nidaqmx.constants
import nidaqmx.task

# Local Imports


class Photoactivation:
    """Photoactivation feature"""

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
                "end": self.end_func_signal,
                "cleanup": self.cleanup_func_signal,
            },
            "data": {
                "init": self.pre_func_data,
                "main": self.in_func_data,
                "end": self.end_func_data,
                "cleanup": self.cleanup_func_data,
            },
            "node": {
                "node_type": "multi-step",  # "multi-step" or "one-step"
                "device_related": True,  # True or False
                "need_response": True,  # True or False
            },
        }

        #: Model: The navigate Model instance.
        self.model = model

        #: str: The type of stimulation. Currently only "point" is supported.
        self.stimulation_type = "point"

        #: float: The offset of the photoactivation event in microns in the x direction.
        self.location_x = None

        #: float: The offset of the photoactivation event in microns in the y direction.
        self.location_y = None

        #: int: The laser wavelength
        self.laser_wavelength = None

        #: str: The pinout for the laser switching galvo.
        self.switching_port = None

        #: str: The trigger source for the DAQ.
        self.trigger_source = None

        #: nidaqmx.Task: The digital output task for switching lasers.
        self.switch_task = None

        #: str: The pinout for the x galvo.
        self.pinout_x = None

        #: nidaqmx.Task: The analog output task for the x galvo.
        self.task_x = None

        #: float: The volts per micron for the x galvo.
        self.volts_per_micron_x = None

        #: str: The pinout for the y galvo.
        self.pinout_y = None

        #: nidaqmx.Task: The analog output task for the y galvo.
        self.task_y = None

        #: float: The volts per micron for the y galvo.
        self.volts_per_micron_y = None

        #: int: The duration in milliseconds of the photoactivation.
        self.duration = None

        #: int: The number of samples for the photoactivation.
        self.n_samples = None

        #: float: The percentage laser power.
        self.percent_laser_power = None

    def get_photoactivation_parameters(self):
        """Get the photoactivation parameters from the configuration."""
        microscope_name = self.model.active_microscope.name

        # Galvo and laser switching pinouts.
        self.pinout_x = self.model.configuration["experiment"]["Photoactivation"][
            "x_pinout"
        ]
        self.pinout_y = self.model.configuration["experiment"]["Photoactivation"][
            "y_pinout"
        ]
        self.switching_port = self.model.configuration["experiment"]["Photoactivation"][
            "laser_switch"
        ]

        # Trigger source for the DAQ.
        self.trigger_source = self.model.configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        # Duration of the photoactivation.
        self.duration = self.model.configuration["experiment"]["Photoactivation"][
            "duration"
        ]

        # Stimulation laser wavelength and power.
        self.laser_wavelength = self.model.configuration["experiment"][
            "Photoactivation"
        ]["laser"]
        self.percent_laser_power = self.model.configuration["experiment"][
            "Photoactivation"
        ]["power"]

        # Stimulation pattern.
        self.stimulation_type = self.model.configuration["experiment"][
            "Photoactivation"
        ]["pattern"]

        # Stimulation position.
        self.location_x = self.model.configuration["experiment"]["Photoactivation"][
            "location_x"
        ]
        self.location_y = self.model.configuration["experiment"]["Photoactivation"][
            "location_y"
        ]

    def trigger_photoactivation_laser(self):
        """Turn on the laser for photoactivation.

        Sets the laser power and turns on the laser.
        """
        self.model.active_microscope.lasers[str(self.laser_wavelength)].set_power(
            self.percent_laser_power
        )

        self.model.active_microscope.lasers[str(self.laser_wavelength)].turn_on()

    def perform_photoactivation(self):
        """Trigger the galvo tasks for the photoactivation feature."""
        self.model.active_microscope.daq.master_trigger_task.write(
            [False, True, True, True, False], auto_start=True
        )
        for task in [self.task_x, self.task_y]:
            task.wait_until_done()
            task.stop()

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
        if self.task_x is None:
            self.task_x = nidaqmx.Task(new_task_name="X-Galvo - Photoactivation")
            self.task_x.ao_channels.add_ao_voltage_chan(self.pinout_x)
            self.task_x.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan=self.n_samples,
            )
            self.task_x.triggers.start_trigger.cfg_dig_edge_start_trig(
                self.trigger_source
            )
            self.task_x.register_done_event(None)

        if self.task_y is None:
            self.task_y = nidaqmx.Task(new_task_name="Y-Galvo - Photoactivation")
            self.task_y.ao_channels.add_ao_voltage_chan(self.pinout_y)
            self.task_y.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan=self.n_samples,
            )
            self.task_y.triggers.start_trigger.cfg_dig_edge_start_trig(
                self.trigger_source
            )
            self.task_y.register_done_event(None)

        x_voltage_offset = self.location_x * self.volts_per_micron_x
        y_voltage_offset = self.location_y * self.volts_per_micron_y

        if self.stimulation_type == "point":
            x_waveform = [x_voltage_offset] * self.n_samples
            y_waveform = [y_voltage_offset] * self.n_samples
        elif self.stimulation_type == "square":
            raise NotImplementedError
        elif self.stimulation_type == "circle":
            raise NotImplementedError

        self.task_x.write(x_waveform)
        self.task_y.write(y_waveform)

    def prepare_laser_switching_task(self):
        """Prepare the laser switching task.

        If the laser switching task is not already created, create it.
        """
        if self.model.active_microscope.daq.laser_switching_task is None:
            self.switch_task = nidaqmx.Task()
            self.switch_task.ao_channels.do_channels.add_do_chan(
                self.switching_port,
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES,
            )
        else:
            self.switch_task = self.model.active_microscope.daq.laser_switching_task
        self.switch_task.write(True, auto_start=True)

    def cleanup_laser_switching_task(self):
        """Cleanup the laser switching task."""
        self.switch_task.write(False, auto_start=True)
        if self.model.active_microscope.daq.laser_switching_task is None:
            self.switch_task.close()

    def pre_func_signal(self):
        """Prepare the signal thread to run this feature.

        The photoactivation feature will take a position in the image, calculate the
        offset necessary to move the galvos to that position in X and Y, trigger the
        laser switching galvo and the image flipping mirror.
        """
        self.get_photoactivation_parameters()
        self.prepare_laser_switching_task()
        self.prepare_galvo_tasks()
        return True

    def in_func_signal(self):
        """Turn on the lasers and perform the photoactivation."""

        self.trigger_photoactivation_laser()
        self.perform_photoactivation()
        return True

    def end_func_signal(self):
        """Turn off the lasers"""

        self.model.active_microscope.lasers[str(self.laser_wavelength)].turn_off()
        return True

    def cleanup_func_signal(self):
        """Cleanup"""
        self.cleanup_laser_switching_task()

    def pre_func_data(self):
        """Prepare data thread to run this feature"""
        pass

    def in_func_data(self, frame_ids):
        """Deal with images"""
        pass

    def end_func_data(self):
        """Decide if this feature ends"""
        pass

    def cleanup_func_data(self):
        """Cleanup"""
        pass
