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

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def validate_enum_arg(context, name, valid):
    value = context.launch_configurations[name]
    if value not in valid:
        raise ValueError(
            f"Argument '{name}' must be one of {valid}, got '{value}'"
        )


def generate_launch_description() -> LaunchDescription:
	"""Generate a ROS 2 launch description skeleton."""

	# Launch arguments
	use_sim_time = LaunchConfiguration("use_sim_time")
	robot_name = LaunchConfiguration("robot_name")
	mode = LaunchConfiguration("mode")
	use_case = LaunchConfiguration("use_case")
	use_ui = LaunchConfiguration("use_ui")
	rviz_config_file = LaunchConfiguration("rviz_config_file")

	pkg_share = FindPackageShare("x3plus_worlds")
	# world_file = PathJoinSubstitution([get_package_share_directory("willowgarage"), "worlds", "willowgarage.world"])
	# world_package = get_package_share_directory("aws_robomaker_small_house_world")
	# world_file = PathJoinSubstitution([world_package, "worlds", "small_house.world"])
	world_package = get_package_share_directory("willowgarage")
	world_file = PathJoinSubstitution([world_package, "worlds", "willowgarage.world"])

	declared_arguments = [
		DeclareLaunchArgument(
			"use_sim_time",
			default_value="true",
			description="Use simulation (Gazebo) clock if true.",
		),
		DeclareLaunchArgument(
			"mode",
			default_value="simulation",
			description="Launch mode: simulation, real).",
		),
		DeclareLaunchArgument(
			"use_case",
			default_value="drive",
			description="Use case for the robot: drive",
		),
		DeclareLaunchArgument(
			"use_ui",
			default_value="rviz",
			description="Whether to use which UI: rviz, none.",
		),
		DeclareLaunchArgument(
			"robot_name",
			default_value="x3plus_bot",
			description="Robot name namespace/identifier.",
		),
		DeclareLaunchArgument(
			"world",
			default_value=world_file,
			description="Full path to world model file to load",
		),
        DeclareLaunchArgument(
            'headless',
            default_value='False',
            description='Whether to execute gazebo Client UI)'),
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=PathJoinSubstitution([pkg_share, 'rviz', 'nav_footprint.rviz']),
            description='Full path to the RVIZ config file to use')
	]

	launch_actions = [
		LogInfo(msg=["Starting bringup for robot: ", robot_name]),
		OpaqueFunction(
            function=lambda context: validate_enum_arg(
                context,
                'mode',
                ['simulation', 'real']
            )
        ),
		OpaqueFunction(
            function=lambda context: validate_enum_arg(
                context,
                'use_case',
                ['drive']
            )
        ),
		OpaqueFunction(
            function=lambda context: validate_enum_arg(
                context,
                'use_ui',
                ['rviz', 'none']
            )
        ),		
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource(
				PathJoinSubstitution([
					pkg_share,
					"launch",
					"system",
					"simulation.launch.py",
				])
			),
			launch_arguments={
				"use_sim_time": LaunchConfiguration("use_sim_time"),
				"robot_name": LaunchConfiguration("robot_name", default="x3plus_bot"),
				"world": LaunchConfiguration("world", default=world_file),
				"headless": LaunchConfiguration("headless"),
			}.items(),
			condition=IfCondition(
				PythonExpression(["'", mode, "' == 'simulation'"])
			),
		),
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource(
				PathJoinSubstitution([
					pkg_share,
					"launch",
					"utils",
					"teleop.launch.py",
				])
			),
			launch_arguments={
			}.items(),
			condition=IfCondition(
				PythonExpression(["'", use_case, "' == 'drive'"])
			),
		),
		Node(
			package="rviz2",
			executable="rviz2",
			name="rviz2",
			arguments=["-d", rviz_config_file],
			parameters=[{"use_sim_time": use_sim_time}],
			output="screen",
			condition=IfCondition(
				PythonExpression(["'", use_ui, "' == 'rviz'"])
			),
		),
	]

	return LaunchDescription(declared_arguments + launch_actions)
