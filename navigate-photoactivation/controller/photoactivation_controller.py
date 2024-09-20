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


#  Standard Library Imports

# Third Party Imports

# Local Imports
from navigate.config import update_config_dict

class PhotoactivationController:
    """Controller for the Photoactivation Plugin"""

    def __init__(self, view, parent_controller=None):
        """Initialize the Photoactivation Controller

        Parameters
        ----------
        view : tk.Frame
            The view for the plugin
        parent_controller : Controller
            The parent controller
        """

        #: tk.Frame: The view for the plugin
        self.view = view

        #: Controller: The parent controller
        self.parent_controller = parent_controller

        #: dict: The variables from the view
        self.variables = self.view.get_variables()

        #: dict: The widgets from the view
        self.widgets = self.view.get_widgets()

        self.microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]

        #: float: The offset in the x direction
        self.location_x = None

        #: float: The offset in the y direction
        self.location_y = None

        #: float: The volts per micron for the x galvo
        self.x_scaling_factor = None

        #: float: The volts per micron for the y galvo
        self.y_scaling_factor = None

        #: str: The pinout for the x galvo
        self.pinout_x = None

        #: str: The pinout for the y galvo
        self.pinout_y = None

        #: str: The pinout for the laser switch
        self.switch = None

        #: str: The pinout for the photoactivation trigger
        self.photoactivation_trigger = None

        #: str: The pinout for the photoactivation source
        self.photoactivation_source = None

        #: float: The power of the laser
        self.laser_power = None

        #: str: The laser wavelength
        self.laser = None

        #: int: The duration of the photoactivation
        self.duration = None

        #: str: The pattern of the photoactivation
        self.pattern = None

        # Default location for communicating with the plugin in the model.
        if "Photoactivation" not in self.parent_controller.configuration["experiment"].keys():
            update_config_dict(self.parent_controller.manager,
                               self.parent_controller.configuration["experiment"],
                               "Photoactivation",
                               {}
                               )

        self.get_default_parameters()
        self.populate_widgets()
        self.set_widget_state()
        self.set_menu_entries()
        self.configure_widget_events()
        self.update_configuration()

    def get_default_parameters(self):
        """Get the default parameters for the plugin

        TODO: Retrieve the values from the configuration file.
        """
        # Pinouts
        self.pinout_x = "TIRF/ao0"
        self.pinout_y = "TIRF/ao1"
        self.photoactivation_trigger = "TIRF/port0/line0"
        self.photoactivation_source = "/TIRF/PFI5"

        # Galvo volts per micron scaling factors.
        self.x_scaling_factor = 0.05
        self.y_scaling_factor = 0.05

        # Default laser power
        self.laser_power = 10

        # Default photoactivation duration
        self.duration = 100

        # Default pattern of photoactivation
        self.widgets["Pattern"]["values"] = ["Point", "Square", "Circle"]
        self.pattern = "Point"

        # Laser wavelengths - Default to first value.
        setting_dict = self.parent_controller.configuration_controller.channels_info
        self.widgets["Laser"]["values"] = setting_dict["laser"]
        self.laser = setting_dict["laser"][0]

        # Laser switching port
        # self.switch = self.parent_controller.configuration["configuration"][
        #     "microscopes"
        # ][self.microscope_name]["daq"]["laser_port_switcher"]
        self.switch = "TIRF/port1/line2"

        # Default location for photoactivation
        self.location_y = 0
        self.location_x = 0

    def populate_widgets(self):
        """Populate the default values for the widgets"""
        self.widgets["Laser"].set(self.laser)
        self.widgets["Pinout - Laser Switch"].set(self.switch)
        self.widgets["Power"].set(self.laser_power)
        self.widgets["Duration (ms)"].set(self.duration)
        self.widgets["Pattern"].set(self.pattern)
        self.widgets["Pinout - X Galvo"].set(self.pinout_x)
        self.widgets["Pinout - Y Galvo"].set(self.pinout_y)
        self.widgets["Volts per Micron - X"].set(self.x_scaling_factor)
        self.widgets["Volts per Micron - Y"].set(self.y_scaling_factor)
        self.widgets["Photoactivation Offset X"].set(self.location_x)
        self.widgets["Photoactivation Offset Y"].set(self.location_y)

    def set_widget_state(self):
        """Set the state of the widgets in the view.

        Active widgets include the laser, power, pattern, and duration.
        Inactive widgets include the pinouts, scaling factors, and offsets."""
        for key in [
            "Pinout - X Galvo",
            "Pinout - Y Galvo",
            "Pinout - Laser Switch",
            "Photoactivation Offset X",
            "Photoactivation Offset Y",
            "Volts per Micron - X",
            "Volts per Micron - Y",
        ]:
            self.widgets[key].configure(state="disabled")

        self.widgets["Laser"].configure(state="readonly")
        self.widgets["Pattern"].configure(state="readonly")
        self.widgets["Power"].configure(state="normal", from_=0, to=100, increment=1)
        self.widgets["Duration (ms)"].configure(
            state="normal", from_=0, to=10000, increment=1
        )

    def set_menu_entries(self):
        """Set the menu entries for the plugin in the view"""
        self.parent_controller.camera_view_controller.menu.add_command(
            label="Photoactivate Here", command=self.mark_position
        )

    def configure_widget_events(self):
        """Add the event traces to the widgets."""
        self.widgets["Laser"].bind("<<ComboboxSelected>>", self.update_configuration)
        self.widgets["Pattern"].bind("<<ComboboxSelected>>", self.update_configuration)
        self.widgets["Power"].bind("<FocusOut>", self.update_configuration)
        self.widgets["Duration (ms)"].bind("<FocusOut>", self.update_configuration)

    def update_configuration(self, *args):
        """Retrieve values from GUI and update the experiment configuration.

        This function is called everytime the user changes a value in the GUI.
        """
        self.laser = int(self.widgets["Laser"].get().rstrip("nm"))
        self.laser_power = float(self.widgets["Power"].get())
        self.duration = int(self.widgets["Duration (ms)"].get())
        self.pattern = str(self.widgets["Pattern"].get())
        self.location_x = float(self.widgets["Photoactivation Offset X"].get())
        self.location_y = float(self.widgets["Photoactivation Offset Y"].get())

        # Update the Proxy Dict
        self.parent_controller.configuration["experiment"]["Photoactivation"]["wavelength"] = self.laser
        self.parent_controller.configuration["experiment"]["Photoactivation"]["laser_power"] = self.laser_power
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "duration"
        ] = self.duration
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "pattern"
        ] = self.pattern
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "location_x"
        ] = self.location_x
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "location_y"
        ] = self.location_y
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "x_pinout"
        ] = self.pinout_x
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "y_pinout"
        ] = self.pinout_y
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "laser_port_switcher"
        ] = self.switch
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "photoactivation_trigger"
        ] = self.photoactivation_trigger
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "photoactivation_source"
        ] = self.photoactivation_source
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "y_scaling_factor"
        ] = self.y_scaling_factor
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "x_scaling_factor"
        ] = self.x_scaling_factor

    def mark_position(self, *args):
        """Mark the current position of the microscope"""
        (
            self.location_x,
            self.location_y,
        ) = self.parent_controller.camera_view_controller.calculate_offset()

        # Update the offset values in the view
        self.widgets["Photoactivation Offset X"].set(self.location_x)
        self.widgets["Photoactivation Offset Y"].set(self.location_y)
        self.update_configuration()
