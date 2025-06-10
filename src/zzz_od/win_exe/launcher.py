import sys
import argparse
from one_dragon.devtools import python_launcher

# 版本号
__version__ = "2.1.0"


def get_version():
    """获取版本号"""
    return __version__


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="绝区零 一条龙 启动器", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本号")
    parser.add_argument("-o", "--onedragon", action="store_true", help="一条龙运行")

    args = parser.parse_args()

    if args.version:
        print(f"绝区零 一条龙 启动器 {get_version()}")
        sys.exit(0)

    if args.onedragon:
        python_launcher.run_python(["zzz_od", "application", "zzz_one_dragon_app.py"], no_windows=False)
    else:
        python_launcher.run_python(["zzz_od", "gui", "app.py"], no_windows=True)
