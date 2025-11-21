from lib.core.exceptions import InvalidRawRequest
from lib.core.logger import logger
from lib.parse.headers import HeadersParser
from lib.utils.file import File


def parse_raw(raw_file):
    """
    解析原始HTTP请求文件，提取请求路径、方法、头部和主体信息

    Args:
        raw_file (str): 原始HTTP请求文件的路径

    Returns:
        tuple: 包含以下元素的元组:
            - list: 请求URL列表，格式为[host+path]
            - str: HTTP请求方法(如GET、POST等)
            - dict: 请求头部信息字典
            - str: 请求主体内容，如果没有则为None

    Raises:
        InvalidRawRequest: 当原始请求格式无效或缺少必要字段时抛出
    """
    # 读取原始请求文件内容
    with File(raw_file) as fd:
        raw_content = fd.read()

    # 尝试按不同换行符分割请求头和请求体
    try:
        head, body = raw_content.split("\n\n", 1)
    except ValueError:
        try:
            head, body = raw_content.split("\r\n\r\n", 1)
        except ValueError:
            head = raw_content.strip("\n")
            body = None

    # 解析请求行和头部信息
    try:
        method, path = head.splitlines()[0].split()[:2]
        headers = HeadersParser("\n".join(head.splitlines()[1:]))
        host = headers.get("host")
    except KeyError:
        raise InvalidRawRequest("在原始请求中找不到Host头")
    except Exception as e:
        logger.exception(e)
        raise InvalidRawRequest("原始请求在形成性上无效")

    return [host + path], method, dict(headers), body

