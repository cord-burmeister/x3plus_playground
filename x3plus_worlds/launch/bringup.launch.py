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

from jaraco import context

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction, SetLaunchConfiguration
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



def derive_configs(context, pkg_share, *args, **kwargs):
	use_case = LaunchConfiguration("use_case").perform(context)
	slam = LaunchConfiguration("slam").perform(context)
	if use_case == "drive":
		rviz_name = "nav_footprint.rviz"
	elif use_case == "slam":
		rviz_name = "nav_footprint.rviz"
		slam = "True"
		# rviz_name = "nav_map.rviz"
	else:
		raise ValueError(f"Unsupported use_case '{use_case}'")
	pkg_share_path = pkg_share.perform(context)  # because pkg_share is FindPackageShare(...)
	rviz_path = os.path.join(pkg_share_path, "rviz", rviz_name)
	return [SetLaunchConfiguration("rviz_config_file", rviz_path), SetLaunchConfiguration("slam", slam)]


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
			default_value="slam",
			description="Use case for the robot: drive, slam",
		),
		DeclareLaunchArgument(
			"use_ui",
			default_value="rviz",
			description="Whether to use which UI: rviz, cockpit, none.",
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
            description='Full path to the RVIZ config file to use'),
		DeclareLaunchArgument(
			'use_nav2',
			default_value='True',
			description='Whether to start the Nav2 stack'),
		DeclareLaunchArgument(
			'map',
			default_value=PathJoinSubstitution([FindPackageShare('x3plus_nav2'), 'maps', 'map.yaml']),
			description='Full path to map file to load'),
		DeclareLaunchArgument(
			'params_file',
			default_value=PathJoinSubstitution([FindPackageShare('x3plus_nav2'), 'config', 'nav2_params.yaml']),
			description='Full path to the Nav2 parameters file'),
		DeclareLaunchArgument(
			'slam',
			default_value='False',
			description='Whether to run SLAM'),
		DeclareLaunchArgument(
			'autostart',
			default_value='true',
			description='Automatically startup the Nav2 stack'),
		DeclareLaunchArgument(
			'use_composition',
			default_value='True',
			description='Whether to use composed bringup'),
		DeclareLaunchArgument(
			'use_respawn',
			default_value='False',
			description='Whether to respawn if a node crashes'),
	]

	launch_actions = [
		LogInfo(msg=["Starting bring up for robot: ", robot_name]),
		LogInfo(msg=[msg]),
		LogInfo(msg=["Selected default world for host ", hostname, ": ", world_name]),

		#region Validation of enum arguments
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
                ['drive', 'slam']
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

	    OpaqueFunction(
                function=derive_configs, 
                        kwargs={"pkg_share": pkg_share},),


		#region Include simulation launch files based on conditions
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
        #endregion
        
		#region Include teleop launch file based on use case
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
				PythonExpression(["'", use_case, "' in ['drive', 'slam']"])
			),
		),
        #endregion

		#region Include localization launch files
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource(
				PathJoinSubstitution([
					FindPackageShare("x3plus_localization"),
					"launch",
					"laser_filters_launch.py",
				])
			),
			launch_arguments={
				"use_sim_time": LaunchConfiguration("use_sim_time"),
			}.items(),
		),
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource(
				PathJoinSubstitution([
					FindPackageShare("x3plus_localization"),
					"launch",
					"wheel_localization_launch.py",
				])
			),
			launch_arguments={
				"use_sim_time": LaunchConfiguration("use_sim_time"),
			}.items(),
		),
		#endregion

		#region Include Nav2 launch file
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource(
				PathJoinSubstitution([
					FindPackageShare('x3plus_nav2'),
					'launch',
					'nav2_launch.py',
				])
			),
			launch_arguments={
				'use_sim_time':    LaunchConfiguration('use_sim_time'),
				'map':             LaunchConfiguration('map'),
				'params_file':     LaunchConfiguration('params_file'),
				'slam':            LaunchConfiguration('slam'),
				'autostart':       LaunchConfiguration('autostart'),
				'use_composition': LaunchConfiguration('use_composition'),
				'use_respawn':     LaunchConfiguration('use_respawn'),
			}.items(),
			condition=IfCondition(LaunchConfiguration('use_nav2')),
		),
		#endregion

        #region Include UI launch files based on conditions    
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
        #endregion
	
	
	]

	return LaunchDescription(declared_arguments + launch_actions)
