"""Command-line interface for Vive Tracker."""

import argparse
import time
from vive_tracker.tracker import ViveTrackerModule, VRTrackedDevice
from vive_tracker.steamvr import enable_vive_trackers_without_hmd


def print_tracker_data(tracker: VRTrackedDevice, interval):
    """Continuously print tracker pose data at the specified interval.
    
    Args:
        tracker: The tracker device to monitor
        interval: Time interval between updates in seconds
    """
    while True:
        start_time = time.time()

        pose = tracker.get_pose_euler()
        pose_mat = tracker.get_pose_matrix()
        vel = tracker.get_velocity()
        pose_quat = tracker.get_pose_quaternion()

        if pose:
            pose_str = f"x={pose[0]:.4f} y={pose[1]:.4f} z={pose[2]:.4f} roll={pose[3]:.4f} pitch={pose[4]:.4f} yaw={pose[5]:.4f}, vel={vel}"
            print(f"{time.time():.4f} {pose_str}")
        else:
            print(f"{time.time():.4f} No pose data available.")
        
        # Calculate sleep time to maintain the desired interval
        sleep_time = interval - (time.time() - start_time)

        # Sleep if necessary
        if sleep_time > 0:
            time.sleep(sleep_time)


def main():
    """Main entry point for the vive-tracker CLI."""
    parser = argparse.ArgumentParser(
        description="HTC Vive Tracker 6 DOF tracking interface"
    )
    parser.add_argument(
        "-f",
        "--frequency",
        type=int,
        default=30,
        help="Frequency of location updates in Hz (default: 30)",
    )
    parser.add_argument(
        "-t",
        "--tracker",
        type=str,
        default="tracker_1",
        help="Tracker device name (default: tracker_1)",
    )
    parser.add_argument(
        "--configure-steamvr",
        action="store_true",
        help="Configure SteamVR settings to enable trackers without HMD",
    )
    
    args = parser.parse_args()

    # Handle SteamVR configuration if requested
    if args.configure_steamvr:
        print("Configuring SteamVR to enable trackers without HMD...\n")
        try:
            driver_null, main_settings = enable_vive_trackers_without_hmd(
                prompt_user=True,
                kill_steam_processes=True
            )
            print(f"\n✓ Successfully configured SteamVR!")
            print(f"  Modified: {driver_null}")
            print(f"  Modified: {main_settings}")
            print("\nBackups created with _BACKUP suffix.")
            print("Please restart SteamVR for changes to take effect.")
            return 0
        except Exception as e:
            print(f"\n❌ Configuration failed: {e}")
            return 1

    # Calculate interval based on the specified frequency
    interval = 1 / args.frequency

    # Initialize Vive Tracker and print discovered objects
    v_tracker = ViveTrackerModule()
    v_tracker.print_discovered_objects()

    # Check if the specified tracker exists
    if args.tracker not in v_tracker.devices:
        print(f"\nError: Tracker '{args.tracker}' not found.")
        print(f"Available devices: {list(v_tracker.devices.keys())}")
        return 1

    # Print tracker data
    tracker_device: VRTrackedDevice = v_tracker.devices[args.tracker]

    serial = tracker_device.get_serial()
    model = tracker_device.get_model()
    battery = tracker_device.get_battery_percent()
    print(f"\nTracker '{args.tracker}' info:")
    print(f"  Serial: {serial}")
    print(f"  Model: {model}")
    print(f"  Battery: {battery:.1f}%")

    print(f"\nTracking {args.tracker} at {args.frequency} Hz")
    print("Output format: timestamp x y z yaw pitch roll\n")
    
    try:
        print_tracker_data(tracker_device, interval)
    except KeyboardInterrupt:
        print("\n\nTracking stopped by user.")
        return 0


if __name__ == "__main__":
    exit(main())
