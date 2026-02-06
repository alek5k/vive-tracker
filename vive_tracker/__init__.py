"""
Vive Tracker - HTC Vive Tracker 6 DOF tracking interface

This package provides a Python interface for tracking HTC Vive Trackers
using OpenVR and SteamVR.
"""

from .tracker import (
    ViveTrackerModule,
    VRTrackedDevice,
    VRTrackingReference,
    PoseSampleBuffer,
    convert_to_euler,
    convert_to_quaternion,
    get_pose,
)

__version__ = "0.1.0"
__all__ = [
    "ViveTrackerModule",
    "VRTrackedDevice",
    "VRTrackingReference",
    "PoseSampleBuffer",
    "convert_to_euler",
    "convert_to_quaternion",
    "get_pose",
]
