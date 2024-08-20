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
import os
from pathlib import Path

# Third Party Imports

# Local Imports

# Standard Imports
from navigate.tools.common_functions import load_module_from_file
from navigate.model.device_startup_functions import device_not_found


DEVICE_TYPE_NAME = "plugin_device"  # Same as in configuraion.yaml, for example "stage", "filter_wheel", "remote_focus_device"...
DEVICE_REF_LIST = ["type"]  # the reference value from configuration.yaml


def load_device(hardware_configuration, is_synthetic=False):
    """Build device connection.

    Parameters
    ----------
    hardware_configuration : dict
        device hardware configuration section
    is_synthetic : bool
        use synthetic hardware

    Returns
    -------
    device_connection : object
    """
    return type("DeviceConnection", (object,), {})


def start_device(microscope_name, device_connection, configuration, is_synthetic=False):
    """Start device.

    Parameters
    ----------
    microscope_name : string
        microscope name
    device_connection : object
        device connection object returned by load_device()
    configuration : dict
        navigate configuration
    is_synthetic : bool
        use synthetic hardware

    Returns
    -------
    device_object : object
    """
    if is_synthetic:
        device_type = "synthetic"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "plugin_device"
        ]["hardware"]["type"]

    if device_type == "PluginDevice":
        # install through navigate
        plugin_device = load_module_from_file(
            "plugin_device",
            os.path.join(Path(__file__).resolve().parent, "plugin_device.py"),
        )
        return plugin_device.PluginDevice(device_connection=device_connection)

        # install through pip
        # from .plugin_device import PluginDevice
        # return PluginDevice(device_connection=device_connection)
    elif device_type == "synthetic":
        # install through navigate
        synthetic_device = load_module_from_file(
            "synthetic_device",
            os.path.join(Path(__file__).resolve().parent, "synthetic_device.py"),
        )
        return synthetic_device.SyntheticDevice(device_connection=device_connection)
    
        # install through pip
        # from .synthetic_device import SyntheticDevice
        # return SyntheticDevice(device_connection=device_connection)
    else:
        return device_not_found(microscope_name, device_type)
