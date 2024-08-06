from typing import Optional, List

from one_dragon.base.config.yaml_config import YamlConfig


class ChargePlanItem:

    def __init__(
            self,
            tab_name: str = '训练',
            category_name: str = '实战模拟室',
            mission_type_name: str = '基础材料',
            mission_name: str = '调查专项',
            auto_battle_config: str = '击破站场-强攻速切',
            run_times: int = 0,
            plan_times: int = 1
    ):
        self.tab_name: str = tab_name
        self.category_name: str = category_name
        self.mission_type_name: str = mission_type_name
        self.mission_name: str = mission_name
        self.auto_battle_config: str = auto_battle_config
        self.run_times: int = run_times
        self.plan_times: int = plan_times


class ChargePlanConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='charge_plan',
            instance_idx=instance_idx,
        )

        self.plan_list: List[ChargePlanItem] = []

        for plan_item in self.data.get('plan_list', []):
            self.plan_list.append(ChargePlanItem(**plan_item))

    def save(self):
        self.data = {}
        plan_list = []
        self.data['plan_list'] = plan_list

        for plan_item in self.plan_list:
            plan_list.append({
                'tab_name': plan_item.tab_name,
                'category_name': plan_item.category_name,
                'mission_type_name': plan_item.mission_type_name,
                'mission_name': plan_item.mission_name,
                'auto_battle_config': plan_item.auto_battle_config,
                'run_times': plan_item.run_times,
                'plan_times': plan_item.plan_times,
            })

        YamlConfig.save(self)

    def add_plan(self) -> None:
        self.plan_list.append(ChargePlanItem(
            '训练',
            '实战模拟室',
            '基础材料',
            '调查专项',
            '击破站场-强攻速切',
            0,
            1
        ))
        self.save()

    def delete_plan(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.plan_list):
            return
        self.plan_list.pop(idx)
        self.save()

    def update_plan(self, idx: int, plan: ChargePlanItem) -> None:
        if idx < 0 or idx >= len(self.plan_list):
            return
        self.plan_list[idx] = plan
        self.save()

    def move_up(self, idx: int) -> None:
        if idx <= 0 or idx >= len(self.plan_list):
            return

        tmp = self.plan_list[idx - 1]
        self.plan_list[idx - 1] = self.plan_list[idx]
        self.plan_list[idx] = tmp

        self.save()

    def reset_plans(self) -> None:
        if len(self.plan_list) == 0:
            return

        while True:
            all_finish: bool = True
            for plan in self.plan_list:
                if plan.run_times < plan.plan_times:
                    all_finish = False

            if not all_finish:
                break

            for plan in self.plan_list:
                plan.run_times -= plan.plan_times

            self.save()

    def get_next_plan(self) -> Optional[ChargePlanItem]:
        if len(self.plan_list) == 0:
            return None

        self.reset_plans()

        for plan in self.plan_list:
            if plan.run_times < plan.plan_times:
                return plan

        return None

    def add_plan_run_times(self, to_add: ChargePlanItem) -> None:
        """
        找到一个合适的计划 增加有一次运行次数
        """
        # 第一次 先找还没有完成的
        for plan in self.plan_list:
            if not self._is_same_plan(plan, to_add):
                continue
            if plan.run_times >= plan.plan_times:
                continue
            plan.run_times += 1
            self.save()
            return

        # 第二次 就随便加一个
        for plan in self.plan_list:
            if not self._is_same_plan(plan, to_add):
                continue
            plan.run_times += 1
            self.save()
            return

    def _is_same_plan(self, x: ChargePlanItem, y: ChargePlanItem) -> bool:
        if x is None or y is None:
            return False

        return (x.tab_name == y.tab_name
                and x.category_name == y.category_name
                and x.mission_type_name == y.mission_type_name
                and x.mission_name == y.mission_name)