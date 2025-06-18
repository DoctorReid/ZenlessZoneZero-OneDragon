try:
    import sys
    from typing import Tuple
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtWidgets import QApplication
    from qfluentwidgets import NavigationItemPosition, setTheme, Theme
    from one_dragon_qt.view.like_interface import LikeInterface
    from one_dragon.base.operation.one_dragon_context import ContextInstanceEventEnum

    from one_dragon_qt.services.styles_manager import OdQtStyleSheet

    from one_dragon_qt.view.code_interface import CodeInterface
    from one_dragon_qt.view.context_event_signal import ContextEventSignal
    from one_dragon_qt.windows.app_window_base import AppWindowBase
    from one_dragon_qt.windows.window import PhosTitleBar
    from one_dragon.utils import app_utils
    from one_dragon.utils.i18_utils import gt

    from zzz_od.context.zzz_context import ZContext

    _init_error = None


    class CheckVersionRunner(QThread):

        get = Signal(tuple)

        def __init__(self, ctx: ZContext, parent=None):
            super().__init__(parent)
            self.ctx = ctx

        def run(self):
            launcher_version = app_utils.get_launcher_version()
            code_version = self.ctx.git_service.get_current_version()
            versions = (launcher_version, code_version)
            self.get.emit(versions)

    # 定义应用程序的主窗口类
    class AppWindow(AppWindowBase):
        titleBar: PhosTitleBar

        def __init__(self, ctx: ZContext, parent=None):
            """初始化主窗口类，设置窗口标题和图标"""
            self.ctx: ZContext = ctx

            project_name = "Unknown Project"
            if ctx.project_config is not None and ctx.project_config.project_name is not None:
                project_name = ctx.project_config.project_name

            instance_name = "Default Instance"
            if ctx.one_dragon_config is not None and \
               ctx.one_dragon_config.current_active_instance is not None and \
               ctx.one_dragon_config.current_active_instance.name is not None:
                instance_name = ctx.one_dragon_config.current_active_instance.name

            AppWindowBase.__init__(
                self,
                win_title="%s %s"
                % (
                    gt(project_name, "ui"),
                    instance_name,
                ),
                project_config=ctx.project_config,
                app_icon="zzz_logo.ico",
                parent=parent,
            )

            self.ctx.listen_event(ContextInstanceEventEnum.instance_active.value, self._on_instance_active_event)
            self._context_event_signal: ContextEventSignal = ContextEventSignal()
            self._context_event_signal.instance_changed.connect(self._on_instance_active_signal)

            self._check_version_runner = CheckVersionRunner(self.ctx)
            self._check_version_runner.get.connect(self._update_version)
            self._check_version_runner.start()

            # 初始化加载状态
            self._loading_complete = False
            self._setup_loading_status()

            self._check_first_run()

        # 继承初始化函数
        def init_window(self):
            self.resize(1050, 700)

            # 初始化位置
            self.move(100, 100)

            # 设置配置ID
            self.setObjectName("PhosWindow")
            self.navigationInterface.setObjectName("NavigationInterface")
            self.stackedWidget.setObjectName("StackedWidget")
            self.titleBar.setObjectName("TitleBar")

            # 布局样式调整
            self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
            self.areaLayout.setContentsMargins(0, 32, 0, 0)
            self.navigationInterface.setContentsMargins(0, 0, 0, 0)

            # 配置样式
            OdQtStyleSheet.APP_WINDOW.apply(self)
            OdQtStyleSheet.NAVIGATION_INTERFACE.apply(self.navigationInterface)
            OdQtStyleSheet.STACKED_WIDGET.apply(self.stackedWidget)
            OdQtStyleSheet.AREA_WIDGET.apply(self.areaWidget)
            OdQtStyleSheet.TITLE_BAR.apply(self.titleBar)

            # DEBUG
            # print("————APP WINDOW STYLE————")
            # print(self.styleSheet())
            # print("————NAVIGATION INTERFACE STYLE————")
            # print(self.navigationInterface.styleSheet())
            # print("————STACKED WIDGET STYLE————")
            # print(self.stackedWidget.styleSheet())
            # print("————TITLE BAR STYLE————")
            # print(self.titleBar.styleSheet())

            # 开启磨砂效果
            # self.setAeroEffectEnabled(True)

        def create_sub_interface(self):
            """创建和添加各个子界面 - 分阶段创建"""

            from zzz_od.gui.view.home.home_interface import HomeInterface
            self.add_sub_interface(HomeInterface(self.ctx, parent=self))

            # 延迟加载其余界面
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self._create_remaining_interfaces)

        def _create_remaining_interfaces(self):  # Renamed from _create_heavy_interfaces
            """异步创建剩余的界面"""

            # 顶部项目
            from zzz_od.gui.view.battle_assistant.battle_assistant_interface import BattleAssistantInterface
            self.add_sub_interface(BattleAssistantInterface(self.ctx, parent=self))

            from zzz_od.gui.view.one_dragon.zzz_one_dragon_interface import ZOneDragonInterface
            self.add_sub_interface(ZOneDragonInterface(self.ctx, parent=self))

            from zzz_od.gui.view.hollow_zero.hollow_zero_interface import HollowZeroInterface
            self.add_sub_interface(HollowZeroInterface(self.ctx, parent=self))

            from zzz_od.gui.view.game_assistant.game_assistant import GameAssistantInterface
            self.add_sub_interface(GameAssistantInterface(self.ctx, parent=self))

            # 底部项目
            self.add_sub_interface(
                LikeInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            from zzz_od.gui.view.devtools.app_devtools_interface import AppDevtoolsInterface
            self.add_sub_interface(
                AppDevtoolsInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            self.add_sub_interface(
                CodeInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            from zzz_od.gui.view.accounts.app_accounts_interface import AccountsInterface
            self.add_sub_interface(
                AccountsInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            from zzz_od.gui.view.setting.app_setting_interface import AppSettingInterface
            self.add_sub_interface(
                AppSettingInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            self.splashScreen.finish()

        def _on_instance_active_event(self, event) -> None:
            """
            切换实例后 更新title 这是context的事件 不能更新UI
            :return:
            """
            self._context_event_signal.instance_changed.emit()

        def _on_instance_active_signal(self) -> None:
            """
            切换实例后 更新title 这是Signal 可以更新UI
            :return:
            """
            self.setWindowTitle(
                "%s %s"
                % (
                    gt(self.ctx.project_config.project_name, "ui"),
                    self.ctx.one_dragon_config.current_active_instance.name,
                )
            )

        def _update_version(self, versions: Tuple[str, str]) -> None:
            """
            更新版本显示
            @param ver:
            @return:
            """
            self.titleBar.setVersion(versions[0], versions[1])

        def _check_first_run(self):
            """首次运行时显示防倒卖弹窗"""
            if self.ctx.env_config.is_first_run:
                from zzz_od.gui.widgets.zzz_welcome_dialog import ZWelcomeDialog
                dialog = ZWelcomeDialog(self)
                if dialog.exec():
                    self.ctx.env_config.is_first_run = False

        def _setup_loading_status(self):
            """设置加载状态指示器"""
            # 如果是懒加载模式，显示加载状态
            if hasattr(self.ctx, '_lazy_load_pending') and self.ctx._lazy_load_pending:
                from PySide6.QtCore import QTimer
                from qfluentwidgets import InfoBar, InfoBarPosition
                from PySide6.QtCore import Qt
                
                # 显示加载提示
                self._loading_info_bar = InfoBar.info(
                    title="正在初始化",
                    content="配置和模型正在后台加载中，请稍候...",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.TOP,
                    duration=-1,  # 不自动消失
                    parent=self,
                )
                
                # 定期检查加载状态
                self._loading_check_timer = QTimer()
                self._loading_check_timer.timeout.connect(self._check_loading_status)
                self._loading_check_timer.start(1000)  # 每秒检查一次

        def _check_loading_status(self):
            """检查加载状态"""
            config_loaded = not hasattr(self.ctx, '_lazy_load_pending') or not self.ctx._lazy_load_pending
            ocr_loaded = hasattr(self.ctx, 'signal') and self.ctx.signal.ocr_loaded
            
            if config_loaded and ocr_loaded:
                # 所有加载完成
                if hasattr(self, '_loading_info_bar'):
                    self._loading_info_bar.close()
                if hasattr(self, '_loading_check_timer'):
                    self._loading_check_timer.stop()
                self._loading_complete = True
                
                # 显示加载完成提示
                from qfluentwidgets import InfoBar, InfoBarPosition
                from PySide6.QtCore import Qt
                # InfoBar.success(
                #     title="初始化完成",
                #     content="配置和模型加载完成，可以正常使用了！",
                #     orient=Qt.Orientation.Horizontal,
                #     isClosable=True,
                #     position=InfoBarPosition.TOP,
                #     duration=3000,
                #     parent=self,
                # )
            elif config_loaded:
                # 配置加载完成，但OCR还在加载
                if hasattr(self, '_loading_info_bar'):
                    self._loading_info_bar.setContent("配置加载完成，OCR模型加载中...")
            elif ocr_loaded:
                # OCR加载完成，但配置还在加载
                if hasattr(self, '_loading_info_bar'):
                    self._loading_info_bar.setContent("OCR模型加载完成，配置加载中...")


# 调用Windows错误弹窗
except Exception as e:
    import ctypes
    import traceback

    stack_trace = traceback.format_exc()
    _init_error = f"启动一条龙失败，报错信息如下:\n{stack_trace}"


# 初始化应用程序，并启动主窗口
if __name__ == "__main__":
    if _init_error is not None:
        ctypes.windll.user32.MessageBoxW(0, _init_error, "错误", 0x10)
        sys.exit(1)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # 使用懒加载模式创建上下文，避免阻塞UI显示
    _ctx = ZContext(lazy_load=True)

    # 设置主题（使用基础配置）
    setTheme(Theme[_ctx.custom_config.theme.upper()])

    # 创建并显示主窗口
    w = AppWindow(_ctx)

    # 显示窗口
    w.show()
    w.activateWindow()

    # 在窗口显示后，异步加载完整配置
    _ctx.async_load_instance_config()

    # 异步加载OCR
    _ctx.async_init_ocr()

    # 异步更新免费代理
    _ctx.async_update_gh_proxy()

    # 启动应用程序事件循环
    app.exec()

    _ctx.after_app_shutdown()
