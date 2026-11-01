#!/usr/bin/env python3
"""Read-only runtime checks; run while sim.launch.py is active."""
import math
import time
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CameraInfo, LaserScan, JointState
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from tf2_ros import Buffer, TransformListener


def main():
    rclpy.init()
    node = rclpy.create_node('check_tennis_sim')
    received = {}
    subscriptions = []
    specs = [('/scan', LaserScan, 'base_scan'), ('/odom', Odometry, 'odom'),
             ('/camera/image_raw', Image, 'camera_rgb_optical_frame'),
             ('/camera/camera_info', CameraInfo, 'camera_rgb_optical_frame'),
             ('/joint_states', JointState, None), ('/clock', Clock, None)]
    for topic, kind, frame in specs:
        subscriptions.append(node.create_subscription(kind, topic, lambda msg, key=topic: received.__setitem__(key, msg), qos_profile_sensor_data))
    buffer = Buffer()
    listener = TransformListener(buffer, node)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if len(received) == len(specs) and all(buffer.can_transform('odom', frame, rclpy.time.Time()) for frame in ['camera_rgb_optical_frame', 'wheel_left_link', 'wheel_right_link']):
            break
    errors = []
    for topic, _, frame in specs:
        msg = received.get(topic)
        if msg is None:
            errors.append(f'{topic}: no data')
        elif frame and msg.header.frame_id != frame:
            errors.append(f'{topic}: frame {msg.header.frame_id!r}, expected {frame!r}')
        else:
            print(f'PASS {topic}')
    image = received.get('/camera/image_raw')
    if image is not None:
        if (image.width, image.height) != (320, 240):
            errors.append('camera resolution is not 320x240')
        if not image.data or max(image.data) == 0 or len(set(image.data)) < 2:
            errors.append('camera image is empty, black or uniform')
        else:
            print(f'PASS image content: {image.width}x{image.height}, range {min(image.data)}..{max(image.data)}')
    scan = received.get('/scan')
    if scan is not None:
        finite = [value for value in scan.ranges if math.isfinite(value)]
        if not finite:
            errors.append('scan has no finite returns')
        else:
            print(f'PASS scan content: {len(finite)} finite returns')
    if '/odom' in received and received['/odom'].child_frame_id != 'base_footprint':
        errors.append('odom child_frame_id')
    for target in ['base_link', 'base_scan', 'camera_rgb_optical_frame', 'wheel_left_link', 'wheel_right_link']:
        if not buffer.can_transform('odom', target, rclpy.time.Time()):
            errors.append(f'missing TF odom -> {target}')
    node.destroy_node()
    rclpy.shutdown()
    for error in errors:
        print('FAIL', error)
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
