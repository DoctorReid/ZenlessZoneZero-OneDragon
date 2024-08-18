import os
import shutil
from typing import Optional, List

from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.utils import os_utils


class YamlConfig(YamlOperator):

    def __init__(self,
                 module_name: str,
                 instance_idx: Optional[int] = None,
                 sub_dir: Optional[List[str]] = None,
                 sample: bool = False, copy_from_sample: bool = False,
                 is_mock: bool = False):
        self.instance_idx: Optional[int] = instance_idx
        """传入时 该配置为一个的脚本实例独有的配置"""

        self.sub_dir: Optional[List[str]] = sub_dir
        """配置所在的子目录"""

        self.module_name: str = module_name
        """配置文件名称"""

        self.is_mock: bool = is_mock
        """mock情况下 不读取文件 也不会实际保存 用于测试"""

        self._sample: bool = sample
        """是否有sample文件"""

        self._copy_from_sample: bool = copy_from_sample
        """配置文件不存在时 是否从sample文件中读取"""

        YamlOperator.__init__(self, self._get_yaml_file_path())

    def _get_yaml_file_path(self) -> Optional[str]:
        """
        获取配置文件的路径
        如果只有sample文件，就复制一个到实例文件夹下
        :return:
        """
        if self.is_mock:
            return None
        sub_dir = ['config']
        if self.instance_idx is not None:
            sub_dir.append('%02d' % self.instance_idx)
        if self.sub_dir is not None:
            sub_dir = sub_dir + self.sub_dir

        yml_path = os.path.join(os_utils.get_path_under_work_dir(*sub_dir), f'{self.module_name}.yml')
        sample_yml_path = os.path.join(os_utils.get_path_under_work_dir(*sub_dir), f'{self.module_name}.sample.yml')
        usage_yml_path = sample_yml_path if self._sample and not os.path.exists(yml_path) else yml_path
        use_sample = self._sample and not os.path.exists(yml_path)

        if use_sample and self._copy_from_sample:
            shutil.copyfile(sample_yml_path, yml_path)
            usage_yml_path = yml_path

        return usage_yml_path

    @property
    def is_sample(self) -> bool:
        """
        是否样例文件
        :return:
        """
        return self.file_path.endswith('.sample.yml')
