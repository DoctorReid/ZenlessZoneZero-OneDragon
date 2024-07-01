import os
from typing import Optional, List

from one_dragon.base.yaml_operator import YamlOperator
from one_dragon.utils import os_utils


class YamlConfig(YamlOperator):

    def __init__(self,
                 module_name: str,
                 instance_idx: Optional[int] = None,
                 sub_dir: Optional[List[str]] = None,
                 sample: bool = False,
                 mock: bool = False):
        self.instance_idx: Optional[int] = instance_idx
        """传入时 该配置为一个的脚本实例独有的配置"""

        self.sub_dir: Optional[List[str]] = sub_dir
        """配置所在的子目录"""

        self.module_name: str = module_name
        """配置文件名称"""

        self.mock: bool = mock
        """mock情况下 不读取文件 也不会实际保存 用于测试"""

        super().__init__(self.get_yaml_file_path(sample))

    def get_yaml_file_path(self, sample: bool = False) -> Optional[str]:
        """
        获取配置文件的路径
        :param sample: 是否有sample文件
        :return:
        """
        if self.mock:
            return None
        sub_dir = ['config']
        if self.instance_idx is not None:
            sub_dir.append('%02d' % self.instance_idx)
        if self.sub_dir is not None:
            sub_dir = sub_dir + self.sub_dir

        yml_path = os.path.join(os_utils.get_path_under_work_dir(*sub_dir), f'{self.module_name}.yml')
        sample_yml_path = os.path.join(os_utils.get_path_under_work_dir(*sub_dir), f'{self.module_name}.sample.yml')
        return sample_yml_path if sample and not os.path.exists(yml_path) else yml_path
