from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
import zzz_od.application.notify.push as Push
from one_dragon.utils import os_utils
import os
import re
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import zzz_od.application.zzz_one_dragon_app as app

class NotifyApp(ZApplication):

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(self, ctx, 'notify',
                              op_name=gt('通知', 'ui'),
                              need_check_game_win=False,
                               run_record=ctx.notify_record)

    @operation_node(name='发送通知', is_start_node=True)
    def notify(self) -> OperationRoundResult:
        """
        打开游戏
        :return:
        """
        if self.ctx.notify_config.notify_method == 'DISABLED':
            return self.round_fail('未启用通知')
        Push.push_config['HITOKOTO'] = 'false'

        def read_log_files(path:str) -> str:
            """读取并过滤最近3小时的日志"""
            combined = []
            time_pattern = re.compile(r"^\[(\d{2}:\d{2}:\d{2}\.\d{3})\]")
            three_hours_ago = datetime.now() - timedelta(hours=3)
            
            
            try:
                if not os.path.exists(path):
                        print(f"日志文件不存在: {path}")

                with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # 提取时间戳
                            match = time_pattern.match(line)
                            if not match:
                                continue
                            
                            try:
                                log_time = parse_log_time(match.group(1))
                                if log_time >= three_hours_ago:
                                    combined.append(line)
                            except Exception as e:
                                print(f"时间解析失败: {line[:50]}... ({str(e)})")
                                
            except UnicodeDecodeError:
                    print(f"文件编码错误: {path}")
            except Exception as e:
                    print(f"日志读取异常: {str(e)}")
            
            return "\n".join(combined) if combined else ""
        def parse_log_time(time_str: str) -> datetime:
            """解析日志时间并处理跨天情况"""
            try:
                log_time = datetime.strptime(time_str, "%H:%M:%S.%f").time()
                now = datetime.now()
                today_date = now.date()
                
                # 组合当前日期和日志时间
                log_datetime = datetime.combine(today_date, log_time)
                
                # 处理跨天情况（如果日志时间晚于当前时间，则视为前一天）
                if log_datetime > now:
                    log_datetime -= timedelta(days=1)
                    
                return log_datetime
            except ValueError as e:
                raise ValueError(f"无效时间格式: {time_str}") from e

        logs = read_log_files(os.path.join(os_utils.get_path_under_work_dir('.log'), 'log.txt'))
        if not logs:
            raise ValueError("最近3小时内未找到有效日志")
        # 日志处理
        def process_instructions(allowed_instructions: List[str], log_text: str) -> List[Dict[str, Any]]:
            instr_pattern = re.compile(
                r"指令\s*\[\s*({})\s*\]\s.*执行\s*(\S+)".format(
                    "|".join(fr"\s*{re.escape(i)}\s*" for i in allowed_instructions)
                ),
                re.IGNORECASE
            )

            instruction_states = {
                instr: {"is_success": False, "states": []}
                for instr in allowed_instructions
            }

            for line in log_text.split("\n"):
                match = instr_pattern.search(line)
                if match:
                    raw_instr = match.group(1).strip()
                    status = match.group(2).upper()

                    matched_instr = next(
                        (instr for instr in allowed_instructions
                        if raw_instr.lower() == instr.lower()),
                        None
                    )

                    if matched_instr:
                        record = instruction_states[matched_instr]
                        if status == "成功" and not record["is_success"]:
                            record["is_success"] = True
                            record["states"].append(status)
                        elif not record["is_success"]:
                            record["states"].append(status)

            return [
                {
                    "instruction": instr,
                    "is_success": data["is_success"],
                    "states": data["states"]
                }
                for instr, data in instruction_states.items()
                if data["states"]
            ]


        # 消息格式化
        def format_message(results: List[Dict[str, Any]]) -> str:
            success = []
            failure = []

            for item in results:
                if item["is_success"]:
                    success.append(item["instruction"])
                else:
                    failure.append(item["instruction"])

            parts = [f"OneDragon执行完成："]
            if failure:
                parts.append(f"❌ 失败指令：{', '.join(failure)}")
            else:
                parts.append(f"全部成功✅")
            if success:
                parts.append(f"成功指令：{', '.join(success)}")
            else:
                parts.remove(f"全部成功✅")
                parts.append(f"全部失败❌")
            return "\n".join(parts) if parts else "⚠️ 未检测到有效指令状态"  
        
        allowed_instructions = []
        for app_lists in app.ZOneDragonApp.get_app_list(self):
            allowed_instructions.append(app_lists.op_name)
        
        results = process_instructions(allowed_instructions,logs)
        message = format_message(results)


        for k in Push.push_config:
            if self.ctx.notify_config.get(k.lower()) and k.lower().startswith(self.ctx.notify_config.notify_method.lower()):
                Push.push_config[k] = self.ctx.notify_config.get(k.lower())
        Push.send("绝区零一条龙运行通知",message,Push.push_config)


        
        return self.round_success(wait=5)


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = NotifyApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()