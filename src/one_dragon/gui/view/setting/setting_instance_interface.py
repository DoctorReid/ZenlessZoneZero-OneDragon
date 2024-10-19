from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, LineEdit, PushButton, \
    ToolButton, PrimaryPushButton, HyperlinkCard

from one_dragon.base.config.one_dragon_config import OneDragonInstance, RunInOneDragonApp
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.combo_box import ComboBox
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class InstanceSettingCard(MultiPushSettingCard):

    changed = Signal(OneDragonInstance)
    active = Signal(int)
    login = Signal(int)
    delete = Signal(int)

    def __init__(self, instance: OneDragonInstance):
        self.instance: OneDragonInstance = instance

        self.instance_name_input = LineEdit()
        self.instance_name_input.setText(self.instance.name)
        self.instance_name_input.textChanged.connect(self._on_name_changed)

        self.run_opt = ComboBox()
        run_idx = 0
        target_idx = 0
        for opt_enum in RunInOneDragonApp:
            opt = opt_enum.value
            self.run_opt.addItem(text=opt.label, userData=opt.value)
            if opt.value == self.instance.active_in_od:
                target_idx = run_idx

            run_idx += 1
        self.run_opt.setCurrentIndex(target_idx)
        self.run_opt.currentIndexChanged.connect(self._on_run_changed)

        self.active_btn = PushButton(text='启用')
        self.active_btn.clicked.connect(self._on_active_clicked)
        self.active_btn.setDisabled(self.instance.active)
        self.login_btn = PushButton(text='登录')
        self.login_btn.clicked.connect(self._on_login_clicked)
        self.delete_btn = ToolButton(FluentIcon.DELETE, parent=None)
        self.delete_btn.clicked.connect(self._on_delete_clicked)

        MultiPushSettingCard.__init__(
            self,
            btn_list=[self.instance_name_input, self.run_opt, self.active_btn, self.login_btn, self.delete_btn],
            title='%02d' % self.instance.idx,
            icon=FluentIcon.PEOPLE,
        )
        self.update_title()

    def update_title(self) -> None:
        """
        更新显示文本
        """
        title = '%02d' % self.instance.idx
        if self.instance.active:
            title += ' ' + gt('当前', 'ui')
        self.setTitle(title)

    def _on_name_changed(self, text: str) -> None:
        self.instance.name = text
        self.changed.emit(self.instance)

    def _on_run_changed(self, idx: int) -> None:
        self.instance.active_in_od = self.run_opt.itemData(idx)
        self.changed.emit(self.instance)

    def _on_active_clicked(self) -> None:
        self.active.emit(self.instance.idx)

    def _on_login_clicked(self) -> None:
        self.login.emit(self.instance.idx)

    def _on_delete_clicked(self) -> None:
        self.delete.emit(self.instance.idx)

    def check_active(self, active_idx: int) -> None:
        """
        检查是否现在启用的 更新显示
        :return:
        """
        active = active_idx == self.instance.idx
        self.instance.active = active
        self.update_title()
        self.active_btn.setDisabled(active)


class SettingInstanceInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        VerticalScrollInterface.__init__(
            self,
            object_name='setting_instance_interface',
            content_widget=None, parent=parent,
            nav_text_cn='实例设置'
        )
        self.ctx: OneDragonContext = ctx

    def get_content_widget(self) -> QWidget:
        """
        子界面内的内容组件 由子类实现
        :return:
        """
        self.content_widget = ColumnWidget()
        return self.content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self._init_content_widget()

    def _init_content_widget(self) -> None:
        """
        重新初始化显示
        :return:
        """
        self.instance_card_list = []
        self.content_widget.clear_widgets()

        guide_opt = HyperlinkCard(
            url='http://one-dragon.org/zzz/zh/docs/feat_one_dragon.html#_4-%E5%A4%9A%E8%B4%A6%E5%8F%B7',
            text='说明',
            icon=FluentIcon.INFO,
            title='注意',
            content='新实例需要点击启用后到各模块进行设置，各实例之间的设置是独立的。'
        )
        self.content_widget.add_widget(guide_opt)

        for instance in self.ctx.one_dragon_config.instance_list:
            instance_card = InstanceSettingCard(instance)
            self.instance_card_list.append(instance_card)
            self.content_widget.add_widget(instance_card)
            instance_card.changed.connect(self._on_instance_changed)
            instance_card.active.connect(self._on_instance_active)
            instance_card.login.connect(self._on_instance_login)
            instance_card.delete.connect(self._on_instance_delete)

        self.add_btn = PrimaryPushButton(text='新增')
        self.add_btn.clicked.connect(self._on_add_clicked)

        self.content_widget.add_widget(self.add_btn)
        self.content_widget.add_stretch(1)

    def _on_add_clicked(self) -> None:
        self.ctx.one_dragon_config.create_new_instance(False)
        self._init_content_widget()

    def _on_instance_changed(self, instance: OneDragonInstance) -> None:
        self.ctx.one_dragon_config.update_instance(instance)

    def _on_instance_active(self, idx: int) -> None:
        self.ctx.switch_instance(idx)

        for instance_card in self.instance_card_list:
            instance_card.check_active(idx)

    def _on_instance_login(self, idx: int) -> None:
        log.error('未配置登录操作')

    def _on_instance_delete(self, idx: int) -> None:
        if len(self.ctx.one_dragon_config.instance_list) <= 1:
            return

        self.ctx.one_dragon_config.delete_instance(idx)
        self._init_content_widget()
