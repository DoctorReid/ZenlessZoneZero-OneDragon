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
    from one_dragon.utils.log_utils import log
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
            
            # 如果是懒加载模式，先创建占位符界面
            if hasattr(self.ctx, '_lazy_load_pending') and self.ctx._lazy_load_pending:
                self._create_placeholder_interfaces()
                # 界面替换将由_check_loading_status方法控制
            else:
                # 直接创建真正的界面
                self._create_real_interfaces()

        def _create_placeholder_interfaces(self):
            """创建占位符界面"""
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            from PySide6.QtCore import Qt
            from qfluentwidgets import FluentIcon, NavigationItemPosition
            
            # 设置标志位
            self._has_placeholder_interfaces = True
            
            # 创建占位符导航项目
            placeholder_items = [
                # 顶部项目
                (FluentIcon.HOME, "仪表盘"),
                (FluentIcon.GAME, "战斗助手"),
                (FluentIcon.BUS, "一条龙"),
                (FluentIcon.IOT, "零号空洞"),
                (FluentIcon.HELP, "游戏助手"),
                # 底部项目
                (FluentIcon.HEART, "点赞", NavigationItemPosition.BOTTOM),
                (FluentIcon.DEVELOPER_TOOLS, "开发工具", NavigationItemPosition.BOTTOM),
                (FluentIcon.SYNC, "代码同步", NavigationItemPosition.BOTTOM),
                (FluentIcon.COPY, "账户管理", NavigationItemPosition.BOTTOM),
                (FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM),
            ]
            
            # 创建占位符界面
            for i, item in enumerate(placeholder_items):
                icon = item[0]
                text = item[1]
                position = item[2] if len(item) > 2 else NavigationItemPosition.TOP
                
                # 创建占位符界面
                placeholder_widget = self._create_placeholder_widget(text)
                placeholder_widget.setObjectName(f"placeholder_{i}")
                
                # 添加到导航栏
                self.addSubInterface(placeholder_widget, icon, text, position=position)
                
                # todo 点击仪表盘其他位置
            
            # 立即关闭启动画面，显示占位符界面
            if hasattr(self, 'splashScreen'):
                self.splashScreen.finish()

        def _create_placeholder_widget(self, interface_name: str):
            """创建单个占位符界面"""
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            from PySide6.QtCore import Qt, QTimer
            from qfluentwidgets import BodyLabel, TitleLabel
            
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(20)
            
            # 添加动态loading图标
            loading_label = QLabel("⏳")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet("font-size: 48px; margin: 20px;")
            layout.addWidget(loading_label)
            
            # 添加动画效果 - 让加载图标闪烁
            def toggle_loading():
                current_text = loading_label.text()
                if current_text == "⏳":
                    loading_label.setText("⌛")
                else:
                    loading_label.setText("⏳")
            
            timer = QTimer(widget)
            timer.timeout.connect(toggle_loading)
            timer.start(1000)  # 每秒切换一次
            widget._timer = timer  # 保持引用
            
            # 添加标题
            title_label = TitleLabel(f"{interface_name}")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)
            
            # 添加加载提示
            loading_text = BodyLabel("正在加载配置和模型...")
            loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_text.setStyleSheet("color: #888888; margin-top: 10px;")
            layout.addWidget(loading_text)
            
            # 添加提示信息
            info_label = BodyLabel("首次启动可能需要一些时间，请耐心等待")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 5px;")
            layout.addWidget(info_label)
            
            # 添加进度提示
            progress_label = BodyLabel("完成后会自动跳转到正常界面")
            progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            progress_label.setStyleSheet("color: #999999; font-size: 11px; margin-top: 10px; font-style: italic;")
            layout.addWidget(progress_label)
            
            # 设置最小大小
            widget.setMinimumSize(400, 350)
            
            return widget

        def _replace_with_real_interfaces(self):
            """替换占位符界面为真正的界面"""
            # 防止重复执行
            if not hasattr(self, '_has_placeholder_interfaces') or not self._has_placeholder_interfaces:
                return
                
            # 暂时断开信号连接，避免在清理过程中触发错误
            try:
                self.stackedWidget.currentChanged.disconnect()
            except:
                pass
            
            # 清理所有占位符界面
            self._clear_all_interfaces()
            
            # 创建真正的界面
            self._create_real_interfaces()
            
            # 重新连接信号
            try:
                self.stackedWidget.currentChanged.connect(self.init_interface_on_shown)
            except:
                pass
            
            # 清除标志位
            self._has_placeholder_interfaces = False
            
            # 强制更新界面显示
            try:
                self.update()
                self.stackedWidget.update()
                if hasattr(self, 'navigationInterface'):
                    self.navigationInterface.update()
                    
                # 触发当前界面的显示事件，确保更新检查能正常工作
                current_widget = self.stackedWidget.currentWidget()
                if current_widget and hasattr(current_widget, 'on_interface_shown'):
                    try:
                        current_widget.on_interface_shown()
                    except Exception as e:
                        log.error(f"触发界面显示事件失败: {e}")
                        
            except Exception as e:
                log.error(f"更新界面时出错: {e}")

        def _clear_all_interfaces(self):
            """清理所有界面和导航项"""
            # 先清理导航栏，避免导航事件触发
            if hasattr(self.navigationInterface, 'items') and self.navigationInterface.items:
                # 从布局中移除所有导航项目
                for route_key in list(self.navigationInterface.items.keys()):
                    try:
                        item = self.navigationInterface.items[route_key]
                        # 从所有可能的布局中移除
                        for layout in [self.navigationInterface.topLayout, 
                                     self.navigationInterface.scrollLayout, 
                                     self.navigationInterface.bottomLayout]:
                            try:
                                layout.removeWidget(item)
                            except:
                                pass
                        # 删除组件
                        item.deleteLater()
                    except Exception as e:
                        log.error(f"清理导航项目时出错: {e}")
                
                # 清空items字典
                self.navigationInterface.items.clear()
            
            # 清理stackedWidget中的所有界面
            widgets_to_remove = []
            for i in range(self.stackedWidget.count()):
                widget = self.stackedWidget.widget(i)
                if widget:
                    widgets_to_remove.append(widget)
            
            # 逐个移除组件
            for widget in widgets_to_remove:
                try:
                    if hasattr(self.stackedWidget, 'view'):
                        self.stackedWidget.view.removeWidget(widget)
                    else:
                        # 备用方法
                        widget.setParent(None)
                except Exception as e:
                    log.error(f"移除界面时出错: {e}")
                
                # 删除组件
                widget.deleteLater()

        def _create_real_interfaces(self):
            """创建真正的应用界面"""
            
            # 导入所需的界面类
            from zzz_od.gui.view.home.home_interface import HomeInterface
            from zzz_od.gui.view.battle_assistant.battle_assistant_interface import BattleAssistantInterface
            from zzz_od.gui.view.one_dragon.zzz_one_dragon_interface import ZOneDragonInterface
            from zzz_od.gui.view.hollow_zero.hollow_zero_interface import HollowZeroInterface
            from zzz_od.gui.view.game_assistant.game_assistant import GameAssistantInterface
            from zzz_od.gui.view.devtools.app_devtools_interface import AppDevtoolsInterface
            from zzz_od.gui.view.accounts.app_accounts_interface import AccountsInterface
            from zzz_od.gui.view.setting.app_setting_interface import AppSettingInterface
            from one_dragon_qt.view.like_interface import LikeInterface
            from one_dragon_qt.view.code_interface import CodeInterface
            from qfluentwidgets import NavigationItemPosition
            
            # 创建主界面
            try:
                home_interface = HomeInterface(self.ctx, parent=self)
                self.add_sub_interface(home_interface)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return
            
            # 顶部项目
            try:
                self.add_sub_interface(BattleAssistantInterface(self.ctx, parent=self))
                self.add_sub_interface(ZOneDragonInterface(self.ctx, parent=self))
                self.add_sub_interface(HollowZeroInterface(self.ctx, parent=self))
                self.add_sub_interface(GameAssistantInterface(self.ctx, parent=self))
            except Exception as e:
                log.error(f"创建顶部界面失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 底部项目
            try:
                self.add_sub_interface(
                    LikeInterface(self.ctx, parent=self),
                    position=NavigationItemPosition.BOTTOM,
                )
                self.add_sub_interface(
                    AppDevtoolsInterface(self.ctx, parent=self),
                    position=NavigationItemPosition.BOTTOM,
                )
                self.add_sub_interface(
                    CodeInterface(self.ctx, parent=self),
                    position=NavigationItemPosition.BOTTOM,
                )
                self.add_sub_interface(
                    AccountsInterface(self.ctx, parent=self),
                    position=NavigationItemPosition.BOTTOM,
                )
                self.add_sub_interface(
                    AppSettingInterface(self.ctx, parent=self),
                    position=NavigationItemPosition.BOTTOM,
                )

            except Exception as e:
                log.error(f"创建底部界面失败: {e}")
            
            # 确保设置主页为当前界面
            try:
                self.stackedWidget.setCurrentWidget(home_interface)
                self.navigationInterface.setCurrentItem(home_interface.objectName())
                
                # 手动触发主页的显示初始化
                if hasattr(home_interface, 'on_interface_shown'):
                    # 启动时只进行基础的界面更新，更新检查通过正常的界面显示触发
                    try:
                        # 先更新界面显示
                        home_interface.update()
                        if hasattr(home_interface, '_banner_widget'):
                            home_interface._banner_widget.update()
                        
                        # 调用父类的显示方法，确保界面正确初始化
                        from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
                        VerticalScrollInterface.on_interface_shown(home_interface)
                        
                    except Exception as e:
                        # 如果更新失败，忽略错误
                        log.error(f"手动初始化主页失败: {e}")
                        import traceback
                        traceback.print_exc()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                # 如果设置失败，尝试设置第一个界面
                if self.stackedWidget.count() > 0:
                    first_widget = self.stackedWidget.widget(0)
                    self.stackedWidget.setCurrentWidget(first_widget)
                    if hasattr(first_widget, 'objectName'):
                        self.navigationInterface.setCurrentItem(first_widget.objectName())
                    # 也尝试触发第一个界面的显示初始化
                    if hasattr(first_widget, 'on_interface_shown'):
                        # 只进行基础的显示初始化，避免触发可能的检查线程
                        try:
                            first_widget.update()
                        except Exception as e:
                            log.error(f"初始化第一个界面失败: {e}")


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
            
            # 如果配置加载完成且还有占位符界面，立即替换
            if config_loaded and hasattr(self, '_has_placeholder_interfaces') and self._has_placeholder_interfaces:
                self._replace_with_real_interfaces()
                self._has_placeholder_interfaces = False
            
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
