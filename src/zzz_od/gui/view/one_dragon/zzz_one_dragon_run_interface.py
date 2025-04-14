from one_dragon.base.operation.one_dragon_app import OneDragonApp
from one_dragon.notify.notify_dialog import NotifyDialog
from one_dragon_qt.view.one_dragon.one_dragon_run_interface import OneDragonRunInterface
from zzz_od.application.zzz_one_dragon_app import ZOneDragonApp
from zzz_od.context.zzz_context import ZContext


class ZOneDragonRunInterface(OneDragonRunInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        OneDragonRunInterface.__init__(
            self,
            ctx=ctx,
            parent=parent,
            help_url='https://onedragon-anything.github.io/zzz/zh/docs/feat_one_dragon.html'
        )

    def on_interface_shown(self):
        super().on_interface_shown()
        self.notify_switch.init_with_adapter(self.ctx.notify_config.get_prop_adapter('enable_notify'))

    def get_one_dragon_app(self) -> OneDragonApp:
        return ZOneDragonApp(self.ctx)

    def _on_notify_setting_clicked(self) -> None:
        dialog = NotifyDialog(self, ctx=self.ctx)
        if dialog.exec():
            selected_apps = dialog.get_selected_apps()
            for app_id, is_checked in selected_apps.items():
                setattr(self.ctx.notify_config, f'enable_{app_id}', is_checked)
