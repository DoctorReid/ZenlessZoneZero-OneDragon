
class ContextLazySignal:
    """
    用于存储懒加载的信号状态
    """
    def __init__(self):
        self._signals = {}

    @property
    def reload_banner(self) -> bool:
        """
        刷新主页背景
        """
        return self._signals.get('reload_banner', False)

    @reload_banner.setter
    def reload_banner(self, new_value: bool) -> None:
        self._signals['reload_banner'] = new_value

    @property
    def start_onedragon(self) -> bool:
        """
        启动一条龙
        """
        return self._signals.get('start_onedragon', False)

    @start_onedragon.setter
    def start_onedragon(self, new_value: bool) -> None:
        self._signals['start_onedragon'] = new_value

    @property
    def config_loaded(self) -> bool:
        """
        配置加载完成
        """
        return self._signals.get('config_loaded', False)

    @config_loaded.setter
    def config_loaded(self, new_value: bool) -> None:
        self._signals['config_loaded'] = new_value

    @property
    def ocr_loaded(self) -> bool:
        """
        OCR模型加载完成
        """
        return self._signals.get('ocr_loaded', False)

    @ocr_loaded.setter
    def ocr_loaded(self, new_value: bool) -> None:
        self._signals['ocr_loaded'] = new_value
