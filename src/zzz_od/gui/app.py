try:
    import sys
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtWidgets import QApplication
    from qfluentwidgets import NavigationItemPosition, setTheme, Theme
    from one_dragon.gui.view.like_interface import LikeInterface
    from one_dragon.base.operation.one_dragon_context import ContextInstanceEventEnum

    from phosdeiz.gui.services import PhosStyleSheet

    from one_dragon.gui.view.code_interface import CodeInterface
    from one_dragon.gui.view.context_event_signal import ContextEventSignal
    from one_dragon.gui.windows.app_window_base import AppWindowBase
    from one_dragon.utils.i18_utils import gt

    from zzz_od.context.zzz_context import ZContext
    from zzz_od.gui.view import (
        AppDevtoolsInterface,
        GameAssistantInterface,
        HollowZeroInterface,
        HomeInterface,
        ZOneDragonInterface,
        AppSettingInterface,
        BattleAssistantInterface,
    )

    _init_error = None


    class CheckVersionRunner(QThread):

        get = Signal(str)

        def __init__(self, ctx: ZContext, parent=None):
            super().__init__(parent)
            self.ctx = ctx

        def run(self):
            ver = self.ctx.git_service.get_current_version()
            if ver is not None:
                self.get.emit(ver)

    # 定义应用程序的主窗口类
    class AppWindow(AppWindowBase):

        def __init__(self, ctx: ZContext, parent=None):
            """初始化主窗口类，设置窗口标题和图标"""
            self.ctx: ZContext = ctx
            AppWindowBase.__init__(
                self,
                win_title="%s %s"
                % (
                    gt(ctx.project_config.project_name, "ui"),
                    ctx.one_dragon_config.current_active_instance.name,
                ),
                project_config=ctx.project_config,
                app_icon="zzz_logo.ico",
                parent=parent,
            )
            self._check_version_runner = CheckVersionRunner(self.ctx)
            self._check_version_runner.get.connect(self._update_version)
            self._check_version_runner.start()

            self.ctx.listen_event(
                ContextInstanceEventEnum.instance_active.value,
                self._on_instance_active_event,
            )
            self._context_event_signal: ContextEventSignal = ContextEventSignal()
            self._context_event_signal.instance_changed.connect(
                self._on_instance_active_signal
            )

        # 继承初始化函数
        def init_window(self):
            self.resize(960, 700)

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
            PhosStyleSheet.APP_WINDOW.apply(self)
            PhosStyleSheet.NAVIGATION_INTERFACE.apply(self.navigationInterface)
            PhosStyleSheet.STACKED_WIDGET.apply(self.stackedWidget)
            PhosStyleSheet.AREA_WIDGET.apply(self.areaWidget)
            PhosStyleSheet.TITLE_BAR.apply(self.titleBar)

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
            """创建和添加各个子界面"""

            # 主页
            self.add_sub_interface(HomeInterface(self.ctx, parent=self))

            # 战斗助手
            self.add_sub_interface(BattleAssistantInterface(self.ctx, parent=self))

            # 一条龙
            self.add_sub_interface(ZOneDragonInterface(self.ctx, parent=self))

            # 空洞
            self.add_sub_interface(HollowZeroInterface(self.ctx, parent=self))

            # 游戏助手
            self.add_sub_interface(GameAssistantInterface(self.ctx, parent=self))

            # 点赞
            self.add_sub_interface(
                LikeInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            # 开发工具
            self.add_sub_interface(
                AppDevtoolsInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            # 代码同步
            self.add_sub_interface(
                CodeInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

            # 设置
            self.add_sub_interface(
                AppSettingInterface(self.ctx, parent=self),
                position=NavigationItemPosition.BOTTOM,
            )

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

        def _update_version(self, ver: str) -> None:
            """
            更新版本显示
            @param ver:
            @return:
            """
            self.titleBar.setVersion(ver)


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

    _ctx = ZContext()

    # 加载配置
    _ctx.init_by_config()

    # 异步加载OCR
    _ctx.async_init_ocr()

    # 异步更新免费代理
    _ctx.async_update_gh_proxy()

    # 设置主题
    setTheme(Theme[_ctx.env_config.theme.upper()])

    # 创建并显示主窗口
    w = AppWindow(_ctx)

    w.show()
    w.activateWindow()

    # 启动应用程序事件循环
    app.exec()

    _ctx.btn_listener.stop()
