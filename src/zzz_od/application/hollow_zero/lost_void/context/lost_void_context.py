import os
from cv2.typing import MatLike
from typing import Optional, List

from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.base.screen import screen_utils
from one_dragon.utils import os_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.hollow_zero.lost_void.context.lost_void_artifact import LostVoidArtifact
from zzz_od.application.hollow_zero.lost_void.context.lost_void_detector import LostVoidDetector
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_dodge_context import YoloStateEventEnum
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import CommonAgentStateEnum


class LostVoidContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

        self.detector: Optional[LostVoidDetector] = None
        self.auto_op: Optional[AutoBattleOperator] = None  # 自动战斗指令

        self.all_artifact_list: List[LostVoidArtifact] = []  # 武备 + 鸣徽
        self.gear_by_name: dict[str, LostVoidArtifact] = {}  # key=名称 value=武备
        self.cate_2_artifact: dict[str, List[LostVoidArtifact]] = {}  # key=分类 value=藏品

    def init_before_run(self) -> None:
        self.init_lost_void_det_model()
        self.load_artifact_data()
        self.init_auto_op()

    def load_artifact_data(self) -> None:
        """
        加载 武备、鸣徽 信息
        @return:
        """
        self.all_artifact_list = []
        self.gear_by_name = {}
        self.cate_2_artifact = {}
        file_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'game_data', 'hollow_zero', 'lost_void'),
            'lost_void_artifact_data.yml'
        )
        yaml_op = YamlOperator(file_path)
        for yaml_item in yaml_op.data:
            artifact = LostVoidArtifact(**yaml_item)
            self.all_artifact_list.append(artifact)
            self.gear_by_name[artifact.name] = artifact
            if artifact.category not in self.cate_2_artifact:
                self.cate_2_artifact[artifact.category] = []
            self.cate_2_artifact[artifact.category].append(artifact)

    def init_lost_void_det_model(self):
        use_gpu = self.ctx.yolo_config.lost_void_det_gpu
        if self.detector is None or self.detector.gpu != use_gpu:
            use_gh_proxy = self.ctx.env_config.is_ghproxy
            self.detector = LostVoidDetector(
                model_name=self.ctx.yolo_config.lost_void_det,
                backup_model_name=self.ctx.yolo_config.lost_void_det_backup,
                gh_proxy=use_gh_proxy,
                personal_proxy=None if use_gh_proxy else self.ctx.env_config.personal_proxy,
                gpu=use_gpu
            )

    def init_auto_op(self) -> None:
        """
        初始化自动战斗指令
        @return:
        """
        if self.auto_op is not None:  # 如果有上一个 先销毁
            self.auto_op.dispose()
        self.auto_op = AutoBattleOperator(self.ctx, 'auto_battle', '全配队通用')
        success, msg = self.auto_op.init_before_running()
        if not success:
            raise Exception(msg)

    def check_battle_encounter(self, screen: MatLike, screenshot_time: float) -> bool:
        """
        判断是否进入了战斗
        1. 识别右上角文本提示
        2. 识别角色血量扣减
        3. 识别黄光红光
        @param screen: 游戏截图
        @param screenshot_time: 截图时间
        @return: 是否进入了战斗
        """
        if self.auto_op is not None:
            in_battle = self.auto_op.auto_battle_context.is_normal_attack_btn_available(screen)
            if in_battle:
                self.auto_op.auto_battle_context.agent_context.check_agent_related(screen, screenshot_time)
                state = self.auto_op.get_state_recorder(CommonAgentStateEnum.LIFE_DEDUCTION_31.value.state_name)
                if state is not None and state.last_record_time == screenshot_time:
                    return True

                self.auto_op.auto_battle_context.dodge_context.check_dodge_flash(screen, screenshot_time)
                state = self.auto_op.get_state_recorder(YoloStateEventEnum.DODGE_RED.value)
                if state is not None and state.last_record_time == screenshot_time:
                    return True
                state = self.auto_op.get_state_recorder(YoloStateEventEnum.DODGE_YELLOW.value)
                if state is not None and state.last_record_time == screenshot_time:
                    return True

        area = self.ctx.screen_loader.get_area('迷失之地-大世界', '区域-文本提示')
        if screen_utils.find_by_ocr(self.ctx, screen, target_cn='战斗开始', area=area):
            return True
        if screen_utils.find_by_ocr(self.ctx, screen, target_cn='侦测到最后的敌人', area=area):
            return True

        return False

    def match_artifact_by_ocr_full(self, name_full_str: str) -> Optional[LostVoidArtifact]:
        """
        使用 [类型]名称 的文本匹配 藏品
        :param name_full_str: 识别的文本 [类型]名称
        :return 藏品
        """
        name_full_str = name_full_str.strip()
        name_full_str = name_full_str.replace('[', '')
        name_full_str = name_full_str.replace(']', '')
        name_full_str = name_full_str.replace('【', '')
        name_full_str = name_full_str.replace('】', '')

        for cate, art_list in self.cate_2_artifact.items():
            cate_name = gt(cate)

            if cate != '卡牌':
                if len(name_full_str) < len(cate_name):
                    continue
                # 取出与分类名称长度一致的前缀 用来判断是否符合分类
                prefix = name_full_str[:len(cate_name)]

                if not str_utils.find_by_lcs(cate_name, prefix, percent=0.5):
                    continue

            # 符合分类的情况下 判断后缀和藏品名字是否一致
            for art in art_list:
                art_name = gt(art.name)
                suffix = name_full_str[-len(art_name):]
                if str_utils.find_by_lcs(art_name, suffix, percent=0.5):
                    return art
