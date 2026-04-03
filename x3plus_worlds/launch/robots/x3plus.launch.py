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
import tempfile
import xml.etree.ElementTree as ET
import xacro

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def get_world_name(sdf_path: str) -> str:
    tree = ET.parse(sdf_path)
    root = tree.getroot()
    world = root.find("world")
    return world.get("name") if world is not None else None

#region Convert XACRO file

def evaluate_xacro(context, *args, **kwargs):
    """
    Evaluates LaunchConfigurations in context for use with xacro.process_file(). Returns a list of launch actions to be
     included in launch description    
    Method is converting the XACRO  description into a URDF file format. 
    XARCO Allows some parameters and programming in the robot description
    This is implemented as OpaqueFunction to process description ad publish it. 
    """

    # Use xacro to process the file
    xacro_file = os.path.join(get_package_share_directory('x3plus_description'), 'urdf', 'yahboomcar_X3plus.urdf.xacro')

    #robot_description_config = xacro.process_file(xacro_file)
    robot_description_config = xacro.process_file(xacro_file, 
            mappings={  
                }).toxml()

    robot_state_publisher_node = Node(
       package='robot_state_publisher',
       executable='robot_state_publisher',
       name='robot_state_publisher',
       output='both',
       parameters=[{
        'robot_description': robot_description_config
      }])

    return [robot_state_publisher_node]

#endregion


def render_bridge_config(context, *args, **kwargs):
    """Render bridge YAML template with runtime world/model names."""

    pkg_gazebo = get_package_share_directory("x3plus_gazebo")
    world = LaunchConfiguration("world").perform(context)
    robot_name = LaunchConfiguration("robot_name").perform(context)
    world_name = get_world_name(world)
    template_path = os.path.join(pkg_gazebo, "config", "x3plus_bridge_template.yaml")
    with open(template_path, "r", encoding="utf-8") as template_file:
        bridge_template = template_file.read()

    rendered_bridge = (
        bridge_template
        .replace("${WORLD_NAME}", world_name)
        .replace("${MODEL_NAME}", robot_name)
    )

    safe_world = world_name.replace("/", "_")
    safe_robot = robot_name.replace("/", "_")
    rendered_path = os.path.join(
        tempfile.gettempdir(),
        f"x3plus_bridge_{safe_world}_{safe_robot}.yaml",
    )

    with open(rendered_path, "w", encoding="utf-8") as rendered_file:
        rendered_file.write(rendered_bridge)

    bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": rendered_path,
                "qos_overrides./tf_static.publisher.durability": "transient_local",
            }
        ],
        output="screen",
    )

    return [bridge_cmd]

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
    world_name = LaunchConfiguration("world")

    declared_arguments = [
        DeclareLaunchArgument("robot_name", default_value="x3plus_bot"),
        DeclareLaunchArgument("x", default_value="0.00"),
        DeclareLaunchArgument("y", default_value="0.00"),
        DeclareLaunchArgument("z", default_value="0.00"),
        DeclareLaunchArgument("roll", default_value="0.00"),
        DeclareLaunchArgument("pitch", default_value="0.00"),
        DeclareLaunchArgument("yaw", default_value="0.00"),
        DeclareLaunchArgument("world"),
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

    pt_joint_bridge_cmd = Node(
        package="x3plus_gazebo",
        executable="pt_joint_command_bridge",
        output="screen",
    )

     
    return LaunchDescription(
        declared_arguments
        + [
            OpaqueFunction(function=evaluate_xacro),
            OpaqueFunction(function=render_bridge_config),
            gz_spawn_entity,
            pt_joint_bridge_cmd,
        ]
    )
