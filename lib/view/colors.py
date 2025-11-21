import string

from colorama import init, Fore, Back, Style
from pyparsing import Literal, Word, Combine, Optional, Suppress, delimitedList, oneOf


# 颜色映射字典，将颜色名称映射到对应的背景颜色代码
BACK_COLORS = {
    "red": Back.RED,
    "green": Back.GREEN,
    "yellow": Back.YELLOW,
    "blue": Back.BLUE,
    "magenta": Back.MAGENTA,
    "cyan": Back.CYAN,
    "white": Back.WHITE,
    "none": "",
}

# 颜色映射字典，将颜色名称映射到对应的前景颜色代码
FORE_COLORS = {
    "red": Fore.RED,
    "green": Fore.GREEN,
    "yellow": Fore.YELLOW,
    "blue": Fore.BLUE,
    "magenta": Fore.MAGENTA,
    "cyan": Fore.CYAN,
    "white": Fore.WHITE,
    "none": "",
}

# 样式映射字典，将样式名称映射到对应的样式代码
STYLES = {
    "bright": Style.BRIGHT,
    "dim": Style.DIM,
    "normal": ""
}

# 定义ANSI转义序列的解析规则，用于匹配和移除颜色代码
# Credit: https://stackoverflow.com/a/2187024/12238982
_escape_seq = Combine(
    Literal("\x1b")
    + "["
    + Optional(delimitedList(Word(string.digits), ";"))
    + oneOf(list(string.ascii_letters))
)

# 初始化colorama库，使其在Windows系统上也能正常工作
init()


def disable_color():
    """
    禁用所有颜色和样式设置，将所有颜色和样式映射重置为无效果的值。
    调用此函数后，后续的颜色设置将不会产生视觉效果。
    """
    # 将所有样式设置为正常样式
    for style in STYLES:
        STYLES[style] = STYLES["normal"]

    # 将前景色和背景色都设置为无颜色效果
    for table in (FORE_COLORS, BACK_COLORS):
        for color in ("red", "green", "yellow", "blue", "magenta", "cyan", "white"):
            table[color] = table["none"]


def set_color(msg, fore="none", back="none", style="normal"):
    """
    为文本消息应用指定的颜色和样式设置。

    参数:
        msg (str): 要着色的文本消息
        fore (str): 前景色名称，默认为"none"（不改变前景色）
        back (str): 背景色名称，默认为"none"（不改变背景色）
        style (str): 文本样式名称，默认为"normal"（正常样式）

    返回:
        str: 应用了颜色和样式的文本消息
    """
    msg = STYLES[style] + FORE_COLORS[fore] + BACK_COLORS[back] + msg
    return msg + Style.RESET_ALL


def clean_color(msg):
    """
    移除文本消息中的所有ANSI颜色和样式转义序列。

    参数:
        msg (str): 包含颜色代码的文本消息

    返回:
        str: 移除了所有颜色和样式代码的纯文本消息
    """
    return Suppress(_escape_seq).transformString(msg)

