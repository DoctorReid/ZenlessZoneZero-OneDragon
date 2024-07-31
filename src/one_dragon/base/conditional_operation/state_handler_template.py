from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig


class StateHandlerTemplate(YamlConfig):

    def __init__(self, sub_dir: str, template_id: str, template_name: str,
                 instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name=template_id,
            sub_dir=[sub_dir],
            instance_idx=instance_idx,
            sample=False
        )

        self.template_name: str = template_name
