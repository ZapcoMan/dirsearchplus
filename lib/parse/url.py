from lib.utils.common import lstrip_once


def clean_path(path, keep_queries=False, keep_fragment=False):
    """
    清理路径字符串，移除查询参数和片段标识符

    Args:
        path (str): 需要清理的路径字符串
        keep_queries (bool): 是否保留查询参数（?后面的部分），默认为False
        keep_fragment (bool): 是否保留片段标识符（#后面的部分），默认为False

    Returns:
        str: 清理后的路径字符串
    """
    # 移除片段标识符（#后面的部分）
    if not keep_fragment:
        path = path.split("#")[0]
    # 移除查询参数（?后面的部分）
    if not keep_queries:
        path = path.split("?")[0]

    return path


def parse_path(value):
    """
    解析路径字符串，提取URL中的路径部分

    Args:
        value (str): 需要解析的路径或URL字符串

    Returns:
        str: 提取到的路径部分，如果解析失败则返回去除左侧斜杠的原字符串
    """
    try:
        # 尝试按照协议分隔符分割URL
        scheme, url = value.split("//", 1)
        # 验证协议格式是否正确
        if (
            scheme and (not scheme.endswith(":") or "/" in scheme)
            or url.startswith("/")
        ):
            raise ValueError

        # 返回URL中除去域名后的路径部分
        return "/".join(url.split("/")[1:])
    except Exception:
        # 如果解析失败，返回去除左侧斜杠的原字符串
        return lstrip_once(value, "/")

