from typing import Optional, Any, Union, List

from one_dragon.base.config.yaml_config import YamlConfig


class YamlConfigAdapter:

    def __init__(self, config: YamlConfig, field: str, default_val: Any = None,
                 getter_convert: Optional[str] = None,
                 setter_convert: Optional[str] = None):
        self.config: YamlConfig = config
        self.field: str = field
        self.default_val: Any = default_val
        self.getter_convert: Optional[str] = getter_convert
        self.setter_convert: Optional[str] = setter_convert

    def get_value(self) -> Any:
        # 获取self.field对应的property属性的值
        val = self._get_nested_value(self.field)
        if self.getter_convert == 'str':
            return str(val)
        elif self.getter_convert == 'int':
            return int(val)
        elif self.getter_convert == 'float':
            return float(val)
        else:
            return val

    def set_value(self, new_value: Any) -> None:
        if self.setter_convert == 'str':
            val = str(new_value)
        elif self.setter_convert == 'int':
            val = int(new_value)
        elif self.setter_convert == 'float':
            val = float(new_value)
        else:
            val = new_value

        self._set_nested_value(self.field, val)
        self.config.save()

    def _get_nested_value(self, field_path: Union[str, List[str]]) -> Any:
        current = self.config.data
        if isinstance(field_path, str):
            field_path = field_path.split('.')
        for key in field_path:
            if isinstance(current, dict):
                current = current.get(key, None)
                if current is None:
                    return self.default_val
            else:
                return self.default_val
        return current

    def _set_nested_value(self, field_path: Union[str, List[str]], value: Any) -> None:
        if isinstance(field_path, str):
            field_path = field_path.split('.')
        current = self.config.data
        for key in field_path[:-1]:
            if isinstance(current, dict):
                current = current.setdefault(key, {})
            else:
                current[key] = {}
                current = current[key]
        current[field_path[-1]] = value
