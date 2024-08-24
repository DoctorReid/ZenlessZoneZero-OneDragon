import difflib
import re
from typing import Optional, List


def find(source: str, target: str, ignore_case: bool = False) -> int:
    """
    字符串find的封装 在原目标串中招目标字符串
    :param source: 原字符串
    :param target: 目标字符串
    :param ignore_case: 是否忽略大小写
    :return:
    """
    if source is None or target is None:
        return -1
    if ignore_case:
        return source.lower().find(target.lower())
    else:
        return source.find(target)


def find_by_lcs(source: str, target: str, percent: float = 0.3,
                ignore_case: bool = True) -> bool:
    """
    根据最长公共子序列长度和一定阈值 判断字符串是否有包含关系。
    用于OCR结果和目标的匹配
    :param source: OCR目标
    :param target: OCR结果
    :param percent: 最长公共子序列长度 需要占 source长度 的百分比
    :param ignore_case: 是否忽略大小写
    :return: 是否包含
    """
    if source is None or target is None or len(source) == 0 or len(target) == 0:
        return False
    source_usage = source.lower() if ignore_case else source
    target_usage = target.lower() if ignore_case else target

    common_length = longest_common_subsequence_length(source_usage, target_usage)

    return common_length >= len(source) * percent


def longest_common_subsequence_length(str1: str, str2: str) -> int:
    """
    找两个字符串的最长公共子序列长度
    :param str1:
    :param str2:
    :return: 长度
    """
    m = len(str1)
    n = len(str2)

    # 创建一个二维数组用于存储中间结果
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 动态规划求解
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def get_positive_digits(v: str, err: Optional[int] = None) -> Optional[int]:
    """
    返回字符串中的数字部分 不包含符号
    :param v: 字符串
    :param err: 原字符串中没有数字的话返回的值
    :return: 字符串中的数字
    """
    try:
        return int(remove_not_digit(v))
    except Exception:
        return err


def get_positive_float(v: str, err: Optional[int] = None) -> Optional[float]:
    """
    返回字符串中的数字部分 不包含符号
    :param v: 字符串
    :param err: 原字符串中没有数字的话返回的值
    :return: 字符串中的数字
    """
    try:
        fix = re.sub(r'[^\d.]+', '', v)
        return float(fix)
    except Exception:
        return err


def remove_not_digit(v: str) -> str:
    """
    移除字符串中的非数字部分
    :param v:
    :return:
    """
    return re.sub(r"\D", "", v)


def find_best_match_by_lcs(word: str, target_word_list: List[str],
                           lcs_percent_threshold: Optional[float] = None) -> Optional[int]:
    """
    在目标词中，找出LCS比例最大的
    :param word: 候选词
    :param target_word_list: 目标词列表
    :param lcs_percent_threshold: 要求的LCS阈值
    :return: 最符合的目标词的下标
    """
    target_idx: Optional[int] = None
    target_lcs_percent: Optional[float] = None

    for idx, target_word in enumerate(target_word_list):
        lcs = longest_common_subsequence_length(word, target_word)
        if lcs == 0:  # 至少要有一个匹配
            continue
        lcs_percent = lcs * 1.0 / len(target_word)
        if lcs_percent_threshold is not None and lcs_percent < lcs_percent_threshold:
            continue
        if target_idx is None or lcs_percent > target_lcs_percent:
            target_idx = idx
            target_lcs_percent = lcs_percent

    return target_idx


def find_most_similar(str_list1, str_list2):
    highest_similarity = 0
    most_similar_pair = (None, None)

    # 创建一个SequenceMatcher对象
    sequence_matcher = difflib.SequenceMatcher()

    # 遍历两个列表中的所有字符串组合
    for s1 in str_list1:
        for s2 in str_list2:
            # 设置要比较的两个字符串
            sequence_matcher.set_seqs(s1, s2)

            # 计算相似度比例
            similarity = sequence_matcher.ratio()

            # 如果当前相似度高于之前记录的最高相似度，则更新最高相似度和最相似的一对
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_similar_pair = (s1, s2)

    return most_similar_pair, highest_similarity