# 全局变量 blacklists 用于存储黑名单信息，键为黑名单类型，值为对应的黑名单数据集合
blacklists = {}

# 全局配置选项字典 options，定义了程序运行时的各种可配置参数及其默认值
# 这些选项控制着扫描行为、请求方式、输出格式等多个方面
options = {
    # 目标URL列表
    "urls": [],
    # 包含目标URL的文件路径
    "url_file": None,
    # 从标准输入读取的URL内容
    "stdin_urls": None,
    # CIDR格式的网络地址范围
    "cidr": None,
    # 原始文件路径（可能用于原始数据处理）
    "raw_file": None,
    # 会话文件路径，用于恢复之前的扫描状态
    "session_file": None,
    # 配置文件路径
    "config": None,
    # 字典文件列表，用于 fuzzing 测试
    "wordlists": (),
    # 扩展名列表，附加到字典项后进行测试
    "extensions": (),
    # 是否强制使用扩展名
    "force_extensions": False,
    # 是否覆盖默认扩展名
    "overwrite_extensions": False,
    # 要排除的扩展名列表
    "exclude_extensions": (),
    # 移除指定扩展名的规则
    "remove_extensions": None,
    # 添加前缀字符串列表
    "prefixes": (),
    # 添加后缀字符串列表
    "suffixes": (),
    # 是否将所有字符转为大写
    "uppercase": False,
    # 是否将所有字符转为小写
    "lowercase": False,
    # 是否启用首字母大写转换
    "capitalization": False,
    # 并发线程数
    "thread_count": 25,
    # 是否递归扫描目录
    "recursive": False,
    # 是否深度递归扫描
    "deep_recursive": False,
    # 强制开启递归扫描
    "force_recursive": False,
    # 最大递归深度
    "recursion_depth": 0,
    # 触发递归的HTTP状态码集合
    "recursion_status_codes": set(),
    # 子目录列表，限定扫描范围
    "subdirs": [],
    # 排除的子目录列表
    "exclude_subdirs": [],
    # 包含的状态码集合（仅显示这些状态码的结果）
    "include_status_codes": set(),
    # 排除的状态码集合
    "exclude_status_codes": set(),
    # 排除特定响应大小的结果
    "exclude_sizes": set(),
    # 排除包含特定文本的响应
    "exclude_texts": None,
    # 使用正则表达式排除匹配的响应
    "exclude_regex": None,
    # 排除重定向目标符合特定条件的响应
    "exclude_redirect": None,
    # 排除满足某响应对象特征的请求结果
    "exclude_response": None,
    # 在遇到某些状态码时跳过该次请求
    "skip_on_status": set(),
    # 设置最小响应体大小阈值
    "minimum_response_size": 0,
    # 设置最大响应体大小阈值
    "maximum_response_size": 0,
    # 每个请求的最大执行时间限制（秒）
    "maxtime": 0,
    # HTTP 请求方法，默认是 GET
    "http_method": "GET",
    # 发送的数据内容（POST等）
    "data": None,
    # 数据来源文件路径
    "data_file": None,
    # 自定义请求头字典
    "headers": {},
    # 请求头来自的文件路径
    "header_file": None,
    # 是否跟随重定向
    "follow_redirects": False,
    # 是否随机更换 User-Agent
    "random_agents": False,
    # 认证凭据信息
    "auth": None,
    # 认证类型（如 basic, digest 等）
    "auth_type": None,
    # SSL/TLS 客户端证书文件路径
    "cert_file": None,
    # SSL/TLS 客户端私钥文件路径
    "key_file": None,
    # 自定义 User-Agent 字符串
    "user_agent": None,
    # Cookie 字符串或字典
    "cookie": None,
    # 请求超时时间（秒）
    "timeout": 10,
    # 请求之间的延迟时间（秒）
    "delay": 0.0,
    # 代理服务器列表
    "proxies": [],
    # 代理设置来自的文件路径
    "proxy_file": None,
    # 代理认证信息
    "proxy_auth": None,
    # 回放代理地址（用于调试）
    "replay_proxy": None,
    # 是否通过 Tor 网络发送请求
    "tor": None,
    # URL 协议方案（http 或 https）
    "scheme": None,
    # 最大请求速率（每秒请求数）
    "max_rate": 0,
    # 失败请求最大重试次数
    "max_retries": 1,
    # 绑定使用的本地 IP 地址
    "ip": None,
    # 出现错误是否立即退出程序
    "exit_on_error": False,
    # 是否启用爬虫模式
    "crawl": False,
    # 输出完整 URL 路径而非相对路径
    "full_url": False,
    # 显示完整的重定向历史记录
    "redirects_history": False,
    # 控制终端输出是否有颜色高亮
    "color": True,
    # 是否静默模式运行（减少输出）
    "quiet": False,
    # 输出文件路径
    "output_file": None,
    # 输出格式（例如 json, xml, plain 等）
    "output_format": None,
    # 日志文件路径
    "log_file": None,
    # 输出根目录路径
    "output_path": None,
    # 是否自动保存报告
    "autosave_report": True,
    # 日志文件最大尺寸（单位未知，通常为字节）
    "log_file_size": 0
}
