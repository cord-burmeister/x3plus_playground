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
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
	"""Generate a ROS 2 launch description skeleton."""

	# Launch arguments
	use_sim_time = LaunchConfiguration("use_sim_time")
	robot_name = LaunchConfiguration("robot_name")
	mode = LaunchConfiguration("mode")
	rviz_config_file = LaunchConfiguration("rviz_config_file")
	worlds_use_rviz = LaunchConfiguration("worlds_use_rviz")

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
			description="Launch mode (simulation or real).",
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
            default_value='True',
            description='Whether to execute gazebo Client UI)'),
        DeclareLaunchArgument(
			'worlds_use_rviz',
			default_value='true',
            description='Whether to start RVIZ'),
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=PathJoinSubstitution([pkg_share, 'rviz', 'nav_footprint.rviz']),
            description='Full path to the RVIZ config file to use')
	]



	launch_actions = [
		LogInfo(msg=["Starting bringup for robot: ", robot_name]),
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
		Node(
			package="rviz2",
			executable="rviz2",
			name="rviz2",
			arguments=["-d", rviz_config_file],
			parameters=[{"use_sim_time": use_sim_time}],
			output="screen",
			condition=IfCondition(worlds_use_rviz),
		),
	]

	return LaunchDescription(declared_arguments + launch_actions)
