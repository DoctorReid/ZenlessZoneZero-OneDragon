import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, setTheme, Theme,setThemeColor
from one_dragon.gui.app.fluent_window_base import FluentWindowBase
from one_dragon.gui.common.od_style_sheet import OdStyleSheet
from one_dragon.gui.view.code_interface import CodeInterface
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.battle_assistant.battle_assistant_interface import BattleAssistantInterface
from zzz_od.gui.view.devtools.app_devtools_interface import AppDevtoolsInterface
from zzz_od.gui.view.hollow_zero.hollow_zero_interface import HollowZeroInterface
from zzz_od.gui.view.home_interface import HomeInterface
from zzz_od.gui.view.one_dragon.zzz_one_dragon_interface import ZOneDragonInterface
from zzz_od.gui.view.setting.app_setting_interface import AppSettingInterface


# 定义应用程序的主窗口类
class AppWindow(FluentWindowBase):

    def __init__(self, ctx: ZContext, parent=None):
        """初始化主窗口类，设置窗口标题和图标"""
        self.ctx: ZContext = ctx
        super().__init__(
            ctx=ctx,
            win_title=ctx.project_config.project_name,
            app_icon='zzz_logo.ico',
            parent=parent
        )

    # 继承初始化函数
    def init_window(self):
        super().init_window()

        # 初始化位置
        self.move(100, 100)

        # 设置配置ID
        self.setObjectName("OneDragonWindow")
        self.navigationInterface.setObjectName("NavigationInterface")
        self.stackedWidget.setObjectName("StackedWidget")
        self.titleBar.setObjectName("TitleBar")    

        # 布局样式调整
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget.setContentsMargins(4, 24, 4, 0)
        self.navigationInterface.setContentsMargins(4, 24, 4, 0)

        # 配置样式
        OdStyleSheet.APP_WINDOW.apply(self)
        OdStyleSheet.NAVIGATION_INTERFACE.apply(self.navigationInterface)
        OdStyleSheet.STACKED_WIDGET.apply(self.stackedWidget)
        OdStyleSheet.TITLE_BAR.apply(self.titleBar)

        # DEBUG       
        print("————APP WINDOW STYLE————")                 
        print(self.styleSheet())         
        print("————NAVIGATION INTERFACE STYLE————")                 
        print(self.navigationInterface.styleSheet())    
        print("————STACKED WIDGET STYLE————")                 
        print(self.stackedWidget.styleSheet())    
        print("————TITLE BAR STYLE————")                 
        print(self.titleBar.styleSheet())    

        # 开启磨砂效果
        self.setAeroEffectEnabled(True)

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

        # 开发工具
        self.add_sub_interface(AppDevtoolsInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)

        # 代码同步
        self.add_sub_interface(CodeInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)

        # 设置
        self.add_sub_interface(AppSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)


# 初始化应用程序，并启动主窗口
if __name__ == '__main__':
    app = QApplication(sys.argv)

    _ctx = ZContext()

    # 加载配置
    _ctx.init_by_config()

    # 设置主题
    setTheme(Theme[_ctx.env_config.theme.upper()])

    # 创建并显示主窗口
    w = AppWindow(_ctx)

    w.show()
    w.activateWindow()

    # 启动应用程序事件循环
    app.exec()
