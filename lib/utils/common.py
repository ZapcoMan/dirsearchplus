from ipaddress import IPv4Network, IPv6Network
from urllib.parse import quote, urljoin

from lib.core.settings import (
    INVALID_CHARS_FOR_WINDOWS_FILENAME, INSECURE_CSV_CHARS,
    INVALID_FILENAME_CHAR_REPLACEMENT, URL_SAFE_CHARS, TEXT_CHARS,
)


def safequote(string_):
    """
    对字符串进行URL安全编码。

    参数:
        string_ (str): 需要编码的字符串。

    返回:
        str: 经过URL编码后的字符串。
    """
    return quote(string_, safe=URL_SAFE_CHARS)


def uniq(array, type_=list):
    """
    去除数组中的重复元素并保持顺序，同时过滤掉空值。

    参数:
        array (list): 输入的列表。
        type_ (type): 返回结果的数据类型，默认是 list。

    返回:
        type_: 去重后的新对象（默认为 list）。
    """
    return type_(filter(None, dict.fromkeys(array)))


def lstrip_once(string, pattern):
    """
    如果字符串以指定模式开头，则只去除一次该前缀。

    参数:
        string (str): 要处理的字符串。
        pattern (str): 要移除的前缀。

    返回:
        str: 处理后的字符串。
    """
    if string.startswith(pattern):
        return string[len(pattern):]

    return string


def rstrip_once(string, pattern):
    """
    如果字符串以指定模式结尾，则只去除一次该后缀。

    参数:
        string (str): 要处理的字符串。
        pattern (str): 要移除的后缀。

    返回:
        str: 处理后的字符串。
    """
    if string.endswith(pattern):
        return string[:-len(pattern)]

    return string


# Windows 在文件名中拒绝使用某些字符
def get_valid_filename(string):
    """
    将输入字符串转换为Windows系统中合法的文件名。

    参数:
        string (str): 原始文件名字符串。

    返回:
        str: 替换非法字符后的有效文件名。
    """
    for char in INVALID_CHARS_FOR_WINDOWS_FILENAME:
        string = string.replace(char, INVALID_FILENAME_CHAR_REPLACEMENT)

    return string


def human_size(num):
    """
    将字节数转换为人类可读的大小格式（如 KB、MB 等）。

    参数:
        num (int or float): 字节大小数值。

    返回:
        str: 可读性较好的大小表示。
    """
    base = 1024
    for unit in ["B ", "KB", "MB", "GB"]:
        if -base < num < base:
            return f"{num}{unit}"
        num = round(num / base)

    return f"{num}TB"


def is_binary(bytes):
    """
    判断给定的字节数据是否为二进制内容。

    参数:
        bytes (bytes): 待检测的字节串。

    返回:
        bool: 若含有非文本字符则返回 True，否则返回 False。
    """
    return bool(bytes.translate(None, TEXT_CHARS))


def is_ipv6(ip):
    """
    检查一个IP地址是否是IPv6地址。

    参数:
        ip (str): IP地址字符串。

    返回:
        bool: 如果是IPv6地址返回True，否则返回False。
    """
    return ip.count(":") >= 2


def iprange(subnet):
    """
    根据子网掩码生成对应的IP地址范围列表。

    参数:
        subnet (str): 子网描述符，例如 '192.168.1.0/24' 或 IPv6 地址段。

    返回:
        list: 包含所有IP地址的字符串列表。
    """
    network = IPv4Network(subnet)
    if is_ipv6(subnet):
        network = IPv6Network(subnet)

    return [str(ip) for ip in network]


# Prevent CSV injection. Reference: https://www.exploit-db.com/exploits/49370
def escape_csv(text):
    """
    对CSV字段内容进行转义以防止注入攻击。

    参数:
        text (str): 需要转义的原始文本。

    返回:
        str: 已经被适当转义的文本。
    """
    if text.startswith(INSECURE_CSV_CHARS):
        text = "'" + text

    return text.replace('"', '""')


# The browser direction behavior when you click on <a href="bar">link</a>
# (https://website.com/folder/foo -> https://website.com/folder/bar)
def merge_path(url, path):
    """
    合并基础URL与相对路径，模拟浏览器解析链接的行为。

    参数:
        url (str): 基础URL。
        path (str): 相对路径。

    返回:
        str: 解析合并后的完整URL路径。
    """
    parts = url.split("/")
    # Normalize path like the browser does (dealing with ../ and ./)
    path = urljoin("/", path).lstrip("/")
    parts[-1] = path

    return "/".join(parts)

