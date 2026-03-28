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


"""This is all-in-one launch script intended for use by nav2 developers."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


#region Start Simulation

def launch_setup(context, *args, **kwargs):
    """
    The Method is starting the simulation. This is for gazebo harmonic and higher.
    This is implemented as OpaqueFunction to process and control the simulation start. 
    """
    world = LaunchConfiguration("world").perform(context)
    headless = LaunchConfiguration("headless").perform(context)
    gz_args = f"--headless-rendering -s -v 4 -r {world}" if eval(headless) else f"-r {world}"
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                ]
            )
        ),
        launch_arguments={
            "gz_args": gz_args,
            "on_exit_shutdown": "True",
        }.items(),
    )
    return [gz_sim]

#endregion


def generate_launch_description():
#region  Get the launch directories
    pkg_bringup = get_package_share_directory('x3plus_bringup')
    bringup_launch_dir = os.path.join(pkg_bringup, 'launch')
    world_file = PathJoinSubstitution([get_package_share_directory("aws_robomaker_small_house_world"), "worlds", "small_house.world"])
#endregion 

#region  Create the launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
#endregion

#region  Declare the launch arguments


    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use simulation (Gazebo) clock if true')

    declare_simulator_cmd = DeclareLaunchArgument(
        'headless',
        default_value='True',
        description='Whether to execute gazebo Client UI)')

    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value=world_file,
        description='Full path to world model file to load')

#endregion

    robot_sim_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("x3plus_worlds"),
                "launch",
                "robots",
                "x3plus.launch.py",
            ])
        ),
        launch_arguments={
            "robot_name": LaunchConfiguration("robot_name", default="x3plus_bot"),
            "x": LaunchConfiguration("x", default="0.00"),
            "y": LaunchConfiguration("y", default="0.00"),
            "z": LaunchConfiguration("z", default="0.00"),
            "roll": LaunchConfiguration("roll", default="0.00"),
            "pitch": LaunchConfiguration("pitch", default="0.00"),
            "yaw": LaunchConfiguration("yaw", default="0.00"),
        }.items(),
    )

    x3plus_bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_launch_dir, 'bringup_launch.py')),
        launch_arguments={'namespace': "",
                          'use_namespace':  "False",
                          'use_rviz': "False",
                          'use_sim_time': use_sim_time
                          }.items())

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_use_sim_time_cmd)

    ld.add_action(declare_simulator_cmd)
    ld.add_action(declare_world_cmd)

    # Add any simulation  actions
    ld.add_action(OpaqueFunction(function=launch_setup))
    ld.add_action(robot_sim_cmd)

    # Add the actions to launch all of the navigation nodes
    # ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(x3plus_bringup_cmd)
    

    return ld
