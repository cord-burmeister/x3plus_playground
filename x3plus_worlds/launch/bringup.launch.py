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
import socket


HOSTNAME_WORLD_MAP = {
	"b760": ("willowgarage", "willowgarage-hd.world"),
}

DEFAULT_WORLD = ("willowgarage", "willowgarage.world")


def validate_enum_arg(context, name, valid):
    value = context.launch_configurations[name]
    if value not in valid:
        raise ValueError(
            f"Argument '{name}' must be one of {valid}, got '{value}'"
        )

def running_in_wsl() -> bool:
    """Detect whether the current process is running inside Windows Subsystem for Linux (WSL).

    Reads /proc/sys/kernel/osrelease and checks for 'microsoft' or 'wsl' in the
    kernel release string, which are present in WSL 1 and WSL 2 kernels.

    Returns:
        True if running inside WSL, False otherwise (including native Linux or
        any environment where /proc/sys/kernel/osrelease is unavailable).
    """
    try:
        with open("/proc/sys/kernel/osrelease") as f:
            release = f.read().lower()
        return "microsoft" in release or "wsl" in release
    except FileNotFoundError:
        return False


def resolve_world_for_hostname() -> tuple[str, str, str]:
	"""Resolve the default world package and file for the current hostname."""
	hostname = socket.gethostname()
	normalized_hostname = hostname.split(".")[0].lower()
	package_name, world_name = HOSTNAME_WORLD_MAP.get(normalized_hostname, DEFAULT_WORLD)
	world_package = get_package_share_directory(package_name)
	return hostname, world_package, world_name

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
	pkg_teleop = FindPackageShare("x3plus_teleop")
	hostname, world_package, world_name = resolve_world_for_hostname()
	world_file = PathJoinSubstitution([world_package, "worlds", world_name])

	if running_in_wsl():
		msg = "Running inside WSL"
		use_joystick = "false"
	else:
		msg = "Running on native Linux"
		use_joystick = "true"

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
			default_value="cockpit",
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
		LogInfo(msg=["Starting bring up for robot: ", robot_name]),
		LogInfo(msg=[msg]),
		LogInfo(msg=["Selected default world for host ", hostname, ": ", world_name]),

		# region Validation of enum arguments
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
                ['cockpit', 'rviz', 'none']
            )
        ),
		# endregion

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
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource(
				PathJoinSubstitution([
					pkg_teleop,
					"launch",
					"cockpit.launch.py",
				])
			),
			launch_arguments={
				"use_joystick": LaunchConfiguration("use_joystick", default=use_joystick),
			}.items(),
			condition=IfCondition(
				PythonExpression(["'", use_ui, "' == 'cockpit'"])
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
