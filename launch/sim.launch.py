"""Single-entry Jazzy / Harmonic tennis simulation with optional software EGL."""
import os
from pathlib import Path
import xacro
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, Shutdown
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def start_sim(context):
    share = Path(get_package_share_directory('teambot_bringup'))



    #Debugged for mac with software rendering, but should work on Linux as well.
    #Fuck TS honestly, I don't know why this is necessary, but it is. The Gazebo server will not start without this. on mac fuc mac 

    headless = LaunchConfiguration('headless').perform(context).lower() == 'true'
    software = LaunchConfiguration('software_rendering').perform(context).lower() == 'true'
    engine = LaunchConfiguration('render_engine').perform(context)
    egl = LaunchConfiguration('headless_rendering').perform(context).lower() == 'true'
    gui = LaunchConfiguration('gui').perform(context).lower() == 'true'
    if software and not headless:
        raise RuntimeError('software_rendering requires headless:=true (software EGL server)')
    if software and engine != 'ogre2':
        raise RuntimeError('software_rendering requires render_engine:=ogre2')
    if (headless or egl) and engine != 'ogre2':
        raise RuntimeError('EGL headless rendering requires ogre2')
    description = xacro.process_file(str(share / 'urdf/tennis.urdf.xacro')).toxml()
    assets = str(Path(get_package_share_directory('turtlebot3_description')).parent)
    render_env = {
        'GZ_SIM_RESOURCE_PATH': assets + os.pathsep + os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
    }
    if software:
        library = Path(get_package_prefix('teambot_bringup')) / 'lib/libsoftware_egl.so'
        if not library.is_file():
            raise RuntimeError(f'Missing installed EGL helper: {library}; rebuild the package')
        render_env.update({'LIBGL_ALWAYS_SOFTWARE': '1', 'LD_PRELOAD': str(library)})
    cmd = ['gz', 'sim', '-r', '--force-version', '8', '--render-engine', engine,
           '--render-engine-server-api-backend', 'opengl']
    if headless or not gui:
        cmd.append('-s')
    if headless or egl:
        cmd.append('--headless-rendering')
    
    # Normal launch 
    cmd.append(str(share / 'worlds/tennis.sdf'))
    return [
        ExecuteProcess(cmd=cmd, additional_env=render_env, output='screen', on_exit=Shutdown()),
        Node(package='robot_state_publisher', executable='robot_state_publisher', parameters=[{'robot_description': description, 'use_sim_time': True}]),
        # create waits for the world service and transient-local description.
        Node(package='ros_gz_sim', executable='create', arguments=['-world', 'tennis', '-name', 'teambot', '-topic', '/robot_description', '-x', '-14', '-y', '-7', '-z', '0.02'], output='screen'),
        Node(package='ros_gz_bridge', executable='parameter_bridge', parameters=[{'config_file': str(share / 'config/bridge.yaml'), 'use_sim_time': True}], output='screen'),
        Node(package='rviz2', executable='rviz2', arguments=['-d', str(share / 'rviz/tennis.rviz')], parameters=[{'use_sim_time': True}], condition=IfCondition(LaunchConfiguration('rviz')), additional_env={'LIBGL_ALWAYS_SOFTWARE': '1'} if software else {}),
    ]


def generate_launch_description():
    return LaunchDescription([

        DeclareLaunchArgument('headless', default_value='false', description='Server only, with EGL sensor rendering'),
        DeclareLaunchArgument('software_rendering', default_value='false', description='Force Mesa software EGL for Gazebo and software GL for RViz'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('render_engine', default_value='ogre2'),
        
        # Preserve the previous explicit server/engine options.
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('headless_rendering', default_value='false'),
        OpaqueFunction(function=start_sim),
    ])
