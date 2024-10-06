import os.path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import FluentIcon, PushButton, HyperlinkCard, ListWidget
from typing import Optional

from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.battle_assistant.auto_battle_app import AutoBattleApp
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_config_file_path, \
    get_auto_battle_op_config_list
from zzz_od.application.battle_assistant.auto_battle_debug_app import AutoBattleDebugApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.battle_assistant.battle_state_display import BattleStateDisplay


class AutoBattleInterface(AppRunInterface):

    auto_op_loaded_signal = Signal()

    def __init__(self, ctx: ZContext, parent=None):
        """初始化 AutoBattleInterface 类"""
        # 获取当前脚本所在的目录
        print("当前工作目录:", os.getcwd())
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 获取项目根目录 (跳过4级目录: src/zzz_od/gui/view/battle_assistant)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..', '..'))

        # 拼接 config 文件夹的绝对路径
        config_folder = os.path.join(project_root, 'config', 'auto_battle')

        # 自动生成配置文件字典，遍历 config_folder 下的所有 .sample.yml 文件
        self.config_files = {}
        if os.path.exists(config_folder):
            for file_name in os.listdir(config_folder):
                if file_name.endswith('.sample.yml'):
                    config_key = os.path.splitext(os.path.splitext(file_name)[0])[0]
                    self.config_files[config_key] = os.path.join(config_folder, file_name)

        # 打印生成的配置文件路径
        print("自动生成的配置文件路径:", self.config_files)

        # 尝试读取默认的配置文件
        default_config = '专属配队-朱鸢-通用击破'  # 不包含扩展名的文件名
        if default_config in self.config_files:
            try:
                with open(self.config_files[default_config], 'r', encoding='utf-8') as f:
                    config_content = f.read()
                    print("默认配置文件内容:", config_content)
            except FileNotFoundError as e:
                print(f"读取文件时出错: {e}")
        else:
            print(f"默认配置文件 '{default_config}' 不存在")

        AppRunInterface.__init__(self,
                                 ctx=ctx, object_name='auto_battle_interface', nav_text_cn='自动战斗', nav_icon=FluentIcon.GAME, parent=parent)
        self.ctx: ZContext = ctx
        self.app: Optional[ZApplication] = None
        self.auto_op_loaded_signal.connect(self._on_auto_op_loaded_signal)

    def get_widget_at_top(self) -> QWidget:
        top_widget = ColumnWidget()

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='使用说明', text='前往',
                                      url='https://one-dragon.org/zzz/zh/docs/feat_battle_assistant.html')
        self.help_opt.setContent('先看说明 再使用与提问')
        top_widget.add_widget(self.help_opt)

        self.config_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='战斗配置',
            content='调试为以当前画面做一次判断执行。配置文件在 config/auto_battle 文件夹，删除会恢复默认配置',
            show_tooltip=True
        )
        self.debug_btn = PushButton(text='调试')
        self.debug_btn.clicked.connect(self._on_debug_clicked)
        self.config_opt.hBoxLayout.addWidget(self.debug_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        self.del_btn = PushButton(text='删除')
        self.del_btn.clicked.connect(self._on_del_clicked)
        self.config_opt.hBoxLayout.addWidget(self.del_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        top_widget.add_widget(self.config_opt)
        self.config_opt.value_changed.connect(self._on_auto_battle_config_changed)

        self.gpu_opt = SwitchSettingCard(
            icon=FluentIcon.GAME, title='GPU运算',
            content='游戏画面掉帧的话 可以不启用'
        )
        self.gpu_opt.value_changed.connect(self._on_gpu_changed)
        top_widget.add_widget(self.gpu_opt)

        self.screenshot_interval_opt = TextSettingCard(
            icon=FluentIcon.GAME, title='截图间隔(秒)',
            content='游戏画面掉帧的话 可以适当加大截图间隔'
        )
        self.screenshot_interval_opt.value_changed.connect(self._on_screenshot_interval_changed)
        top_widget.add_widget(self.screenshot_interval_opt)

        self.gamepad_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='手柄类型',
            content='需先安装虚拟手柄依赖，参考文档或使用安装器。仅在战斗助手生效。',
            options_enum=GamepadTypeEnum
        )
        self.gamepad_type_opt.value_changed.connect(self._on_gamepad_type_changed)
        top_widget.add_widget(self.gamepad_type_opt)

        return top_widget

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        # 创建 QVBoxLayout 作为主布局
        main_layout = QVBoxLayout(content_widget)

        # 创建 QHBoxLayout 作为中间布局
        horizontal_layout = QHBoxLayout()

        # 将 QVBoxLayouts 加入 QHBoxLayout
        left_layout = QVBoxLayout()
        left_layout.addWidget(AppRunInterface.get_content_widget(self))

        right_layout = QVBoxLayout()

        # 替换 QListWidget 为 qfluentwidgets 的 ListWidget
        self.additional_list_widget = ListWidget(parent=self)
        
        # 添加示例项目
        self.additional_list_widget.addItem("在左侧选择新的战斗配置")
        self.additional_list_widget.addItem("此处将显示脚本须知")
        right_layout.addWidget(self.additional_list_widget)

        self.battle_state_display = BattleStateDisplay()
        right_layout.addWidget(self.battle_state_display)

        horizontal_layout.addLayout(left_layout, stretch=1)
        horizontal_layout.addLayout(right_layout, stretch=1)

        # 设置伸缩因子，让 QHBoxLayout 占据空间
        main_layout.addLayout(horizontal_layout, stretch=1)

        return content_widget

    def on_interface_shown(self) -> None:
        """
        界面显示时 进行初始化
        :return:
        """
        AppRunInterface.on_interface_shown(self)
        self._update_auto_battle_config_opts()
        self.config_opt.setValue(self.ctx.battle_assistant_config.auto_battle_config)
        self.gpu_opt.setValue(self.ctx.battle_assistant_config.use_gpu)
        self.screenshot_interval_opt.setValue(str(self.ctx.battle_assistant_config.screenshot_interval))
        self.gamepad_type_opt.setValue(self.ctx.battle_assistant_config.gamepad_type)
        self.debug_btn.setText('%s %s' % (self.ctx.key_debug.upper(), '调试'))
        self.ctx.listen_event(AutoBattleApp.EVENT_OP_LOADED, self._on_auto_op_loaded_event)

    def on_interface_hidden(self) -> None:
        AppRunInterface.on_interface_hidden(self)
        self.ctx.unlisten_all_event(self)
        self.battle_state_display.set_update_display(False)

    def _update_auto_battle_config_opts(self) -> None:
        """
        更新闪避指令
        :return:
        """
        try:
            self.config_opt.value_changed.disconnect(self._on_auto_battle_config_changed)
        except:
            pass
        self.config_opt.set_options_by_list(get_auto_battle_op_config_list('auto_battle'))
        self.config_opt.value_changed.connect(self._on_auto_battle_config_changed)

    def _on_auto_battle_config_changed(self, index, value):
        self.ctx.battle_assistant_config.auto_battle_config = value

    def _on_gpu_changed(self, value: bool):
        self.ctx.battle_assistant_config.use_gpu = value

    def _on_screenshot_interval_changed(self, value: str) -> None:
        self.ctx.battle_assistant_config.screenshot_interval = float(value)

    def get_app(self) -> ZApplication:
        return self.app

    def _on_start_clicked(self) -> None:
        """
        正常运行
        """
        self.app = AutoBattleApp(self.ctx)
        AppRunInterface._on_start_clicked(self)

    def _on_debug_clicked(self) -> None:
        """
        调试
        """
        self.app = AutoBattleDebugApp(self.ctx)
        AppRunInterface._on_start_clicked(self)

    def _on_del_clicked(self) -> None:
        """
        删除配置 只删除非 sample 的
        :return:
        """
        item: str = self.config_opt.getValue()
        if item is None:
            return

        path = get_auto_battle_config_file_path('auto_battle', item)
        if os.path.exists(path):
            os.remove(path)

        self._update_auto_battle_config_opts()

    def _on_gamepad_type_changed(self, idx: int, value: str) -> None:
        self.ctx.battle_assistant_config.gamepad_type = value

    def _on_key_press(self, event: ContextEventItem) -> None:
        """
        按键监听
        """
        key: str = event.data
        if key == self.ctx.key_start_running and self.ctx.is_context_stop:
            self._on_start_clicked()
        elif key == self.ctx.key_debug and self.ctx.is_context_stop:
            self._on_debug_clicked()

    def _on_context_state_changed(self) -> None:
        """
        按运行状态更新显示
        :return:
        """
        AppRunInterface._on_context_state_changed(self)

        if self.battle_state_display is not None:
            self.battle_state_display.set_update_display(self.ctx.is_context_running)

    def _on_auto_op_loaded_event(self, event: ContextEventItem) -> None:
        """
        自动战斗指令加载之后
        :param event:
        :return:
        """
        if self.battle_state_display is None:
            return
        self.battle_state_display.auto_op = event.data
        self.auto_op_loaded_signal.emit()

    def _on_auto_op_loaded_signal(self) -> None:
        """
        指令加载之后 更新需要监听的事件
        :return:
        """
        if self.battle_state_display is None:
            return
        self.battle_state_display.set_update_display(True)

    def _on_auto_battle_config_changed(self, index):
        selected_option = self.config_opt.combo_box.currentText()
        selected_file_path = self.config_files.get(selected_option)

        # 读取文件的前五行并显示在 ListWidget 中
        if selected_file_path:
            try:
                with open(selected_file_path, 'r', encoding='utf-8') as file:
                    self.additional_list_widget.clear()  # 清空列表
                    for i in range(5):
                        line = file.readline().strip()
                        if line:  # 只添加非空行
                            self.additional_list_widget.addItem(line)
            except Exception as e:
                self.additional_list_widget.clear()
                self.additional_list_widget.addItem(f"读取文件时出错: {e}")
        else:
            self.additional_list_widget.clear()
            self.additional_list_widget.addItem("未选择文件或路径无效")
