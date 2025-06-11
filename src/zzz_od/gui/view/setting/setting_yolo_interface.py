from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon, HyperlinkCard

from one_dragon.utils.i18_utils import gt
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.log_display_card import LogDisplayCard
from one_dragon_qt.widgets.setting_card.common_download_card import ZipDownloaderSettingCard
from one_dragon_qt.widgets.setting_card.onnx_model_download_card import OnnxModelDownloadCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from zzz_od.config.model_config import get_flash_classifier_opts, get_hollow_zero_event_opts, \
    get_lost_void_det_opts, get_ocr_opts
from zzz_od.context.zzz_context import ZContext


class SettingYoloInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        VerticalScrollInterface.__init__(
            self,
            object_name='setting_yolo_interface',
            content_widget=None, parent=parent,
            nav_text_cn='模型选择'
        )

        self.ctx: ZContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        content_widget.add_widget(self._init_model_group())
        content_widget.add_widget(self._init_log_group())
        content_widget.add_stretch(1)

        return content_widget

    def _init_model_group(self) -> SettingCardGroup:
        group = SettingCardGroup(gt('模型', 'ui'))

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='下载说明', text='',
                                      url='')
        self.help_opt.linkButton.hide()
        self.help_opt.setContent('下载失败时 请尝试到「脚本环境」更改网络代理')
        group.addSettingCard(self.help_opt)

        self.ocr_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='OCR识别')
        self.ocr_opt.value_changed.connect(self.on_ocr_changed)
        self.ocr_opt.gpu_changed.connect(self.on_ocr_gpu_changed)
        group.addSettingCard(self.ocr_opt)

        self.flash_classifier_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='闪光识别')
        self.flash_classifier_opt.value_changed.connect(self.on_flash_classifier_changed)
        self.flash_classifier_opt.gpu_changed.connect(self.on_flash_classifier_gpu_changed)
        group.addSettingCard(self.flash_classifier_opt)

        self.hollow_zero_event_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='空洞格子识别')
        self.hollow_zero_event_opt.value_changed.connect(self.on_hollow_zero_event_changed)
        self.hollow_zero_event_opt.gpu_changed.connect(self.on_hollow_zero_event_gpu_changed)
        group.addSettingCard(self.hollow_zero_event_opt)

        self.lost_void_det_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='迷失之地识别')
        self.lost_void_det_opt.value_changed.connect(self.on_lost_void_det_changed)
        self.lost_void_det_opt.gpu_changed.connect(self.on_lost_void_det_gpu_changed)
        group.addSettingCard(self.lost_void_det_opt)

        return group

    def _init_log_group(self) -> SettingCardGroup:
        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        self.log_card = LogDisplayCard()
        log_group.addSettingCard(self.log_card)

        return log_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.init_ocr_opts()
        self.init_flash_classifier()
        self.init_hollow_zero_event_opts()
        self.init_lost_void_det_opts()

        self.log_card.start()

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.stop()

    def init_ocr_opts(self) -> None:
        self.ocr_opt.blockSignals(True)
        self.ocr_opt.set_options_by_list(get_ocr_opts())
        self.ocr_opt.setValue(self.ctx.model_config.ocr)
        self.ocr_opt.gpu_opt.setChecked(self.ctx.model_config.ocr_gpu)
        self.ocr_opt.check_and_update_display()
        self.ocr_opt.blockSignals(False)

    def init_flash_classifier(self) -> None:
        self.flash_classifier_opt.blockSignals(True)
        self.flash_classifier_opt.set_options_by_list(get_flash_classifier_opts())
        self.flash_classifier_opt.setValue(self.ctx.model_config.flash_classifier)
        self.flash_classifier_opt.gpu_opt.setChecked(self.ctx.model_config.flash_classifier_gpu)
        self.flash_classifier_opt.check_and_update_display()
        self.flash_classifier_opt.blockSignals(False)

    def init_hollow_zero_event_opts(self) -> None:
        self.hollow_zero_event_opt.blockSignals(True)
        self.hollow_zero_event_opt.set_options_by_list(get_hollow_zero_event_opts())
        self.hollow_zero_event_opt.setValue(self.ctx.model_config.hollow_zero_event)
        self.hollow_zero_event_opt.gpu_opt.setChecked(self.ctx.model_config.hollow_zero_event_gpu)
        self.hollow_zero_event_opt.check_and_update_display()
        self.hollow_zero_event_opt.blockSignals(False)

    def init_lost_void_det_opts(self) -> None:
        self.lost_void_det_opt.blockSignals(True)
        self.lost_void_det_opt.set_options_by_list(get_lost_void_det_opts())
        self.lost_void_det_opt.setValue(self.ctx.model_config.lost_void_det)
        self.lost_void_det_opt.gpu_opt.setChecked(self.ctx.model_config.lost_void_det_gpu)
        self.lost_void_det_opt.check_and_update_display()
        self.lost_void_det_opt.blockSignals(False)

    def on_ocr_changed(self, index: int, value: str) -> None:
        self.ctx.model_config.flash_classifier = value
        self.ocr_opt.check_and_update_display()

    def on_ocr_gpu_changed(self, value: bool) -> None:
        self.ctx.model_config.ocr_gpu = value

    def on_flash_classifier_changed(self, index: int, value: str) -> None:
        self.ctx.model_config.flash_classifier = value
        self.flash_classifier_opt.check_and_update_display()

    def on_flash_classifier_gpu_changed(self, value: bool) -> None:
        self.ctx.model_config.flash_classifier_gpu = value

    def on_hollow_zero_event_changed(self, index: int, value: str) -> None:
        self.ctx.model_config.hollow_zero_event = value
        self.hollow_zero_event_opt.check_and_update_display()

    def on_hollow_zero_event_gpu_changed(self, value: bool) -> None:
        self.ctx.model_config.hollow_zero_event_gpu = value

    def on_lost_void_det_changed(self, index: int, value: str) -> None:
        self.ctx.model_config.lost_void_det = value
        self.lost_void_det_opt.check_and_update_display()

    def on_lost_void_det_gpu_changed(self, value: bool) -> None:
        self.ctx.model_config.lost_void_det_gpu = value
