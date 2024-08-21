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


class PhotoactivationController:
    def __init__(self, view, parent_controller=None):

        #: tk.Frame: The view for the plugin
        self.view = view

        #: Controller: The parent controller
        self.parent_controller = parent_controller

        #: dict: The variables from the view
        self.variables = self.view.get_variables()

        #: dict: The buttons from the view
        self.buttons = self.view.get_buttons()

        #: dict: The widgets from the view
        self.widgets = self.view.get_widgets()

        self.microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]

        self.configuration = self.parent_controller.configuration["configuration"][
            "microscopes"
        ]

        #: float: The offset in the x direction
        self.location_x = 0

        #: float: The offset in the y direction
        self.location_y = 0

        #: float: The volts per micron for the x galvo
        self.x_scaling_factor = 1

        #: float: The volts per micron for the y galvo
        self.y_scaling_factor = 1

        #: str: The pinout for the x galvo
        self.pinout_x = None

        #: str: The pinout for the y galvo
        self.pinout_y = None

        #: str: The pinout for the laser switch
        self.switch = None

        # Default location for communicating with the plugin in the model.
        self.parent_controller.configuration["experiment"]["Photoactivation"] = {}

        self.get_default_configuration()
        self.populate_widgets()
        self.set_menu_entries()
        self.configure_widget_events()

    def get_default_configuration(self):
        """Get the default configuration for the plugin"""
        # TODO: Retrieve the values from the plugin configuration file.
        self.pinout_x = "PCIE6738/ao0"
        self.pinout_y = "PCIE6738/ao1"

        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "x_pinout"
        ] = self.pinout_x
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "y_pinout"
        ] = self.pinout_y
        self.switch = self.configuration[self.microscope_name]["daq"][
            "laser_port_switcher"
        ]
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "laser_switch"
        ] = self.switch

        self.y_scaling_factor = 0.05
        self.x_scaling_factor = 0.05

        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "y_scaling_factor"
        ] = self.y_scaling_factor
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "x_scaling_factor"
        ] = self.x_scaling_factor

    def update_configuration(self, *args):
        """Retrieve values from GUI and update the experiment configuration.

        This function is called everytime the user changes a value in the GUI.
        """
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "laser"
        ] = int(self.widgets["Laser"].get().rstrip("nm"))
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "power"
        ] = float(self.widgets["Power"].get())
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "duration"
        ] = int(self.widgets["Duration (ms)"].get())
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "pattern"
        ] = str(self.widgets["Pattern"].get())
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "location_x"
        ] = float(self.widgets["Photoactivation Offset X"].get())
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "location_y"
        ] = float(self.widgets["Photoactivation Offset Y"].get())

    def populate_widgets(self):
        """Populate the default values for the widgets"""
        # Laser Wavelengths - "Laser"
        setting_dict = self.parent_controller.configuration_controller.channels_info
        self.widgets["Laser"]["values"] = setting_dict["laser"]
        self.widgets["Laser"].set(setting_dict["laser"][0])

        # Laser Switch - "Pinout - Laser Switch"
        self.widgets["Pinout - Laser Switch"].set(self.switch)

        # Laser Power - "Power"
        self.widgets["Power"].set(10)

        # Duration (ms) - "Duration"
        self.widgets["Duration (ms)"].set(10)

        # Pattern - "Pattern"
        self.widgets["Pattern"]["values"] = ["Point", "Square", "Circle"]
        self.widgets["Pattern"].set("Point")

        # Pin outs for Galvos
        self.widgets["Pinout - X Galvo"].set(self.pinout_x)
        self.widgets["Pinout - Y Galvo"].set(self.pinout_y)

        # Volts per Micron
        self.widgets["Volts per Micron - X"].set(self.x_scaling_factor)
        self.widgets["Volts per Micron - Y"].set(self.y_scaling_factor)

        # Photoactivation Offset
        self.widgets["Photoactivation Offset X"].set(self.location_x)
        self.widgets["Photoactivation Offset Y"].set(self.location_y)

    def configure_widget_events(self):
        """Add the event traces to the widgets."""
        self.widgets["Laser"].bind("<FocusOut>", self.update_configuration)
        self.widgets["Power"].bind("<FocusOut>", self.update_configuration)
        self.widgets["Duration (ms)"].bind("<FocusOut>", self.update_configuration)
        self.widgets["Pattern"].bind("<FocusOut>", self.update_configuration)

    def set_menu_entries(self):
        """Set the menu entries for the plugin in the view"""
        self.parent_controller.camera_view_controller.menu.add_command(
            label="Photoactivate Here", command=self.mark_position
        )

    def mark_position(self, *args):
        """Mark the current position of the microscope"""
        (
            self.location_x,
            self.location_y,
        ) = self.parent_controller.camera_view_controller.calculate_offset()

        # Update the offset values in the view
        self.widgets["Photoactivation Offset X"].set(self.location_x)
        self.widgets["Photoactivation Offset Y"].set(self.location_y)

        # Update the offset values in the configuration
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "location_x"
        ] = self.location_x
        self.parent_controller.configuration["experiment"]["Photoactivation"][
            "location_y"
        ] = self.location_y
