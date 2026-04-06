from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'terminal', default_value='xterm',
            description='Terminal emulator to use'
        ),

        ExecuteProcess(
            cmd=[
                LaunchConfiguration('terminal'),
                '-e',
                'ros2 run teleop_twist_keyboard teleop_twist_keyboard'
            ],
            shell=False
        )
    ])
