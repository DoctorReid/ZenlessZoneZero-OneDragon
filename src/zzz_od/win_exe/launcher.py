import sys
import argparse
from one_dragon.devtools import python_launcher

# 版本号
__version__ = "v2.1.0"


def get_version():
    """获取版本号"""
    return __version__


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="绝区零 一条龙 启动器", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本号")
    parser.add_argument("-o", "--onedragon", action="store_true", help="一条龙运行")
    parser.add_argument("-c", "--close-game", action="store_true", help="运行后关闭游戏")
    parser.add_argument("-s", "--shutdown", type=int, nargs='?', const=60, help="运行后关机，可指定延迟秒数，默认60秒")
    parser.add_argument("-i", "--instance", type=str, help="指定运行的账号实例，多个用英文逗号分隔，如：1,2")
    parser.add_argument("-a", "--app", type=str, help="指定运行的应用，仅限一条龙页面的应用，多个用英文逗号分隔")

    args = parser.parse_args()

    if args.version:
        print(f"绝区零 一条龙 启动器 {get_version()}")
        sys.exit(0)

    if not args.onedragon and (args.close_game or args.shutdown or args.instance or args.app):
        print("错误：参数 --close-game, --shutdown, --instance, --app 只能在指定 --onedragon 时使用")
        sys.exit(1)

    if args.onedragon:
        launch_args = []
        if args.instance:
            launch_args.extend(["--instance", args.instance])
        if args.app:
            launch_args.extend(["--app", args.app])
        if args.close_game:
            launch_args.append("--close-game")
        if args.shutdown:
            launch_args.extend(["--shutdown", str(args.shutdown)])
        python_launcher.run_python(["zzz_od", "application", "application_runner.py"], no_windows=False, args=launch_args)
    else:
        python_launcher.run_python(["zzz_od", "gui", "app.py"], no_windows=True)
