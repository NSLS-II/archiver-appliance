# -*- coding: utf-8 -*-
"""Top-level package for Python EPICS Archiver Appliance (AA) library."""
from pkg_resources import get_distribution, DistributionNotFound
from .aa import *
from .epicsarchiver import ArchiverAppliance

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

__author__ = """Yong Hu"""
__email__ = "yhu@bnl.gov"

__all__ = [ "report_never_connected_pvs",
            "report_currently_disconnected_pvs",
            "report_paused_pvs",
            "report_pvs",
            "report_all_pvs",
            "report_pvs_from_file",
            "report_waveform_pvs",
            "report_storage_rate",
            "report_storage_consumed",
            "report_overflow_pvs",
            "abort_pvs",
            "pause_pvs",
            "resume_pvs",
            "delete_pvs_only",
            "delete_pvs_and_data",
            "change_pvs_archival_parameters",
            "get_reconnected_pvnames",
            "ArchiverAppliance"]
