import sys

from lib.core.settings import (
    AUTHENTICATION_TYPES,
    COMMON_EXTENSIONS,
    DEFAULT_TOR_PROXIES,
    OUTPUT_FORMATS,
    SCRIPT_PATH,
)
from lib.parse.cmdline import parse_arguments
from lib.parse.config import ConfigParser
from lib.parse.headers import HeadersParser
from lib.utils.common import iprange, uniq
from lib.utils.file import File, FileUtils


def parse_options():
    """解析命令行选项并进行初始化配置

    此函数负责处理用户输入的各种命令行参数，并根据这些参数完成程序运行所需的各项初始化工作。
    包括 URL 列表来源判断、扩展名处理、代理设置、请求头构建等关键步骤。

    返回值:
        dict: 经过处理后的所有配置项组成的字典
    """
    open("bypass403_url.txt", 'w').close()
    opt = parse_config(parse_arguments())

    if opt.session_file:
        return vars(opt)

    opt.http_method = opt.http_method.upper()

    # 设置 URLs 来源：从文件读取、CIDR 地址段、标准输入或原始请求文件
    if opt.url_file:
        fd = _access_file(opt.url_file)
        opt.urls = fd.get_lines()
    elif opt.cidr:
        opt.urls = iprange(opt.cidr)
    elif opt.stdin_urls:
        opt.urls = sys.stdin.read().splitlines(0)
    elif opt.raw_file:
        _access_file(opt.raw_file)
    elif not opt.urls:
        print("缺少URL目标，请尝试使用 -u <url>")
        #opt.urls="http://www.baidu.com"
        exit(1)
    bypass403_url="".join(opt.urls)
    with open('bypass403_url.txt','w') as f:
        f.write(bypass403_url)


    if not opt.raw_file:
        opt.urls = uniq(opt.urls)

    # 检查是否指定了扩展名
    if not opt.extensions and not opt.remove_extensions:
        print("警告：未指定扩展名！")

    # 必须提供至少一个字典文件
    if not opt.wordlists:
        print("未提供字典文件，请尝试使用 -w <字典文件>")
        exit(1)

    opt.wordlists = tuple(wordlist.strip() for wordlist in opt.wordlists.split(","))

    # 检查每个字典文件是否存在且可读
    for dict_file in opt.wordlists:
        _access_file(dict_file)

    # 线程数量必须大于零
    if opt.thread_count < 1:
        print("线程数必须大于零")
        exit(1)

    # 设置代理服务器
    if opt.tor:
        opt.proxies = list(DEFAULT_TOR_PROXIES)
    elif opt.proxy_file:
        fd = _access_file(opt.proxy_file)
        opt.proxies = fd.get_lines()

    # 数据文件处理
    if opt.data_file:
        fd = _access_file(opt.data_file)
        opt.data = fd.get_lines()

    # SSL/TLS 认证相关文件检查
    if opt.cert_file:
        _access_file(opt.cert_file)

    if opt.key_file:
        _access_file(opt.key_file)

    headers = {}

    # 请求头文件处理
    if opt.header_file:
        try:
            fd = _access_file(opt.header_file)
            headers.update(dict(HeadersParser(fd.read())))
        except Exception as e:
            print("请求头文件错误: " + str(e))
            exit(1)

    # 命令行传入的请求头处理
    if opt.headers:
        try:
            headers.update(dict(HeadersParser("\n".join(opt.headers))))
        except Exception:
            print("无效的请求头")
            exit(1)

    opt.headers = headers

    # 解析各种状态码过滤条件
    opt.include_status_codes = _parse_status_codes(opt.include_status_codes)
    opt.exclude_status_codes = _parse_status_codes(opt.exclude_status_codes)
    opt.recursion_status_codes = _parse_status_codes(opt.recursion_status_codes)
    opt.skip_on_status = _parse_status_codes(opt.skip_on_status)

    # 处理前缀与后缀
    opt.prefixes = uniq([prefix.strip() for prefix in opt.prefixes.split(",") if prefix], tuple)
    opt.suffixes = uniq([suffix.strip() for suffix in opt.suffixes.split(",") if suffix], tuple)

    # 子目录路径处理
    opt.subdirs = [
        subdir.lstrip(" /") + ("" if not subdir or subdir.endswith("/") else "/")
        for subdir in opt.subdirs.split(",")
    ]
    opt.exclude_subdirs = [
        subdir.lstrip(" /") + ("" if not subdir or subdir.endswith("/") else "/")
        for subdir in opt.exclude_subdirs.split(",")
    ]

    # 排除大小处理
    opt.exclude_sizes = {size.strip().upper() for size in opt.exclude_sizes.split(",")}

    # 扩展名处理逻辑
    if opt.remove_extensions:
        opt.extensions = ("",)
    elif opt.extensions == "*":
        opt.extensions = COMMON_EXTENSIONS
    elif opt.extensions == "CHANGELOG.md":
        print("提供了奇怪的扩展名: 'CHANGELOG.md'。请不要使用 * 作为扩展名或将其用双引号括起来")
        exit(0)
    else:
        opt.extensions = uniq(
            [extension.lstrip(" .") for extension in opt.extensions.split(",")],
            tuple,
        )

    # 排除扩展名处理
    opt.exclude_extensions = uniq(
        [
            exclude_extension.lstrip(" .")
            for exclude_extension in opt.exclude_extensions.split(",")
        ], tuple
    )

    # 认证类型验证
    if opt.auth and not opt.auth_type:
        print("请选择认证类型 --auth-type")
        exit(1)
    elif opt.auth_type and not opt.auth:
        print("未找到认证凭据")
        exit(1)
    elif opt.auth and opt.auth_type not in AUTHENTICATION_TYPES:
        print(f"'{opt.auth_type}' 不在可用的认证类型中: {', '.join(AUTHENTICATION_TYPES)}")
        exit(1)

    # 扩展名冲突检测
    if set(opt.extensions).intersection(opt.exclude_extensions):
        print("排除扩展名列表不能包含已在扩展名列表中的任何扩展名")
        exit(1)

    # 输出格式校验
    if opt.output_format not in OUTPUT_FORMATS:
        print("请选择以下输出格式之一: "
              f"{', '.join(OUTPUT_FORMATS)}")
        exit(1)

    return vars(opt)


def _parse_status_codes(str_):
    """
    将字符串形式的状态码转换为整型集合

    参数:
        str_ (str): 状态码字符串，支持单个数字或范围如 "200,400-404"

    返回值:
        set[int]: 解析后的状态码集合
    """
    if not str_:
        return set()

    status_codes = set()

    for status_code in str_.split(","):
        try:
            if "-" in status_code:
                start, end = status_code.strip().split("-")
                status_codes.update(range(int(start), int(end) + 1))
            else:
                status_codes.add(int(status_code.strip()))
        except ValueError:
            print(f"无效的状态码或状态码范围: {status_code}")
            exit(1)

    return status_codes


def _access_file(path):
    """
    检查指定路径的文件是否存在、是普通文件并且可以被读取

    参数:
        path (str): 文件路径

    返回值:
        File: 可操作的 File 对象实例
    """
    with File(path) as fd:
        if not fd.exists():
            print(f"{path} 不存在")
            exit(1)

        if not fd.is_valid():
            print(f"{path} 不是一个文件")
            exit(1)

        if not fd.can_read():
            print(f"{path} 无法读取")
            exit(1)

        return fd


def parse_config(opt):
    """
    使用配置文件中的默认值填充未在命令行中提供的选项

    参数:
        opt (argparse.Namespace): 已经通过命令行解析得到的对象

    返回值:
        argparse.Namespace: 合并了配置文件和命令行参数的结果对象
    """
    config = ConfigParser()
    config.read(opt.config)

    # 通用设置
    opt.thread_count = opt.thread_count or config.safe_getint(
        "general", "threads", 25
    )
    opt.include_status_codes = opt.include_status_codes or config.safe_get(
        "general", "include-status"
    )
    opt.exclude_status_codes = opt.exclude_status_codes or config.safe_get(
        "general", "exclude-status"
    )
    opt.exclude_sizes = opt.exclude_sizes or config.safe_get("general", "exclude-sizes", "")
    opt.exclude_texts = opt.exclude_texts or list(config.safe_get("general", "exclude-text", []))
    opt.exclude_regex = opt.exclude_regex or config.safe_get("general", "exclude-regex")
    opt.exclude_redirect = opt.exclude_redirect or config.safe_get(
        "general", "exclude-redirect"
    )
    opt.exclude_response = opt.exclude_response or config.safe_get(
        "general", "exclude-response"
    )
    opt.recursive = opt.recursive or config.safe_getboolean("general", "recursive")
    opt.deep_recursive = opt.deep_recursive or config.safe_getboolean(
        "general", "deep-recursive"
    )
    opt.force_recursive = opt.force_recursive or config.safe_getboolean(
        "general", "force-recursive"
    )
    opt.recursion_depth = opt.recursion_depth or config.safe_getint(
        "general", "max-recursion-depth"
    )
    opt.recursion_status_codes = opt.recursion_status_codes or config.safe_get(
        "general", "recursion-status", "100-999"
    )
    opt.subdirs = opt.subdirs or config.safe_get("general", "subdirs", "")
    opt.exclude_subdirs = opt.exclude_subdirs or config.safe_get(
        "general", "exclude-subdirs", ""
    )
    opt.skip_on_status = opt.skip_on_status or config.safe_get(
        "general", "skip-on-status", ""
    )
    opt.max_time = opt.max_time or config.safe_getint("general", "max-time")
    opt.exit_on_error = opt.exit_on_error or config.safe_getboolean(
        "general", "exit-on-error"
    )

    # 字典设置
    opt.wordlists = opt.wordlists or config.safe_get(
        "dictionary",
        "wordlists",
        FileUtils.build_path(SCRIPT_PATH, "db", "dicc.txt"),
    )
    opt.extensions = opt.extensions or config.safe_get(
        "dictionary", "default-extensions", ""
    )
    opt.force_extensions = opt.force_extensions or config.safe_getboolean(
        "dictionary", "force-extensions"
    )
    opt.overwrite_extensions = opt.overwrite_extensions or config.safe_getboolean(
        "dictionary", "overwrite-extensions"
    )
    opt.exclude_extensions = opt.exclude_extensions or config.safe_get(
        "dictionary", "exclude-extensions", ""
    )
    opt.prefixes = opt.prefixes or config.safe_get("dictionary", "prefixes", "")
    opt.suffixes = opt.suffixes or config.safe_get("dictionary", "suffixes", "")
    opt.lowercase = opt.lowercase or config.safe_getboolean("dictionary", "lowercase")
    opt.uppercase = opt.uppercase or config.safe_getboolean("dictionary", "uppercase")
    opt.capitalization = opt.capitalization or config.safe_getboolean(
        "dictionary", "capitalization"
    )

    # 请求设置
    opt.http_method = opt.http_method or config.safe_get("request", "http-method", "get")
    opt.header_file = opt.header_file or config.safe_get("request", "headers-file")
    opt.follow_redirects = opt.follow_redirects or config.safe_getboolean(
        "request", "follow-redirects"
    )
    opt.random_agents = opt.random_agents or config.safe_getboolean(
        "request", "random-user-agents"
    )
    opt.user_agent = opt.user_agent or config.safe_get("request", "user-agent")
    opt.cookie = opt.cookie or config.safe_get("request", "cookie")

    # 连接设置
    opt.delay = opt.delay or config.safe_getfloat("connection", "delay")
    opt.timeout = opt.timeout or config.safe_getfloat("connection", "timeout", 15)  # 从7.5秒增加到15秒以更好地兼容SOCKS4a
    opt.max_retries = opt.max_retries or config.safe_getint("connection", "max-retries", 1)
    opt.max_rate = opt.max_rate or config.safe_getint("connection", "max-rate")
    opt.proxies = opt.proxies or list(config.safe_get("connection", "proxy", []))
    opt.proxy_file = opt.proxy_file or config.safe_get("connection", "proxy-file")
    opt.scheme = opt.scheme or config.safe_get(
        "connection", "scheme", None, ["http", "https"]
    )
    opt.replay_proxy = opt.replay_proxy or config.safe_get("connection", "replay-proxy")

    # 高级设置
    opt.crawl = opt.crawl or config.safe_getboolean("advanced", "crawl")

    # 显示设置
    opt.full_url = opt.full_url or config.safe_getboolean("view", "full-url")
    opt.color = opt.color or config.safe_getboolean("view", "color", True)
    opt.quiet = opt.quiet or config.safe_getboolean("view", "quiet-mode")
    opt.redirects_history = opt.redirects_history or config.safe_getboolean(
        "view", "show-redirects-history"
    )

    # 输出设置
    opt.output_path = config.safe_get("output", "autosave-report-folder")
    opt.autosave_report = config.safe_getboolean("output", "autosave-report")
    opt.log_file_size = config.safe_getint("output", "log-file-size")
    opt.log_file = opt.log_file or config.safe_get("output", "log-file")
    opt.output_format = opt.output_format or config.safe_get(
        "output", "report-format", "plain", OUTPUT_FORMATS
    )

    return opt

