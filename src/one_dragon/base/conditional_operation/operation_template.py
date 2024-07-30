from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig


class OperationTemplate(YamlConfig):

    def __init__(self, sub_dir: str, module_name: str, template_name: str, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name=module_name,
            sub_dir=[sub_dir],
            instance_idx=instance_idx,
            sample=False
        )

        self.template_name: str = template_name
