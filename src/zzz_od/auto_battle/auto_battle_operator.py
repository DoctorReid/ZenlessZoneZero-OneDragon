import time

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from zzz_od.auto_battle.auto_battle_loader import AutoBattleLoader
from zzz_od.context.zzz_context import ZContext


class AutoBattleOperator(ConditionalOperator):

    def __init__(self, ctx: ZContext, sub_dir: str, config_name: str):
        self.ctx: ZContext = ctx
        self.config_loader = AutoBattleLoader(self.ctx)

        ConditionalOperator.__init__(
            self,
            sub_dir=sub_dir,
            module_name=config_name
        )

    def init_operator(self):
        ConditionalOperator.init(
            self,
            event_bus=self.ctx,
            state_recorders=self.config_loader.get_all_state_recorders(),
            op_getter=self.config_loader.get_atomic_op,
            scene_handler_getter=self.config_loader.get_state_handler_template,
            operation_template_getter=self.config_loader.get_operation_template
        )


if __name__ == '__main__':
    ctx = ZContext()
    ctx.init_by_config()
    op = AutoBattleOperator(ctx, 'auto_battle', 'test')
    op.init_operator()
    ctx.dispatch_event('前台-艾莲', time.time())
    op.start_running_async()
    time.sleep(5)
    op.stop_running()
    time.sleep(1)
    pass