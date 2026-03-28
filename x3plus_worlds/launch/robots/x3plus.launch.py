# Copyright 2026 x3plus contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Launch robot-specific spawn and bridge setup for x3plus."""

    pkg_gazebo = get_package_share_directory("x3plus_gazebo")

    robot_name = LaunchConfiguration("robot_name")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    roll = LaunchConfiguration("roll")
    pitch = LaunchConfiguration("pitch")
    yaw = LaunchConfiguration("yaw")

    declared_arguments = [
        DeclareLaunchArgument("robot_name", default_value="x3plus_bot"),
        DeclareLaunchArgument("x", default_value="0.00"),
        DeclareLaunchArgument("y", default_value="0.00"),
        DeclareLaunchArgument("z", default_value="0.00"),
        DeclareLaunchArgument("roll", default_value="0.00"),
        DeclareLaunchArgument("pitch", default_value="0.00"),
        DeclareLaunchArgument("yaw", default_value="0.00"),
    ]

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            robot_name,
            "-allow_renaming",
            "false",
            "-topic",
            "robot_description",
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            roll,
            "-P",
            pitch,
            "-Y",
            yaw,
        ],
        output="screen",
        namespace="",
    )

    bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": os.path.join(pkg_gazebo, "config", "x3plus_bridge.yaml"),
                "qos_overrides./tf_static.publisher.durability": "transient_local",
            }
        ],
        output="screen",
    )

    pt_joint_bridge_cmd = Node(
        package="x3plus_gazebo",
        executable="pt_joint_command_bridge",
        output="screen",
    )

    return LaunchDescription(
        declared_arguments + [gz_spawn_entity, bridge_cmd, pt_joint_bridge_cmd]
    )
