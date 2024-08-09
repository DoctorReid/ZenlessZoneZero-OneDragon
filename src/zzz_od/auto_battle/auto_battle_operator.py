import os
from typing import List, Optional

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.state_handler_template import StateHandlerTemplate
from one_dragon.base.conditional_operation.state_recorder import StateRecorder
from one_dragon.utils import os_utils
from zzz_od.auto_battle.atomic_op.btn_chain_left import AtomicBtnChainLeft
from zzz_od.auto_battle.atomic_op.btn_chain_right import AtomicBtnChainRight
from zzz_od.auto_battle.atomic_op.btn_dodge import AtomicBtnDodge
from zzz_od.auto_battle.atomic_op.btn_move_a import AtomicBtnMoveA
from zzz_od.auto_battle.atomic_op.btn_move_d import AtomicBtnMoveD
from zzz_od.auto_battle.atomic_op.btn_move_s import AtomicBtnMoveS
from zzz_od.auto_battle.atomic_op.btn_move_w import AtomicBtnMoveW
from zzz_od.auto_battle.atomic_op.btn_normal_attack import AtomicBtnNormalAttack
from zzz_od.auto_battle.atomic_op.btn_special_attack import AtomicBtnSpecialAttack
from zzz_od.auto_battle.atomic_op.btn_switch_next import AtomicBtnSwitchNext
from zzz_od.auto_battle.atomic_op.btn_switch_prev import AtomicBtnSwitchPrev
from zzz_od.auto_battle.atomic_op.btn_ultimate import AtomicBtnUltimate
from zzz_od.auto_battle.atomic_op.state_clear import AtomicClearState
from zzz_od.auto_battle.atomic_op.state_set import AtomicSetState
from zzz_od.auto_battle.atomic_op.wait import AtomicWait
from zzz_od.context.battle_context import BattleEventEnum
from zzz_od.context.yolo_context import YoloStateEventEnum
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentEnum, AgentTypeEnum


class AutoBattleOperator(ConditionalOperator):

    def __init__(self, ctx: ZContext, sub_dir: str, template_name: str, is_mock: bool = False):
        self.ctx: ZContext = ctx

        ConditionalOperator.__init__(
            self,
            sub_dir=sub_dir,
            template_name=template_name,
            is_mock=is_mock
        )

        self._state_recorders: dict[str, StateRecorder] = {}
        self._mutex_list: dict[str, List[str]] = {}

    def init_operator(self):
        self._mutex_list: dict[str, List[str]] = {}

        for agent_enum in AgentEnum:
            mutex_list: List[str] = []
            for mutex_agent_enum in AgentEnum:
                if mutex_agent_enum == agent_enum:
                    continue
                mutex_list.append(mutex_agent_enum.value.agent_name)

            self._mutex_list['前台-' + agent_enum.value.agent_name] = ['前台-' + i for i in mutex_list]

        for agent_type_enum in AgentTypeEnum:
            mutex_list: List[str] = []
            for mutex_agent_type_enum in AgentTypeEnum:
                if mutex_agent_type_enum == agent_type_enum:
                    continue
                mutex_list.append(mutex_agent_type_enum.value)

            self._mutex_list['前台-' + agent_type_enum.value] = ['前台-' + i for i in mutex_list]
            
        ConditionalOperator.init(
            self,
            event_bus=self.ctx,
            state_getter=self.get_state_recorder,
            op_getter=self.get_atomic_op,
            scene_handler_getter=AutoBattleOperator.get_state_handler_template,
            operation_template_getter=AutoBattleOperator.get_operation_template
        )

    @staticmethod
    def get_all_state_event_ids() -> List[str]:
        """
        目前可用的状态事件ID
        :return:
        """
        event_ids = []

        for event_enum in YoloStateEventEnum:
            event_ids.append(event_enum.value)

        for event_enum in BattleEventEnum:
            event_ids.append(event_enum.value)

        for agent_enum in AgentEnum:
            event_ids.append('前台-' + agent_enum.value.agent_name)
            event_ids.append('后台-1-' + agent_enum.value.agent_name)
            event_ids.append('后台-2-' + agent_enum.value.agent_name)
            event_ids.append('连携技-1-' + agent_enum.value.agent_name)
            event_ids.append('连携技-2-' + agent_enum.value.agent_name)
            event_ids.append('快速支援-' + agent_enum.value.agent_name)

        for agent_type_enum in AgentTypeEnum:
            event_ids.append('前台-' + agent_type_enum.value)
            event_ids.append('后台-1-' + agent_type_enum.value)
            event_ids.append('后台-2-' + agent_type_enum.value)
            event_ids.append('连携技-1-' + agent_type_enum.value)
            event_ids.append('连携技-2-' + agent_type_enum.value)
            event_ids.append('快速支援-' + agent_type_enum.value)

        return event_ids

    def get_state_recorder(self, state_name: str) -> Optional[StateRecorder]:
        """
        获取状态记录器
        :param state_name:
        :return:
        """
        if AutoBattleOperator.is_valid_state(state_name):
            if state_name in self._state_recorders:
                return self._state_recorders[state_name]
            else:
                r = StateRecorder(self.ctx, state_name, mutex_list=self._mutex_list.get(state_name, None))
                self._state_recorders[state_name] = r
                return r
        else:
            return None

    @staticmethod
    def is_valid_state(state_name: str) -> bool:
        """
        判断一个状态是否合法
        :param state_name:
        :return:
        """
        if state_name in AutoBattleOperator.get_all_state_event_ids():
            return True
        elif state_name.startswith('自定义-'):
            return True
        else:
            return False

    def get_atomic_op(self, op_name: str, op_data: List[str]) -> AtomicOp:
        """
        获取一个原子操作
        :param op_name:
        :param op_data:
        :return:
        """
        # 有几个特殊参数 在这里统一提取
        press: bool = op_name.endswith('-按下')
        release: bool = op_name.endswith('-松开')
        if press:
            press_time = float(op_data[0]) if len(op_data) > 0 else None
        else:
            press_time = None

        if op_name.startswith(BattleEventEnum.BTN_DODGE.value):
            return AtomicBtnDodge(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_SWITCH_NEXT.value):
            return AtomicBtnSwitchNext(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_SWITCH_PREV.value):
            return AtomicBtnSwitchPrev(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value):
            return AtomicBtnNormalAttack(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_SWITCH_SPECIAL_ATTACK.value):
            return AtomicBtnSpecialAttack(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_ULTIMATE.value):
            return AtomicBtnUltimate(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_CHAIN_LEFT.value):
            return AtomicBtnChainLeft(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_CHAIN_RIGHT.value):
            return AtomicBtnChainRight(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_MOVE_W.value):
            return AtomicBtnMoveW(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_MOVE_S.value):
            return AtomicBtnMoveS(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_MOVE_A.value):
            return AtomicBtnMoveA(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name.startswith(BattleEventEnum.BTN_MOVE_D.value):
            return AtomicBtnMoveD(self.ctx, press=press, press_time=press_time, release=release)
        elif op_name == AtomicWait.OP_NAME:
            if len(op_data) == 0:
                raise ValueError(f'{AtomicWait.OP_NAME} 未填入参数 data')
            return AtomicWait(float(op_data[0]))
        elif op_name == AtomicSetState.OP_NAME:
            if len(op_data) == 0:
                raise ValueError(f'{AtomicSetState.OP_NAME} 未填入参数 data')
            event_id = op_data[0]
            diff_time = float(op_data[1]) if len(op_data) > 1 else 0
            value = int(op_data[2]) if len(op_data) > 2 else None
            return AtomicSetState(self.ctx.custom_battle, event_id, diff_time, value)
        elif op_name == AtomicClearState.OP_NAME:
            if len(op_data) == 0:
                raise ValueError(f'{AtomicClearState.OP_NAME} 未填入参数 data')
            event_id = op_data[0]
            return AtomicClearState(self.ctx.custom_battle, event_id)
        else:
            raise ValueError('非法的指令 %s' % op_name)

    @staticmethod
    def get_state_handler_template(target_template_name: str) -> Optional[StateHandlerTemplate]:
        """
        获取场景处理器模板
        :param target_template_name: 模板名称
        :return:
        """
        sub_dir = 'auto_battle_state_handler'
        template_dir = os_utils.get_path_under_work_dir('config', sub_dir)
        file_list = os.listdir(template_dir)

        for file_name in file_list:
            if file_name.endswith('.sample.yml'):
                template_name = file_name[0:-11]
            elif file_name.endswith('.yml'):
                template_name = file_name[0:-4]
            else:
                continue
            if template_name != target_template_name:
                continue

            return StateHandlerTemplate(sub_dir, template_name)

        return None

    @staticmethod
    def get_operation_template(target_template_name: str) -> Optional[OperationTemplate]:
        """
        获取操作模板
        :param target_template_name: 模板名称
        :return:
        """
        sub_dir = 'auto_battle_operation'
        template_dir = os_utils.get_path_under_work_dir('config', sub_dir)
        file_list = os.listdir(template_dir)

        for file_name in file_list:
            if file_name.endswith('.sample.yml'):
                template_name = file_name[0:-11]
            elif file_name.endswith('.yml'):
                template_name = file_name[0:-4]
            else:
                continue

            if target_template_name != template_name:
                continue

            return OperationTemplate(sub_dir, template_name)

        return None

    def dispose(self) -> None:
        """
        销毁 注意要解绑各种事件监听
        :return:
        """
        ConditionalOperator.dispose(self)
        for sr in self._state_recorders.values():
            sr.dispose()
        self._state_recorders.clear()


if __name__ == '__main__':
    ctx = ZContext()
    ctx.init_by_config()
    op = AutoBattleOperator(ctx, 'auto_battle', '强攻站场-击破支援速切')
    op.init_operator()
    print(op.get_usage_states())
    pass