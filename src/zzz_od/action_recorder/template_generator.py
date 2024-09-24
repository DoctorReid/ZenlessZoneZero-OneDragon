import pickle
import os
from copy import deepcopy

import yaml

import numpy as np

from sklearn.cluster import KMeans
from sklearn.metrics import euclidean_distances

from gensim.models import Word2Vec as GSWord2Vec

from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log
from zzz_od.auto_battle.auto_battle_state import BattleStateEnum

from enum import Enum


class ImportantOperation(Enum):
    # 可自定义状态动作至模板

    LEFT_CLICK = 'mouse_left'
    RIGHT_CLICK = 'mouse_right'
    MIDDLE_CLICK = 'mouse_middle'
    CONSIDERED_MOUSE_SET = (LEFT_CLICK, RIGHT_CLICK, MIDDLE_CLICK)

    SPECIAL_SKILL = 'keyboard_e'
    ULTIMATE_SKILL = 'keyboard_q'
    BTN_SPACE = 'keyboard_space'
    PREVIOUS_AGENT = 'keyboard_c'
    CONSIDERED_KEYBOARD_SET = (SPECIAL_SKILL, ULTIMATE_SKILL, BTN_SPACE)

    LONG_PRESS_THRESHOLD = 0.5
    LONG_PRESS = '按下'
    SHORT_PRESS = '点按'

    DODGE_TRIGGER = '闪避状态'
    DODGE_YELLOW = '闪避识别-黄光'
    DODGE_RED = '闪避识别-红光'
    DODGE_AUDIO = '闪避识别-声音'

    # 简单操作转化
    SIMPLE_OPERATION = {LEFT_CLICK: BattleStateEnum.BTN_SWITCH_NORMAL_ATTACK.value,
                        # RIGHT_CLICK: BattleStateEnum.BTN_DODGE.value,
                        MIDDLE_CLICK: BattleStateEnum.BTN_LOCK.value,

                        SPECIAL_SKILL: BattleStateEnum.BTN_SWITCH_SPECIAL_ATTACK.value,

                        # BTN_SPACE: BattleStateEnum.BTN_SWITCH_NEXT.value,  # 换人
                        # PREVIOUS_AGENT: BattleStateEnum.BTN_SWITCH_PREV.value
                        }

    # 特殊操作转化
    SPECIAL_OPERATION = {(BattleStateEnum.STATUS_CHAIN_READY.value, LEFT_CLICK): BattleStateEnum.BTN_CHAIN_LEFT.value,  # 连携
                         (BattleStateEnum.STATUS_CHAIN_READY.value, RIGHT_CLICK): BattleStateEnum.BTN_CHAIN_RIGHT.value,
                         (BattleStateEnum.STATUS_CHAIN_READY.value, MIDDLE_CLICK): BattleStateEnum.BTN_CHAIN_CANCEL.value,

                         (BattleStateEnum.STATUS_QUICK_ASSIST_READY.value, BTN_SPACE): BattleStateEnum.BTN_SWITCH_NEXT.value,  # 快速支援
                         (BattleStateEnum.STATUS_QUICK_ASSIST_READY.value, PREVIOUS_AGENT): BattleStateEnum.BTN_SWITCH_PREV.value,

                         (DODGE_TRIGGER, BTN_SPACE): BattleStateEnum.BTN_SWITCH_NEXT.value,  # 切人闪避, 黄光红光声音
                         (DODGE_TRIGGER, PREVIOUS_AGENT): BattleStateEnum.BTN_SWITCH_PREV.value,
                         (DODGE_TRIGGER, RIGHT_CLICK): BattleStateEnum.BTN_DODGE.value,  # 不切人闪避

                         (BattleStateEnum.STATUS_ULTIMATE_READY.value, ULTIMATE_SKILL): BattleStateEnum.BTN_ULTIMATE.value  # 终结技


                         }

    # 更新动作优先级顺序
    STATUS_PRIORITY = [
        BattleStateEnum.STATUS_SPECIAL_READY.value,
        BattleStateEnum.STATUS_ULTIMATE_READY.value,
        BattleStateEnum.STATUS_QUICK_ASSIST_READY.value,
        BattleStateEnum.STATUS_CHAIN_READY.value,
        DODGE_TRIGGER
    ]



class PreProcessor:
    def __init__(self):
        # 直接读取log中保存的信息
        keyboard_action_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'keyboard_actions.pkl')
        with open(keyboard_action_file_path, 'rb') as file:  # 使用 'rb' 模式读取二进制文件
            self.keyboard_flows = pickle.load(file)

        mouse_action_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'mouse_actions.pkl')
        with open(mouse_action_file_path, 'rb') as file:  # 使用 'rb' 模式读取二进制文件
            self.mouse_flows = pickle.load(file)

        status_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'status.pkl')
        with open(status_file_path, 'rb') as file:  # 使用 'rb' 模式读取二进制文件
            self.status_flows = pickle.load(file)

        for index in range(len(self.status_flows)):
            agent_info = self.status_flows[index][1]['代理人顺序']
            if agent_info is not None:
                self.agent_info = agent_info  # 代理人配队信息
                break
        self.agent_names = [ag.split('-')[-1] for ag in self.agent_info[0]]
        self.agent_types = [ag.split('-')[-1] for ag in self.agent_info[1]]

        print()

    def keyboard_pre_process(self):
        # 键盘按键预处理
        new_keyboard_flows = []
        keyboard_timestamp = []
        temp_keyboard = {}
        for action in self.keyboard_flows:
            time_stamp = action[0]
            btn_series = action[1].split('|')

            btn = btn_series[-1]  # 键位名称

            is_release = 'release' in btn_series
            is_consider = btn in ImportantOperation.CONSIDERED_KEYBOARD_SET.value
            is_temporarily_catch = btn in temp_keyboard.keys()

            if (not is_temporarily_catch) and is_consider and (not is_release):
                temp_keyboard[btn] = time_stamp  # 按下按键

            if is_temporarily_catch and is_consider and is_release:
                delta_time = time_stamp - temp_keyboard[btn]  # 释放按键, 时间差

                if delta_time > ImportantOperation.LONG_PRESS_THRESHOLD.value:  # 长按或断按
                    new_keyboard_flows.append(({'op_name': btn,  # 需结合状态判定最终状态
                                                'way': ImportantOperation.LONG_PRESS.value,
                                                'press': round(delta_time, 1)}))
                else:
                    new_keyboard_flows.append(({'op_name': btn,
                                                'way': ImportantOperation.SHORT_PRESS.value}))

                keyboard_timestamp.append(temp_keyboard[btn])

                temp_keyboard.pop(btn)

        return new_keyboard_flows, keyboard_timestamp

    def mouse_pre_process(self):
        # 鼠标按键预处理
        # 尽管两个方法类似还是重写一次,方便后面各自修改
        new_mouse_flows = []
        mouse_timestamp = []
        temp_mouse = {}
        for action in self.mouse_flows:
            time_stamp = action[0]
            btn_series = action[1].split('|')

            btn = btn_series[-1]  # 键位名称

            is_release = 'release' in btn_series
            is_consider = btn in ImportantOperation.CONSIDERED_MOUSE_SET.value
            is_temporarily_catch = btn in temp_mouse.keys()

            if (not is_temporarily_catch) and is_consider and (not is_release):
                temp_mouse[btn] = time_stamp  # 按下按键

            if is_temporarily_catch and is_consider and is_release:
                delta_time = time_stamp - temp_mouse[btn]  # 释放按键, 时间差

                if delta_time > ImportantOperation.LONG_PRESS_THRESHOLD.value:  # 长按或短按
                    new_mouse_flows.append(({'op_name': btn,  # 需结合状态判定最终状态
                                                'way': ImportantOperation.LONG_PRESS.value,
                                                'press': round(delta_time, 1)}))
                else:
                    new_mouse_flows.append(({'op_name': btn,
                                                'way': ImportantOperation.SHORT_PRESS.value}))

                mouse_timestamp.append(temp_mouse[btn])

                temp_mouse.pop(btn)

        return new_mouse_flows, mouse_timestamp

    def status_pre_process(self):
        # 状态预处理
        status_template = {'timestamp': 0,
                            '代理人顺序': [],
                            BattleStateEnum.STATUS_SPECIAL_READY.value: 0,
                            BattleStateEnum.STATUS_ULTIMATE_READY.value: 0,
                            BattleStateEnum.STATUS_QUICK_ASSIST_READY.value: 0,
                            BattleStateEnum.STATUS_CHAIN_READY.value: 0,
                            '闪避状态': 0}

        new_status_flows = []

        for status in self.status_flows:
            time_stamp = status[0]
            details = status[1]

            agent_info = details['代理人顺序']

            updated_status = status_template.copy()

            if agent_info is None: # 可能出现连携动作, 更新至上一次识别状态
                # 连携技
                if details[BattleStateEnum.STATUS_CHAIN_READY.value] is not None:
                    new_status_flows[-1][BattleStateEnum.STATUS_CHAIN_READY.value] = \
                        [agent[0].split('-')[-1] for agent in details[BattleStateEnum.STATUS_CHAIN_READY.value]]

            else:  # 正常更新
                updated_status['代理人顺序'] = [agent.split('-')[-1] for agent in agent_info[0]]

                # 特殊技能
                if details[BattleStateEnum.STATUS_SPECIAL_READY.value] is not None:
                    updated_status[BattleStateEnum.STATUS_SPECIAL_READY.value] = 1
                else:
                    updated_status[BattleStateEnum.STATUS_SPECIAL_READY.value] = 0

                # 终结技能
                if details[BattleStateEnum.STATUS_ULTIMATE_READY.value] is not None:
                    updated_status[BattleStateEnum.STATUS_ULTIMATE_READY.value] = 1
                else:
                    updated_status[BattleStateEnum.STATUS_ULTIMATE_READY.value] = 0

                # 快速支援
                if details[BattleStateEnum.STATUS_QUICK_ASSIST_READY.value] is not None:
                    updated_status[BattleStateEnum.STATUS_QUICK_ASSIST_READY.value] = \
                        details[BattleStateEnum.STATUS_QUICK_ASSIST_READY.value][0].split('-')[-1]
                else:
                    updated_status[BattleStateEnum.STATUS_QUICK_ASSIST_READY.value] = 0

                # 无连携动作
                updated_status[BattleStateEnum.STATUS_CHAIN_READY.value] = 0

                # 闪避状态
                if details['闪避状态'][0]:
                    updated_status['闪避状态'] = details['闪避状态'][1]
                else:
                    updated_status['闪避状态'] = 0

                # 时间
                updated_status['timestamp'] = time_stamp

                # 更新
                new_status_flows.append(updated_status)

        return new_status_flows

    def _merge_status_and_ops(self, ops_flows: list, ops_timestamps: list, status_flows: list, nearest_pos: list):
        updated_handlers = []
        for index in range(len(ops_flows)):
            current_status = status_flows[int(nearest_pos[index])]
            current_ops = ops_flows[index]  # 匹配时间最接近的状态和操作

            ops = current_ops['op_name']

            updated_status = [ops_timestamps[index], {'states': None, '前台': current_status['代理人顺序'][0]}]  # 只记录前台角色

            # # # # # # # # # # # # # # # # # # 带状态复杂操作 # # # # # # # # # # # # # # # # # #
            # 没有更新操作则不加入
            is_updated = False
            updated_op_name = None
            updated_status_name = None
            for status in ImportantOperation.STATUS_PRIORITY.value:
                if (status, ops) in ImportantOperation.SPECIAL_OPERATION.value.keys():
                    if current_status[status] != 0:  # 发现有对应状态的操作

                        updated_op_name = ImportantOperation.SPECIAL_OPERATION.value[(status, ops)]
                        is_updated = True

                        if status == BattleStateEnum.STATUS_CHAIN_READY.value:  # 连携技特殊处理
                            if ops == ImportantOperation.LEFT_CLICK.value:
                                updated_status_name = '连携技-1-{}'.format(current_status[status][0])
                            elif ops == ImportantOperation.RIGHT_CLICK.value:
                                updated_status_name = '连携技-2-{}'.format(current_status[status][1])
                            elif ops == ImportantOperation.MIDDLE_CLICK.value:
                                updated_status_name = ['连携技-{}-{}'.format(i + 1, current_status[status][i])
                                                       for i in range(0, 2)]

                        elif status == '闪避状态':  # 闪避状态特殊处理
                            updated_status_name = current_status[status]

                        else:
                            updated_status_name = status

                if is_updated:  # 更新
                    # 合并状态和动作
                    updated_ops = current_ops.copy()
                    updated_ops['op_name'] = updated_op_name

                    updated_status = updated_status.copy()
                    updated_status[1]['states'] = updated_status_name
                    updated_status[1].update(updated_ops)

                    updated_handlers.append(updated_status)
                    break  # 每个操作只会对应一种状态

            if is_updated:
                continue

            # # # # # # # # # # # # # # # # # # 简单操作 # # # # # # # # # # # # # # # # # #
            if ops in ImportantOperation.SIMPLE_OPERATION.value.keys():
                updated_op_name = ImportantOperation.SIMPLE_OPERATION.value[ops]

                updated_status_name = '""'  # 打桩状态只有角色状态

                if ops == ImportantOperation.SPECIAL_SKILL.value:  # 特殊技特殊处理
                    if current_status[BattleStateEnum.STATUS_SPECIAL_READY.value] == 0:  # 不可长按
                        if current_ops['way'] == '按下':  # 改为点按
                            current_ops['way'] = '点按'
                            current_ops.pop('press')
                    else:  # 可长按
                        updated_status_name = BattleStateEnum.STATUS_SPECIAL_READY.value  # 更新状态
                        if current_ops['way'] == '按下':
                            current_ops['press'] = min([5.0, current_ops['press']])  # 最大长按5s

                # 更新
                updated_ops = current_ops.copy()
                updated_ops['op_name'] = updated_op_name

                updated_status = updated_status.copy()
                updated_status[1]['states'] = updated_status_name
                updated_status[1].update(updated_ops)

                updated_handlers.append(updated_status)

        return updated_handlers

    def _drop_duplicates(self, updated_flows: list):
        # 检查下一位状态, 如果相同, 去重
        unique_updated_flows = []
        previous_flow = deepcopy(updated_flows[0])
        repeat = 1
        for index in range(1, len(updated_flows)):
            if updated_flows[index][1] == previous_flow[1]:
                repeat += 1  # 记录重复次数
            else:
                if (repeat > 1) and (previous_flow[1]['op_name'] == BattleStateEnum.BTN_SWITCH_NORMAL_ATTACK.value):  # 普通攻击才会记录
                    previous_flow[1]['repeat'] = repeat
                unique_updated_flows.append(previous_flow)

                previous_flow = deepcopy(updated_flows[index])
                repeat = 1

        return unique_updated_flows

    def pre_process(self):
        # 预处理, 并匹配邻近时间
        new_keyboard_flows, keyboard_timestamp = self.keyboard_pre_process()
        new_mouse_flows, mouse_timestamp = self.mouse_pre_process()
        new_status_flows = self.status_pre_process()

        status_timestamp =  np.asarray([flow['timestamp'] for flow in new_status_flows], dtype=np.float64)

        # 找到动作最近的状态, 采用循环防止内存溢出
        keyboard_pos = []
        for index in range(len(keyboard_timestamp)):
            keyboard_pos.append(np.argmin(np.abs(keyboard_timestamp[index] - status_timestamp)))
        mouse_pos = []
        for index in range(len(mouse_timestamp)):
            mouse_pos.append(np.argmin(np.abs(mouse_timestamp[index] - status_timestamp)))

        # 连接动作与状态
        updated_keyboard_flows = self._merge_status_and_ops(new_keyboard_flows, keyboard_timestamp, new_status_flows, keyboard_pos)
        updated_mouse_flows = self._merge_status_and_ops(new_mouse_flows, mouse_timestamp, new_status_flows, mouse_pos)

        # 去重
        unique_updated_keyboard_flows = self._drop_duplicates(updated_keyboard_flows)
        unique_updated_mouse_flows = self._drop_duplicates(updated_mouse_flows)

        # 按时间戳合并动作
        merged_status_ops = unique_updated_keyboard_flows + unique_updated_mouse_flows
        merged_timestamps = [so[0] for so in merged_status_ops]

        # 按时间排序
        correct_pos = np.argsort(merged_timestamps)
        merged_status_ops = [merged_status_ops[pos] for pos in list(correct_pos)]

        return merged_status_ops


class SelfAdaptiveGenerator:
    # WORD2VEC
    KEY4WORD = ['前台', 'states', 'op_name', 'way', 'press', 'repeat']  # 构造句子考虑的单词

    VECTOR_SIZE = len(KEY4WORD) // 2  # 词向量维度, 动作组合有限, 没必要大维度, 避免维度灾难
    WINDOW_SIZE = 3  # 上下文窗口
    MIN_COUNT = 1  # 所有单词均需要考虑

    CBOW = 0  # CBOW模型更高效，适合小数据集和高频词

    MINIMUM_CLUSTER = 3  # 最小聚类数量

    AGENT_INDEX = 0
    ACTION_INDEX = 2

    def __init__(self, merged_status_ops: list, agent_names: list):
        self.status_ops_with_timestamp = merged_status_ops  # 已按时间顺序排好
        self.status_ops = [sot[1] for sot in self.status_ops_with_timestamp]

        self.agent_names = agent_names

        self.agent_groups = self._groupby_agents()

    def _groupby_agents(self):
        # 按角色分组分组
        groups = {}
        for agent in self.agent_names:
            groups[agent] = []

        # 每次切人后为一个大动作组合包
        previous_agent = self.status_ops[0]['前台']
        temp_combinations = [self.status_ops[0]]
        for index in range(1, len(self.status_ops)):
            current_agent = self.status_ops[index]['前台']

            if current_agent == previous_agent:
                temp_combinations.append(self.status_ops[index])
            else:
                groups[previous_agent].append(temp_combinations)

                temp_combinations = [self.status_ops[index]]

            previous_agent = current_agent

        return groups

    def _prepare_sentences(self, agent_groups: dict):
        # 构造语句和单词
        agent_sentences = {}  # 所有语句分开
        agent_comb_sentences = {}  # 语句按动作包进行连接
        for agent in self.agent_names:
            agent_sentences[agent] = []
            agent_comb_sentences[agent] = []

        for agent in self.agent_names:
            combinations = agent_groups[agent]
            for so in combinations:  # 按动作包顺序添加
                current_sentence = []
                for so_iter in so:
                    sentence = [str(so_iter[k]) if isinstance(so_iter[k], float) else so_iter[k] for k in self.KEY4WORD
                                if k in so_iter.keys()]  # 当前语句

                    agent_sentences[agent].append(sentence)  # 上下文无链接

                    current_sentence.extend(sentence)  # 同一个动作装填包内上下文直接连接

                agent_comb_sentences[agent].append(current_sentence)

        return agent_sentences, agent_comb_sentences

    def _word2vec(self, agent_comb_sentences: dict):
        # 无监督训练获取分词向量
        agent_models = {}
        for agent in self.agent_names:
            model = GSWord2Vec(agent_comb_sentences[agent],
                               vector_size=self.VECTOR_SIZE,
                               window=self.WINDOW_SIZE,
                               min_count=self.MIN_COUNT,
                               sg=self.CBOW,
                               workers=1)

            agent_models[agent] = model

        return agent_models

    def _estimate_cluster(self, agent_sentences: dict, agent_models: dict):
        # 获取每个语句的向量并进行短文本聚类
        agent_templates = {}

        for agent in self.agent_names:
            combinations = self.agent_groups[agent]
            sentences = agent_sentences[agent]
            model = agent_models[agent]

            # 平均法获取向量
            response_vectors = []
            for index in range(len(sentences)):
                response_vectors.append(np.mean([model.wv[word] for word in sentences[index]], axis=0))
            response_vectors = np.asarray(response_vectors)

            # 根据动作状态包内的数量获取期望的聚类数量
            num_comb = [len(comb) for comb in combinations]
            value_counts = np.bincount(num_comb)
            expected_cluster_num = max([self.MINIMUM_CLUSTER, int(np.argmax(value_counts))])

            # 用最简单的KMeans
            # 其实这里最适用层次聚类, 获取树状图之后再根据树状结构获取聚类数量, 但十分用户不友好
            # 密度聚类用不了
            cluster_instance = KMeans(n_clusters=expected_cluster_num, init='k-means++', random_state=20240919)
            cluster_instance.fit(response_vectors)

            labels = cluster_instance.labels_  # 标签
            cluster_centers = cluster_instance.cluster_centers_  # 聚类中心

            # 分别获取最接近聚类中心的动作状态
            distance_matrix = euclidean_distances(response_vectors, cluster_centers)
            nearest_action_status_pos = np.argmin(distance_matrix, axis=0)

            # 获取位置
            orders_in_combination = []  # 动作状态包中动作和状态所在的编号
            combination_id = []  # 所在的动作状态包
            for index, comb in enumerate(combinations):
                combination_id.extend([index] * len(comb))
                orders_in_combination.extend(list(range(len(comb))))

            # 所处的动作状态包
            nearest_combination_pos = np.asarray([combination_id[pos] for pos in nearest_action_status_pos])

            # 获取最接近点在对应动作状态包的位置
            _orders = np.asarray([orders_in_combination[pos] for pos in nearest_action_status_pos])

            # 根据上述位置重排, 获取正确顺序
            nearest_action_status_pos = nearest_action_status_pos[np.argsort(_orders)]
            nearest_combination_pos = nearest_combination_pos[np.argsort(_orders)]
            _orders = _orders[np.argsort(_orders)]

            # 获取代理人动作模板
            agent_templates[agent] = []
            for index in range(len(nearest_action_status_pos)):
                potential_so = self.agent_groups[agent][nearest_combination_pos[index]][_orders[index]]
                if (potential_so['states'] == '""') or (potential_so['states'] == BattleStateEnum.STATUS_SPECIAL_READY.value):
                    agent_templates[agent].append(potential_so)

        return agent_templates

    def _get_special_status_freq(self, agent_sentences: dict, key_status: str, index=0):
        # 获取特殊状态和对应动作的频率
        potential_actions = {}
        for agent in self.agent_names:
            for sentence in agent_sentences[agent]:
                if key_status in sentence[1]:
                    if sentence[index] not in potential_actions.keys():
                        potential_actions[(sentence[1], sentence[index])] = 1
                    else:
                        potential_actions[(sentence[1], sentence[index])] += 1

        selected_action = None
        maximum_num = 0
        for action in potential_actions.keys():
            if potential_actions[action] > maximum_num:
                maximum_num = potential_actions[action]
                selected_action = action

        return selected_action

    def _get_special_status_freq_by_agent(self, agent_sentences: dict, key_status: str, index=0):
        # 获取特殊状态和对应动作的频率
        selected_actions = {}
        for agent in self.agent_names:
            potential_actions = {}
            for sentence in agent_sentences[agent]:
                if key_status in sentence[1]:
                    if sentence[index] not in potential_actions.keys():
                        potential_actions[(sentence[1], sentence[index])] = 1
                    else:
                        potential_actions[(sentence[1], sentence[index])] += 1

            # 选取频率最大的动作
            selected_action = None
            maximum_num = 0
            for action in potential_actions.keys():
                if potential_actions[action] > maximum_num:
                    maximum_num = potential_actions[action]
                    selected_action = action

            selected_actions[agent] = selected_action

        return selected_actions

    def _get_switch_habit(self):
        agent_ids = {}
        for index in range(len(self.agent_names)):
            agent_ids[self.agent_names[index]] = index + 1

        # 获取切人习惯 (2-3人)
        switch_habits = {}
        for index, agent in enumerate(self.agent_names):
            potential_actions = {}
            for j in range(1, len(self.status_ops)):
                agent_info_now = self.status_ops[j - 1]  # 现在
                agent_info_next = self.status_ops[j]  # 下一个角色
                if (agent_info_now['前台'] == agent) and (agent_info_now['states'] == '""') and (agent_info_next['前台'] != agent):
                    action = None
                    aid_now = agent_ids[agent_info_now['前台']]
                    aid_next = agent_ids[agent_info_next['前台']]
                    if (aid_next == (aid_now + 1)) or ((aid_now > aid_next) and aid_next == 0):
                        action = BattleStateEnum.BTN_SWITCH_NEXT.value
                    elif (aid_now == (aid_next + 1)) or ((aid_now < aid_next) and aid_now == 0):
                        action = BattleStateEnum.BTN_SWITCH_PREV.value

                    if action is not None:
                        if action not in potential_actions.keys():
                            potential_actions[action] = 1
                        else:
                            potential_actions[action] += 1

            # 选取频率最大的动作
            selected_action = None
            maximum_num = 0
            for action in potential_actions.keys():
                if potential_actions[action] > maximum_num:
                    maximum_num = potential_actions[action]
                    selected_action = action

            switch_habits[agent] = selected_action

        return switch_habits


    def get_templates(self):
        agent_sentences, agent_comb_sentences = self._prepare_sentences(self.agent_groups)
        agent_models = self._word2vec(agent_sentences)
        agent_templates = self._estimate_cluster(agent_sentences, agent_models)

        # 特殊状态处理
        quick_assist = self._get_special_status_freq_by_agent(agent_sentences, BattleStateEnum.STATUS_QUICK_ASSIST_READY.value, self.ACTION_INDEX)
        dodge_reaction = self._get_special_status_freq_by_agent(agent_sentences, "闪避识别", self.ACTION_INDEX)
        ultimate_action = self._get_special_status_freq(agent_sentences, BattleStateEnum.STATUS_ULTIMATE_READY.value, self.AGENT_INDEX)
        chain_selection = self._get_special_status_freq_by_agent(agent_sentences, "连携技", self.ACTION_INDEX)
        switch_habits = self._get_switch_habit()

        special_status = {BattleStateEnum.STATUS_QUICK_ASSIST_READY.value: quick_assist,
                          "闪避识别": dodge_reaction,
                          BattleStateEnum.STATUS_ULTIMATE_READY.value: ultimate_action,
                          "连携技": chain_selection,
                          "换人习惯": switch_habits}


        return agent_templates, special_status

    def output_yaml(self, agent_templates: dict, special_status: dict):
        output_dict = {}  # 导出字典


        # # # # # # # # 可用终结技 # # # # # # # #
        if special_status[BattleStateEnum.STATUS_ULTIMATE_READY.value]:
            output_dict['allow_ultimate'] = [{'agent_name': '"{}"'.format(special_status[BattleStateEnum.STATUS_ULTIMATE_READY.value][1])}]


        # # # # # # # # 默认设置 # # # # # # # #
        output_dict['check_dodge_interval'] = 0.02
        output_dict['check_agent_interval'] = '[0.4, 0.6]'
        output_dict['check_special_attack_interval'] = '[0.4, 0.6]'
        output_dict['check_ultimate_interval'] = '[0.4, 0.6]'
        output_dict['check_chain_interval'] = '[0.9, 1.1]'
        output_dict['check_quick_interval'] = '[0.9, 1.1]'

        output_dict['scenes'] = []


        # # # # # # # # 闪避状态 # # # # # # # #
        handlers = []
        for agent in self.agent_names:
            action = special_status["闪避识别"][agent]
            if action is not None:
                handlers.append({'states': '"[前台-{}]"'.format(agent),
                                 'operations': [{'op_name': '"{}"'.format(action[1]), 'post_delay': 0.05}]})
            else:
                handlers.append({'states': '"[前台-{}]"'.format(agent),
                                 'operations': [{'op_name': '"{}"'.format(BattleStateEnum.BTN_SWITCH_NEXT.value),
                                                 'post_delay': 0.05}]})  # 默认切人

        triggers = {'triggers': '["{}", "{}", "{}"]'.format(ImportantOperation.DODGE_YELLOW.value,
                                                            ImportantOperation.DODGE_RED.value,
                                                            ImportantOperation.DODGE_AUDIO.value),
                    'interval': 1,
                    'handlers': handlers}

        output_dict['scenes'].append(triggers)


        # # # # # # # # 快速支援 # # # # # # # #
        handlers = []
        for agent in self.agent_names:
            action = special_status[BattleStateEnum.STATUS_QUICK_ASSIST_READY.value][agent]
            if action:
                handlers.append({'states': '"[前台-{}]"'.format(agent),
                                 'operations': [{'op_name': '"{}"'.format(action[1]), 'post_delay': 0.05}]})

        triggers = {'triggers': '["{}"]'.format(BattleStateEnum.STATUS_QUICK_ASSIST_READY.value),
                    'interval': 1,
                    'handlers': handlers}

        output_dict['scenes'].append(triggers)


        # # # # # # # # 连携技 # # # # # # # #
        handlers = []
        for agent in self.agent_names:
            action = special_status['连携技'][agent]
            if action:
                handlers.append({'states': '"[前台-{}] & [{}]"'.format(agent, action[0]),
                                 'operations': [{'op_name': '"{}"'.format(action[1]), 'post_delay': 0.05}]})

        # 添加邦布连携
        handlers.append({'states': '""',
                         'operations': [
                             {'op_name': '"{}"'.format(BattleStateEnum.BTN_SWITCH_NEXT.value), 'post_delay': 0.05}]})

        triggers = {'triggers': '["{}"]'.format(BattleStateEnum.STATUS_CHAIN_READY.value),
                    'interval': 0.2,
                    'handlers': handlers}

        output_dict['scenes'].append(triggers)


        # # # # # # # # 终结技 # # # # # # # #
        handlers = []
        action = special_status[BattleStateEnum.STATUS_ULTIMATE_READY.value]
        if action:
            handlers.append({'states': '"[前台-{}] & [{}] & ![按键-切换角色-下一个,0,1]"'.format(action[1], action[0]),
                             'operations': [{'op_name': '"{}"'.format(BattleStateEnum.BTN_ULTIMATE.value), 'post_delay': 0.1, 'repeat': 2}]})

        triggers = {'triggers': '["{}"]'.format(BattleStateEnum.STATUS_ULTIMATE_READY.value),
                    'interval': 1,
                    'handlers': handlers}

        output_dict['scenes'].append(triggers)


        # # # # # # # # 普通状态循环动作模板 # # # # # # # #
        switch_habits = special_status["换人习惯"]

        handlers = [{'state_template': "站场模板-未识别角色"}]
        for agent in self.agent_names:
            temporary_operations = {}  # 先载入动作状态,看是否需要合并
            for so in agent_templates[agent]:
                so = so.copy()  # 动作预处理
                state = so['states']
                so.pop('前台')  # 删除前台角色标记
                so.pop('states')  # 删除状态只保留动作
                so['op_name'] = '"{}"'.format(so['op_name'])  # 加上标识符

                if 'repeat' in so.keys():  # 如果有重复动作比如普通攻击连击,需要加上延时,否则会瞬间执行完,没有连击效果
                    so['post_delay'] = 0.1

                if state not in temporary_operations.keys():
                    temporary_operations[state] = [so]
                else:
                    temporary_operations[state].append(so)

            # 换人动作
            switch_habit = switch_habits[agent]
            if switch_habit is None:
                switch_habit = BattleStateEnum.BTN_SWITCH_NEXT.value  # 默认下一个人

            sub_handlers = []
            for state in temporary_operations.keys():
                so = temporary_operations[state]
                so.insert(0, {'op_name': '"{}"'.format(BattleStateEnum.BTN_MOVE_W.value), 'way': '"按下"'})  # 加上按W键
                if state == '""':  # 正常动作状态
                    so = (so +
                          [{'op_name': '"{}"'.format(BattleStateEnum.BTN_MOVE_W.value), 'way': '"松开"'}] +  # 松开W键
                          [{'op_name': '"{}"'.format(switch_habit), 'post_delay': 0.05}])  # 加上换人动作
                    sub_handlers.append({'states': '""', 'operations': so})
                else:  # 特殊状态
                    so = (so +
                          [{'op_name': '"{}"'.format(BattleStateEnum.BTN_MOVE_W.value), 'way': '"松开"'}])  # 松开W键
                    sub_handlers.insert(0, {'states': '"[{}]"'.format(state), 'operations': so})

                sub_handlers.insert(0, {'state_template': "通用模板-锁定敌人"})  # 锁定敌人,防止丢失目标

            handlers.append({'states': '"[前台-{}]"'.format(agent),
                             'sub_states': sub_handlers})

        triggers = {'triggers': [],
                    'interval': 0.35,
                    'handlers': handlers}

        output_dict['scenes'].append(triggers)


        # # # # # # # # 输出到 LOG文件夹下 YAML文件 # # # # # # # #
        yaml_path = os.path.join(os_utils.get_path_under_work_dir('.log'), '配队动作模板.yml')

        content: str = yaml.dump(output_dict, stream=None, allow_unicode=True, sort_keys=False)
        content = content.replace("'", "")

        with open(yaml_path, 'w', encoding='utf-8') as file:
            file.write(content)

        log.error("导出到YAML模板完毕...")

def _debug():
    pp = PreProcessor()
    merged_status_ops = pp.pre_process()

    sag = SelfAdaptiveGenerator(merged_status_ops, pp.agent_names)
    agent_templates, special_status = sag.get_templates()
    sag.output_yaml(agent_templates, special_status)


if __name__ == '__main__':
    _debug()
