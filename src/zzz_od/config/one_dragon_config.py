import os
import shutil
from typing import List, Optional

from one_dragon.base.config.yaml_config import YamlConfig


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
        self._init_account_list()

    def _init_account_list(self):
        """
        初始化账号列表
        :return:
        """
        account_list = self.dict_instance_list

        self.instance_list.clear()
        for account in account_list:
            self.instance_list.append(OneDragonInstance(**account))

    def create_new_account(self, first: bool) -> OneDragonInstance:
        """
        创建一个新的脚本账号
        :param first:
        :return:
        """
        idx = 0
        while True:
            idx += 1
            existed: bool = False
            for account in self.instance_list:
                if account.idx == idx:
                    existed = True
                    break
            if not existed:
                break

        new_account = OneDragonInstance(idx, '账号%02d' % idx, first, True)
        self.instance_list.append(new_account)

        dict_account_list = self.dict_instance_list
        dict_account_list.append(vars(new_account))
        self.dict_instance_list = dict_account_list

        return new_account

    def update_account(self, to_update: OneDragonInstance):
        """
        更新一个账号
        :param to_update:
        :return:
        """
        dict_account_list = self.dict_instance_list

        for account in dict_account_list:
            if account['idx'] == to_update.idx:
                account['name'] = to_update.name
                account['active_in_od'] = to_update.active_in_od

        self.save()
        self._init_account_list()

    def active_account(self, account_idx: int):
        """
        启用一个账号
        :param account_idx:
        :return:
        """
        dict_account_list = self.dict_instance_list

        for account in dict_account_list:
            account['active'] = account['idx'] == account_idx

        self.save()
        self._init_account_list()

    def delete_account(self, account_idx: int):
        """
        删除一个账号
        :param account_idx:
        :return:
        """
        idx = -1

        dict_account_list = self.dict_instance_list
        for i in range(len(dict_account_list)):
            if dict_account_list[i]['idx'] == account_idx:
                idx = i
                break
        if idx != -1:
            dict_account_list.pop(idx)
        self.dict_instance_list = dict_account_list

        account_dir = os_utils.get_path_under_work_dir('config', ('%02d' % account_idx))
        if os.path.exists(account_dir):
            shutil.rmtree(account_dir)

        self.save()
        self._init_account_list()

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
        for account in self.instance_list:
            if account.active:
                return account
        return None

    @property
    def is_debug(self) -> bool:
        """
        调试模式
        :return:
        """
        return self.get('is_debug', False)

    @is_debug.setter
    def is_debug(self, new_value: bool):
        """
        更新调试模式
        :return:
        """
        self.update('is_debug', new_value)
