import argparse
import sys
from typing import List

from one_dragon.utils import cmd_utils
from one_dragon.utils.log_utils import log
from zzz_od.application.zzz_one_dragon_app import ZOneDragonApp
from zzz_od.context.zzz_context import ZContext


def parse_comma_separated_values(value: str) -> List[str]:
    """解析逗号分隔的值"""
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_comma_separated_ints(value: str) -> List[int]:
    """解析逗号分隔的整数值"""
    if not value:
        return []
    try:
        return [int(item.strip()) for item in value.split(',') if item.strip()]
    except ValueError:
        log.error(f"无效的实例参数: {value}")
        return []


def set_temp_instance_config(ctx: ZContext, instance_indices: List[int]) -> bool:
    """设置临时实例配置"""
    if not instance_indices:
        return False

    ctx.one_dragon_config.set_temp_instance_indices(instance_indices)

    # 验证有效实例
    valid_instances = [idx for idx in instance_indices
                       if any(instance.idx == idx for instance in ctx.one_dragon_config.instance_list)]

    if valid_instances:
        log.info(f"指定运行实例: {valid_instances}")
        return True
    else:
        log.error("未找到有效的实例")
        ctx.one_dragon_config.clear_temp_instance_indices()
        return False


def set_temp_app_config(ctx: ZContext, app_names: List[str]) -> bool:
    """设置临时应用配置"""
    if not app_names:
        return False

    # 获取所有可用应用
    temp_app = ZOneDragonApp(ctx)
    all_apps = temp_app.get_app_list()

    # 构建应用名称到ID的映射
    app_name_to_id = {}
    for app in all_apps:
        # 使用应用ID作为名称
        app_name_to_id[app.app_id] = app.app_id
        # 如果有中文名称，也加入映射
        if hasattr(app, 'op_name') and app.op_name:
            app_name_to_id[app.op_name] = app.app_id

    # 查找匹配的应用ID
    valid_app_ids = []
    for app_name in app_names:
        if app_name in app_name_to_id:
            valid_app_ids.append(app_name_to_id[app_name])
        else:
            log.warning(f"未找到应用: {app_name}")

    if valid_app_ids:
        ctx.one_dragon_app_config.set_temp_app_run_list(valid_app_ids)
        log.info(f"指定运行应用: {valid_app_ids}")
        return True
    else:
        log.error("未找到有效的应用")
        return False


def main():
    parser = argparse.ArgumentParser(description="绝区零 一条龙 参数启动器", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息")
    parser.add_argument("-c", "--close-game", action="store_true", help="运行后关闭游戏")
    parser.add_argument("-s", "--shutdown", type=int, nargs='?', const=60, help="运行后关机，可指定延迟秒数，默认60秒")
    parser.add_argument("-i", "--instance", type=str, help="指定运行的账号实例，多个用英文逗号分隔，如：1,2")
    parser.add_argument("-a", "--app", type=str, help="指定运行的应用，仅限一条龙页面的应用，多个用英文逗号分隔")

    args = parser.parse_args()

    # 初始化上下文
    ctx = ZContext()
    ctx.init_by_config()

    # 异步加载OCR
    ctx.async_init_ocr()

    # 异步更新免费代理
    ctx.async_update_gh_proxy()

    # 处理命令行参数
    if args.instance:
        instance_indices = parse_comma_separated_ints(args.instance)
        if not set_temp_instance_config(ctx, instance_indices):
            ctx.after_app_shutdown()
            sys.exit(1)

    if args.app:
        app_names = parse_comma_separated_values(args.app)
        if not set_temp_app_config(ctx, app_names):
            ctx.after_app_shutdown()
            sys.exit(1)

    try:
        # 执行一条龙应用
        app = ZOneDragonApp(ctx)
        app.execute()

        # 运行后操作
        if args.close_game:
            ctx.controller.close_game()
        if args.shutdown:
            cmd_utils.shutdown_sys(args.shutdown)
    finally:
        ctx.after_app_shutdown()


if __name__ == '__main__':
    main()
