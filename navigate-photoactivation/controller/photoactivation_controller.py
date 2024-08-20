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

        self.microscope_name = self.parent_controller.configuration[
            "experiment"]["MicroscopeState"]["microscope_name"]

        self.configuration = self.parent_controller.configuration[
            "configuration"]["microscopes"]

        #: float: The offset in the x direction
        self.offset_x = 0

        #: float: The offset in the y direction
        self.offset_y = 0

        self.populate_widgets()
        self.set_menu_entries()

        # Tkinter Events
        self.buttons["execute"].configure(command=self.move)

    def populate_widgets(self):
        """Populate the default values for the widgets """
        # Laser Wavelengths - "Laser"
        setting_dict = self.parent_controller.configuration_controller.channels_info
        self.widgets["Laser"]["values"] = setting_dict["laser"]
        self.widgets["Laser"].set(setting_dict["laser"][0])

        # Laser Switching - "Pinout - Laser Switch"
        switch = self.configuration[self.microscope_name]["daq"]["laser_port_switcher"]
        self.widgets["Pinout - Laser Switch"].set(switch)

        # Laser Power - "Power"
        self.widgets["Power"].set(10)

        # Duration (ms) - "Duration"
        self.widgets["Duration (ms)"].set(10)

        # Pattern - "Pattern"
        self.widgets["Pattern"]["values"] = ["Point", "Square", "Circle"]
        self.widgets["Pattern"].set("Point")

        # Pinouts for Galvos TODO: Add as plugin configuration entry
        self.widgets["Pinout - X Galvo"].set("PCIE6738/ao0")
        self.widgets["Pinout - Y Galvo"].set("PCIE6738/ao1")

        # Volts per Micron TODO: Add as plugin configuration entry
        self.widgets["Volts per Micron - X"].set(0.05)
        self.widgets["Volts per Micron - Y"].set(0.05)

        # Photoactivation Offset
        self.widgets["Photoactivation Offset X"].set(self.offset_x)
        self.widgets["Photoactivation Offset Y"].set(self.offset_y)

    def set_menu_entries(self):
        """Set the menu entries for the plugin in the view"""
        self.parent_controller.camera_view_controller.menu.add_command(
            label="Photoactivate Here", command=self.mark_position)

    def move(self, *args):
        """Example function to move the plugin device"""
        print("*** Move button is clicked!")
        #self.parent_controller.execute("move_plugin_device", self.variables[
        # "plugin_name"].get())

    def mark_position(self, *args):
        """Mark the current position of the microscope"""
        self.offset_x, self.offset_y = (
            self.parent_controller.camera_view_controller.calculate_offset()
        )
        self.widgets["Photoactivation Offset X"].set(self.offset_x)
        self.widgets["Photoactivation Offset Y"].set(self.offset_y)

        #self.parent_controller.execute("mark_position")

    