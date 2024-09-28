from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.compendium.compendium_choose_category import CompendiumChooseCategory
from zzz_od.operation.compendium.compendium_choose_mission_type import CompendiumChooseMissionType
from zzz_od.operation.compendium.compendium_choose_tab import CompendiumChooseTab
from zzz_od.operation.compendium.open_compendium import OpenCompendium
from zzz_od.operation.zzz_operation import ZOperation


class TransportByCompendium(ZOperation):

    def __init__(self, ctx: ZContext, tab_name: str, category_name: str, mission_type_name: str):
        """
        使用快捷手册传送 最后不会等待加载完毕
        :param ctx:
        """
        ZOperation.__init__(
            self, ctx,
            op_name='%s %s %s-%s-%s' % (
                gt('传送'),
                gt('快捷手册'),
                gt(tab_name), gt(category_name), gt(mission_type_name)
            )
        )

        self.tab_name: str = tab_name
        self.category_name: str = category_name
        self.mission_type_name: str = mission_type_name

        if self.mission_type_name == '自定义模板':  # 没法直接传送到自定义
            self.mission_type_name: str = '基础材料'

    @operation_node(name='快捷手册', is_start_node=True)
    def open_compendium(self) -> OperationRoundResult:
        op = OpenCompendium(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='快捷手册')
    @operation_node(name='选择TAB')
    def choose_tab(self) -> OperationRoundResult:
        op = CompendiumChooseTab(self.ctx, self.tab_name)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择TAB')
    @operation_node(name='选择分类')
    def choose_category(self) -> OperationRoundResult:
        op = CompendiumChooseCategory(self.ctx, self.category_name)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择分类')
    @operation_node(name='选择副本分类')
    def choose_mission_type(self) -> OperationRoundResult:
        op = CompendiumChooseMissionType(self.ctx, self.mission_type_name)
        return self.round_by_op_result(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    op = TransportByCompendium(ctx, '训练', '定期清剿', '疯子与追随者')
    op.execute()


if __name__ == '__main__':
    __debug()
