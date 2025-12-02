import os
import sys
import string

from lib.utils.file import FileUtils

# 版本号格式：<主版本>.<次版本>.<修订版>[.<月份>]
VERSION = "1.5.11 "
author = "ZapcoMan"
# 启动时显示的横幅信息（ASCII艺术字）
# BANNER = f"""
#    _      __    __                     __            ___     ____                 __   ___  __
#  | | /| / /__ / /______  __ _  ___   / /____    ___/ (_)___/ __/__ ___ _________/ /  / _ \/ /_ _____  v{VERSION}
#  | |/ |/ / -_) / __/ _ \/  ' \/ -_) / __/ _ \  / _  / / __/\ \/ -_) _ `/ __/ __/ _ \/ ___/ / // (_-<
#  |__/|__/\__/_/\__/\___/_/_/_/\__/  \__/\___/  \_,_/_/_/ /___/\__/\_,_/_/  \__/_//_/_/  /_/\_,_/___/
#
#
# """
BANNER = f"""
 __        __   _ _  ____                        _____        ____  _                              _    __  __
 \ \      / /__| | |/ ___|___  _ __ ___   ___   |_   _|__    |  _ \(_)_ __ ___  ___  __ _ _ __ ___| |__ \ \/ /  v{VERSION} by {author}
  \ \ /\ / / _ \ | | |   / _ \| '_ ` _ \ / _ \    | |/ _ \   | | | | | '__/ __|/ _ \/ _` | '__/ __| '_ \ \  /
   \ V  V /  __/ | | |__| (_) | | | | | |  __/    | | (_) |  | |_| | | |  \__ \  __/ (_| | | | (__| | | |/  \/|
    \_/\_/ \___|_|_|\____\___/|_| |_| |_|\___|    |_|\___/   |____/|_|_|  |___/\___|\__,_|_|  \___|_| |_/_/\_/

"""



# 获取当前脚本所在目录的上三级父目录路径
SCRIPT_PATH = FileUtils.parent(__file__, 3)

# 默认配置文件名
OPTIONS_FILE = "options.ini"

# 判断是否运行在 Windows 平台
IS_WINDOWS = sys.platform in ("win32", "msys")

# 默认编码方式
DEFAULT_ENCODING = "utf-8"

# 操作系统换行符
NEW_LINE = os.linesep

# Windows 文件名中不允许出现的字符集合
INVALID_CHARS_FOR_WINDOWS_FILENAME = ('"', "*", "<", ">", "?", "\\", "|", "/", ":")

# 非法文件名字符替换符号
INVALID_FILENAME_CHAR_REPLACEMENT = "_"

# 支持的输出格式列表
OUTPUT_FORMATS = ("simple", "plain", "json", "xml", "md", "csv", "html", "sqlite")

# 常见网页扩展名
COMMON_EXTENSIONS = ("php", "jsp", "asp", "aspx", "do", "action", "cgi", "html", "htm", "js", "tar.gz")

# 多媒体资源扩展名
MEDIA_EXTENSIONS = ("webm", "mkv", "avi", "ts", "mov", "qt", "amv", "mp4", "m4p", "m4v", "mp3", "swf", "mpg", "mpeg", "jpg", "jpeg", "pjpeg", "png", "woff", "svg", "webp", "bmp", "pdf", "wav", "vtt")

# 不应被覆盖写入的文件扩展名集合（包括多媒体和其他重要类型）
EXCLUDE_OVERWRITE_EXTENSIONS = MEDIA_EXTENSIONS + ("axd", "cache", "coffee", "conf", "config", "css", "dll", "lock", "log", "key", "pub", "properties", "ini", "jar", "js", "json", "toml", "txt", "xml", "yaml", "yml")

# 在HTML解析过程中需要爬取链接属性的标签属性列表
CRAWL_ATTRIBUTES = ("action", "cite", "data", "formaction", "href", "longdesc", "poster", "src", "srcset", "xmlns")

# 在HTML解析过程中需要处理的标签名称列表
CRAWL_TAGS = ("a", "area", "base", "blockquote", "button", "embed", "form", "frame", "frameset", "html", "iframe", "input", "ins", "noframes", "object", "q", "script", "source")

# 支持的身份验证类型
AUTHENTICATION_TYPES = ("basic", "digest", "bearer", "ntlm", "jwt", "oauth2")

# 支持的代理协议前缀
PROXY_SCHEMES = ("http://", "https://", "socks5://", "socks5h://", "socks4://", "socks4a://")

# HTTP 和 HTTPS 的标准端口号映射表
STANDARD_PORTS = {"http": 80, "https": 443}

# 可能导致CSV注入攻击的危险字符
INSECURE_CSV_CHARS = ("+", "-", "=", "@")

# 默认测试路径前缀
DEFAULT_TEST_PREFIXES = (".",)

# 默认测试路径后缀
DEFAULT_TEST_SUFFIXES = ("/",)

# Tor网络默认使用的 SOCKS5 代理地址
DEFAULT_TOR_PROXIES = ("socks5://127.0.0.1:9050", "socks5://127.0.0.1:9150")

# 默认HTTP请求头设置
DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "accept": "*/*",
    "accept-rncoding": "*",
    "keep-alive": "timeout=15, max=1000",
    "cache-control": "max-age=0",
}

# 默认会话保存文件名
DEFAULT_SESSION_FILE = "session.pickle"

# 路径反射标记，在某些测试场景下用于标识反射点位置
REFLECTED_PATH_MARKER = "__REFLECTED_PATH__"

# 通配符测试点标记，表示可变部分的位置
WILDCARD_TEST_POINT_MARKER = "__WILDCARD_POINT__"

# 扩展名占位符标记，用于动态替换实际扩展名
EXTENSION_TAG = "%ext%"

# 匹配常见文件扩展名的正则表达式模式
EXTENSION_RECOGNITION_REGEX = r"\w+([.][a-zA-Z0-9]{2,5}){1,3}~?$"

# 查询字符串格式校验的正则表达式
QUERY_STRING_REGEX = r"^(\&?([^=& ]+)\=([^=& ]+)?){1,200}$"

# 请求响应读取错误匹配的异常类名正则表达式
READ_RESPONSE_ERROR_REGEX = r"(ChunkedEncodingError|StreamConsumedError|UnrewindableBodyError)"

# URI 格式校验的正则表达式（检查是否有合法的协议开头）
URI_REGEX = r"^[a-z]{2,}:"

# robots.txt 中 Allow/Disallow 规则提取的正则表达式
ROBOTS_TXT_REGEX = r"(?:Allow|Disallow): /(.*)"

# 表示未知状态或值的通用字符串常量
UNKNOWN = "unknown"

# Linux 下临时目录路径
TMP_PATH = "/tmp/dirsearch"

# 示例域名，用于模拟测试等用途
DUMMY_DOMAIN = "example.com"

# 示例完整 URL 地址
DUMMY_URL = "https://example.com/"

# 示例单词，用作测试数据填充
DUMMY_WORD = "dummyasdf"

# Socket 连接超时时间（秒）
SOCKET_TIMEOUT = 6

# 更新速率统计的时间间隔（秒）
RATE_UPDATE_DELAY = 0.15

# 最大相似度阈值，超过该比例视为重复内容
MAX_MATCH_RATIO = 0.98

# 数据流分块大小（单位：字节），用于高效传输大文件
ITER_CHUNK_SIZE = 1024 * 1024

# 允许的最大响应体大小限制（单位：字节）
MAX_RESPONSE_SIZE = 80 * 1024 * 1024

# 测试路径长度基准值
TEST_PATH_LENGTH = 6

# 连续请求失败最大次数上限
MAX_CONSECUTIVE_REQUEST_ERRORS = 75

# 等待暂停操作完成的最长等待时间（秒）
PAUSING_WAIT_TIMEOUT = 7

# URL安全字符集定义（来自string模块中的标点符号）
URL_SAFE_CHARS = string.punctuation

# 文本字符范围定义（用于判断二进制内容是否为文本）
TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})

