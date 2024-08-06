import os
import shutil
from typing import List, Optional

from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.utils import os_utils


class OneDragonInstance:

    def __init__(self, idx: int, name: str, active: bool, active_in_od: bool):
        self.idx: int = idx
        self.name: str = name
        self.active: bool = active
        self.active_in_od: bool = active_in_od


class OneDragonConfig(YamlConfig):

    def __init__(self):
        self.instance_list: List[OneDragonInstance] = []
        YamlConfig.__init__(self, 'zzz_one_dragon', sample=False)

    def _init_after_read_file(self):
        self._init_instance_list()

    def _init_instance_list(self):
        """
        初始化账号列表
        :return:
        """
        instance_list = self.dict_instance_list

        self.instance_list.clear()
        for instance in instance_list:
            self.instance_list.append(OneDragonInstance(**instance))

    def create_new_instance(self, first: bool) -> OneDragonInstance:
        """
        创建一个新的脚本账号
        :param first:
        :return:
        """
        idx = 0
        while True:
            idx += 1
            existed: bool = False
            for instance in self.instance_list:
                if instance.idx == idx:
                    existed = True
                    break
            if not existed:
                break

        new_instance = OneDragonInstance(idx, '账号%02d' % idx, first, True)
        self.instance_list.append(new_instance)

        dict_instance_list = self.dict_instance_list
        dict_instance_list.append(vars(new_instance))
        self.dict_instance_list = dict_instance_list

        return new_instance

    def update_instance(self, to_update: OneDragonInstance):
        """
        更新一个账号
        :param to_update:
        :return:
        """
        dict_instance_list = self.dict_instance_list

        for instance in dict_instance_list:
            if instance['idx'] == to_update.idx:
                instance['name'] = to_update.name
                instance['active_in_od'] = to_update.active_in_od

        self.save()
        self._init_instance_list()

    def active_instance(self, instance_idx: int):
        """
        启用一个账号
        :param instance_idx:
        :return:
        """
        dict_instance_list = self.dict_instance_list

        for instance in dict_instance_list:
            instance['active'] = instance['idx'] == instance_idx

        self.save()
        self._init_instance_list()

    def delete_instance(self, instance_idx: int):
        """
        删除一个账号
        :param instance_idx:
        :return:
        """
        idx = -1

        dict_instance_list = self.dict_instance_list
        for i in range(len(dict_instance_list)):
            if dict_instance_list[i]['idx'] == instance_idx:
                idx = i
                break
        if idx != -1:
            dict_instance_list.pop(idx)
        self.dict_instance_list = dict_instance_list

        instance_dir = os_utils.get_path_under_work_dir('config', ('%02d' % instance_idx))
        if os.path.exists(instance_dir):
            shutil.rmtree(instance_dir)

        self.save()
        self._init_instance_list()

    @property
    def dict_instance_list(self) -> List[dict]:
        return self.get('instance_list', [])

    @dict_instance_list.setter
    def dict_instance_list(self, new_list: List[dict]):
        self.update('instance_list', new_list)

    @property
    def current_active_instance(self) -> Optional[OneDragonInstance]:
        """
        获取当前激活使用的账号
        :return:
        """
        for instance in self.instance_list:
            if instance.active:
                return instance
        return None

    @property
    def app_order(self) -> List[str]:
        """
        运行顺序
        :return:
        """
        return self.get("app_order", [])

    @app_order.setter
    def app_order(self, new_list: List[str]):
        self.update('app_order', new_list)

    def move_up_app(self, app_id: str) -> None:
        """
        将一个app的执行顺序往前调一位
        :param app_id:
        :return:
        """
        old_app_orders = self.app_order
        idx = -1

        for i in range(len(old_app_orders)):
            if old_app_orders[i] == app_id:
                idx = i
                break

        if idx <= 0:  # 无法交换
            return

        temp = old_app_orders[idx - 1]
        old_app_orders[idx - 1] = old_app_orders[idx]
        old_app_orders[idx] = temp

        self.app_order = old_app_orders

    @property
    def app_run_list(self) -> List[str]:
        """
        运行顺序
        :return:
        """
        return self.get("app_run_list", [])

    @app_run_list.setter
    def app_run_list(self, new_list: List[str]):
        self.update('app_run_list', new_list)

    def set_app_run(self, app_id: str, to_run: bool) -> None:
        app_run_list = self.app_run_list
        if to_run and app_id not in app_run_list:
            app_run_list.append(app_id)
        elif not to_run:
            app_run_list.remove(app_id)
        self.app_run_list = app_run_list
