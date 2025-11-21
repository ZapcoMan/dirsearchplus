import random
import string


def rand_string(n, omit=None):
    """
    生成指定长度的随机字符串

    参数:
        n (int): 要生成的随机字符串的长度
        omit (str, optional): 需要从字符集中排除的字符集合，默认为None表示不排除任何字符

    返回:
        str: 生成的随机字符串
    """
    # 定义字符集，包含大小写字母和数字
    seq = string.ascii_lowercase + string.ascii_uppercase + string.digits

    # 如果指定了要排除的字符，则从字符集中移除这些字符
    if omit:
        seq = list(set(seq) - set(omit))

    # 从字符集中随机选择n个字符并拼接成字符串
    return "".join(random.choice(seq) for _ in range(n))

