from optparse import OptionParser, OptionGroup

from lib.core.settings import VERSION, SCRIPT_PATH, AUTHENTICATION_TYPES
from lib.utils.file import FileUtils


def parse_arguments():
    """
    解析命令行参数并返回解析后的选项对象。

    此函数使用 OptionParser 构建完整的命令行接口，包括：
    - 必需参数（如 URL、文件路径等）
    - 字典设置（扩展名、大小写处理等）
    - 常规设置（线程数、递归深度等）
    - 请求设置（HTTP 方法、头部、认证信息等）
    - 连接设置（代理、超时、延迟等）
    - 高级功能（爬虫、绕过机制等）
    - 显示与输出控制（颜色、格式化、日志等）

    返回:
        options (Values): 包含所有解析后命令行参数的对象。
    """

    # 定义程序的基本用法说明
    usage = "用法: %prog [-u|--url] 目标 [-e|--extensions] 扩展名 [选项]"
    parser = OptionParser(usage, version=f"dirsearch v{VERSION}")

    # === 必需参数组 ===
    mandatory = OptionGroup(parser, "必需参数")
    mandatory.add_option(
        "-u",
        "--url",
        action="append",
        dest="urls",
        metavar="URL",
        help="目标URL，可以使用多个标志",
    )
    mandatory.add_option(
        "-b",
        "--bypass",
        action="append",
        dest="bypass",
        metavar="",
        help="绕过403检测(是/否)",
    )
    mandatory.add_option(
        "-j",
        "--jsfind",
        action="append",
        dest="jsfind",
        metavar="",
        help="JS查找(是/否)",
    )
    mandatory.add_option(
        "-z",
        "--zwsb",
        action="append",
        dest="zwsb",
        metavar="",
        help="指纹识别(是/否)",
    )
    mandatory.add_option(
        "-p",
        "--packer-fuzzer",
        action="append",
        dest="packer_fuzzer",
        metavar="",
        help="包混淆扫描(是/否)",
    )
    # 在必需参数组中添加新的选项
    mandatory.add_option(
        "-a",
        "--all",
        action="store_true",
        dest="all_modules",
        help="启动所有功能模块(bypass, jsfind, zwsb, packer-fuzzer, swagger)",
    )

    mandatory.add_option(
        "--swagger",
        action="append",
        dest="swagger",
        metavar="",
        help="Swagger扫描(是/否)",
    )
    mandatory.add_option(
        "-l",
        "--url-file",
        action="store",
        dest="url_file",
        metavar="路径",
        help="URL列表文件",
    )
    mandatory.add_option(
        "--stdin",
        action="store_true",
        dest="stdin_urls",
        help="从标准输入读取URL"
    )
    mandatory.add_option(
        "--cidr",
        action="store",
        dest="cidr",
        help="目标CIDR"
    )
    mandatory.add_option(
        "--raw",
        action="store",
        dest="raw_file",
        metavar="路径",
        help="从文件加载原始HTTP请求(使用 `--scheme` 标志设置协议)",
    )
    mandatory.add_option(
        "-s",
        "--session",
        action="store",
        dest="session_file",
        help="会话文件"
    )
    mandatory.add_option(
        "--config",
        action="store",
        dest="config",
        metavar="路径",
        help="配置文件的完整路径，参考 'config.ini' 示例(默认: config.ini)",
        default=FileUtils.build_path(SCRIPT_PATH, "config.ini"),
    )

    # === 字典设置组 ===
    dictionary = OptionGroup(parser, "字典设置")
    dictionary.add_option(
        "-w",
        "--wordlists",
        action="store",
        dest="wordlists",
        help="自定义单词列表(用逗号分隔)",
    )
    dictionary.add_option(
        "-e",
        "--extensions",
        action="store",
        dest="extensions",
        help="扩展名列表，用逗号分隔(例如 php,asp)",
    )
    dictionary.add_option(
        "-f",
        "--force-extensions",
        action="store_true",
        dest="force_extensions",
        help="在每个单词列表条目末尾添加扩展名。默认情况下dirsearch只替换%EXT%关键字为扩展名",
    )
    dictionary.add_option(
        "-O",
        "--overwrite-extensions",
        action="store_true",
        dest="overwrite_extensions",
        help="用您的扩展名覆盖单词列表中的其他扩展名(通过 `-e` 选择)",
    )
    dictionary.add_option(
        "--exclude-extensions",
        action="store",
        dest="exclude_extensions",
        metavar="扩展名",
        help="排除的扩展名列表，用逗号分隔(例如 asp,jsp)",
    )
    dictionary.add_option(
        "--remove-extensions",
        action="store_true",
        dest="remove_extensions",
        help="移除所有路径中的扩展名(例如 admin.php -> admin)",
    )
    dictionary.add_option(
        "--prefixes",
        action="store",
        dest="prefixes",
        help="为所有单词列表条目添加自定义前缀(用逗号分隔)",
    )
    dictionary.add_option(
        "--suffixes",
        action="store",
        dest="suffixes",
        help="为所有单词列表条目添加自定义后缀，忽略目录(用逗号分隔)",
    )
    dictionary.add_option(
        "-U",
        "--uppercase",
        action="store_true",
        dest="uppercase",
        help="大写单词列表",
    )
    dictionary.add_option(
        "-L",
        "--lowercase",
        action="store_true",
        dest="lowercase",
        help="小写单词列表",
    )
    dictionary.add_option(
        "-C",
        "--capital",
        action="store_true",
        dest="capitalization",
        help="首字母大写单词列表",
    )

    # === 常规设置组 ===
    general = OptionGroup(parser, "常规设置")
    general.add_option(
        "-t",
        "--threads",
        action="store",
        type="int",
        dest="thread_count",
        metavar="线程数",
        help="线程数量",
    )
    general.add_option(
        "-r",
        "--recursive",
        action="store_true",
        dest="recursive",
        help="递归暴力破解",
    )
    general.add_option(
        "--deep-recursive",
        action="store_true",
        dest="deep_recursive",
        help="对每个目录深度执行递归扫描(例如 api/users -> api/)",
    )
    general.add_option(
        "--force-recursive",
        action="store_true",
        dest="force_recursive",
        help="对每个找到的路径都进行递归暴力破解，不仅限于目录",
    )
    general.add_option(
        "-R",
        "--max-recursion-depth",
        action="store",
        type="int",
        dest="recursion_depth",
        metavar="深度",
        help="最大递归深度",
    )
    general.add_option(
        "--recursion-status",
        action="store",
        dest="recursion_status_codes",
        metavar="状态码",
        help="执行递归扫描的有效状态码，支持范围(用逗号分隔)",
    )
    general.add_option(
        "--subdirs",
        action="store",
        dest="subdirs",
        metavar="子目录",
        help="扫描给定URL的子目录(用逗号分隔)",
    )
    general.add_option(
        "--exclude-subdirs",
        action="store",
        dest="exclude_subdirs",
        metavar="子目录",
        help="递归扫描期间排除以下子目录(用逗号分隔)",
    )
    general.add_option(
        "-i",
        "--include-status",
        action="store",
        dest="include_status_codes",
        metavar="状态码",
        help="包含的状态码，用逗号分隔，支持范围(例如 200,300-399)",
    )
    general.add_option(
        "-x",
        "--exclude-status",
        action="store",
        dest="exclude_status_codes",
        metavar="状态码",
        help="排除的状态码，用逗号分隔，支持范围(例如 301,500-599)",
    )
    general.add_option(
        "--exclude-sizes",
        action="store",
        dest="exclude_sizes",
        metavar="大小",
        help="按大小排除响应，用逗号分隔(例如 0B,4KB)",
    )
    general.add_option(
        "--exclude-text",
        action="append",
        dest="exclude_texts",
        metavar="文本",
        help="按文本排除响应，可以使用多个标志",
    )
    general.add_option(
        "--exclude-regex",
        action="store",
        dest="exclude_regex",
        metavar="正则表达式",
        help="按正则表达式排除响应",
    )
    general.add_option(
        "--exclude-redirect",
        action="store",
        dest="exclude_redirect",
        metavar="字符串",
        help="如果此正则表达式(或文本)匹配重定向URL，则排除响应(例如 '/index.html')",
    )
    general.add_option(
        "--exclude-response",
        action="store",
        dest="exclude_response",
        metavar="路径",
        help="排除与此页面响应相似的响应，路径作为输入(例如 404.html)",
    )
    general.add_option(
        "--skip-on-status",
        action="store",
        dest="skip_on_status",
        metavar="状态码",
        help="当遇到这些状态码之一时跳过目标，用逗号分隔，支持范围",
    )
    general.add_option(
        "--min-response-size",
        action="store",
        type="int",
        dest="minimum_response_size",
        help="最小响应长度",
        metavar="长度",
        default=0,
    )
    general.add_option(
        "--max-response-size",
        action="store",
        type="int",
        dest="maximum_response_size",
        help="最大响应长度",
        metavar="长度",
        default=0,
    )
    general.add_option(
        "--max-time",
        action="store",
        type="int",
        dest="max_time",
        metavar="秒数",
        help="扫描的最大运行时间",
    )
    general.add_option(
        "--exit-on-error",
        action="store_true",
        dest="exit_on_error",
        help="发生错误时退出",
    )

    # === 请求设置组 ===
    request = OptionGroup(parser, "请求设置")
    request.add_option(
        "-m",
        "--http-method",
        action="store",
        dest="http_method",
        metavar="方法",
        help="HTTP方法(默认: GET)",
    )
    request.add_option(
        "-d",
        "--data",
        action="store",
        dest="data",
        help="HTTP请求数据"
    )
    request.add_option(
        "--data-file",
        action="store",
        dest="data_file",
        metavar="路径",
        help="包含HTTP请求数据的文件"
    )
    request.add_option(
        "-H",
        "--header",
        action="append",
        dest="headers",
        help="HTTP请求头，可以使用多个标志",
    )
    request.add_option(
        "--header-file",
        dest="header_file",
        metavar="路径",
        help="包含HTTP请求头的文件",
    )
    request.add_option(
        "-F",
        "--follow-redirects",
        action="store_true",
        dest="follow_redirects",
        help="跟随HTTP重定向",
    )
    request.add_option(
        "--random-agent",
        action="store_true",
        dest="random_agents",
        help="为每个请求选择随机User-Agent",
    )
    request.add_option(
        "--auth",
        action="store",
        dest="auth",
        metavar="凭证",
        help="身份验证凭据(例如 user:password 或 bearer token)",
    )
    request.add_option(
        "--auth-type",
        action="store",
        dest="auth_type",
        metavar="类型",
        help=f"身份验证类型 ({', '.join(AUTHENTICATION_TYPES)})",
    )
    request.add_option(
        "--cert-file",
        action="store",
        dest="cert_file",
        metavar="路径",
        help="包含客户端证书的文件",
    )
    request.add_option(
        "--key-file",
        action="store",
        dest="key_file",
        metavar="路径",
        help="包含客户端证书私钥的文件(未加密)",
    )
    request.add_option(
        "--user-agent",
        action="store",
        dest="user_agent"
    )
    request.add_option(
        "--cookie",
        action="store",
        dest="cookie"
    )

    # === 连接设置组 ===
    connection = OptionGroup(parser, "连接设置")
    connection.add_option(
        "--timeout",
        action="store",
        type="float",
        dest="timeout",
        help="连接超时",
    )
    connection.add_option(
        "--delay",
        action="store",
        type="float",
        dest="delay",
        help="请求之间的延迟",
    )
    connection.add_option(
        "--proxy",
        action="append",
        dest="proxies",
        metavar="代理",
        help="代理URL(HTTP/SOCKS)，可以使用多个标志",
    )
    connection.add_option(
        "--proxy-file",
        action="store",
        dest="proxy_file",
        metavar="路径",
        help="包含代理服务器的文件",
    )
    connection.add_option(
        "--proxy-auth",
        action="store",
        dest="proxy_auth",
        metavar="凭证",
        help="代理身份验证凭据",
    )
    connection.add_option(
        "--replay-proxy",
        action="store",
        dest="replay_proxy",
        metavar="代理",
        help="用于重现找到路径的代理",
    )
    connection.add_option(
        "--tor",
        action="store_true",
        dest="tor",
        help="使用Tor网络作为代理"
    )
    connection.add_option(
        "--scheme",
        action="store",
        dest="scheme",
        metavar="协议",
        help="原始请求的协议或者URL中没有协议时使用的协议(默认: 自动检测)",
    )
    connection.add_option(
        "--max-rate",
        action="store",
        type="int",
        dest="max_rate",
        metavar="速率",
        help="每秒最大请求数",
    )
    connection.add_option(
        "--retries",
        action="store",
        type="int",
        dest="max_retries",
        metavar="重试次数",
        help="失败请求的重试次数",
    )
    connection.add_option(
        "--ip",
        action="store",
        dest="ip",
        help="服务器IP地址"
    )

    # === 高级设置组 ===
    advanced = OptionGroup(parser, "高级设置")
    advanced.add_option(
        "--crawl",
        action="store_true",
        dest="crawl",
        help="在响应中爬取新路径"
    )

    # === 显示设置组 ===
    view = OptionGroup(parser, "显示设置")
    view.add_option(
        "--full-url",
        action="store_true",
        dest="full_url",
        help="输出中显示完整URL(安静模式下自动启用)",
    )
    view.add_option(
        "--redirects-history",
        action="store_true",
        dest="redirects_history",
        help="显示重定向历史",
    )
    view.add_option(
        "--no-color",
        action="store_false",
        dest="color",
        help="无彩色输出"
    )
    view.add_option(
        "-q",
        "--quiet-mode",
        action="store_true",
        dest="quiet",
        help="安静模式"
    )

    # === 输出设置组 ===
    output = OptionGroup(parser, "输出设置")
    output.add_option(
        "-o",
        "--output",
        action="store",
        dest="output_file",
        metavar="路径",
        help="输出文件",
    )
    output.add_option(
        "--format",
        action="store",
        dest="output_format",
        metavar="格式",
        help="报告格式(可用: simple, plain, json, xml, md, csv, html, sqlite)",
    )
    output.add_option(
        "--log",
        action="store",
        dest="log_file",
        metavar="路径",
        help="日志文件"
    )

    # 将各个选项组加入主解析器
    parser.add_option_group(mandatory)
    parser.add_option_group(dictionary)
    parser.add_option_group(general)
    parser.add_option_group(request)
    parser.add_option_group(connection)
    parser.add_option_group(advanced)
    parser.add_option_group(view)
    parser.add_option_group(output)

    # 解析命令行参数
    options, _ = parser.parse_args()

    return options
