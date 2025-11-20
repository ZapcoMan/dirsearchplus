##
# 导入标准库和第三方模块
##
import sys, argparse, validators, os, tldextract
from colorama import init, Fore, Style
from pyfiglet import Figlet

import http.client
import socket
import random
import re
import requests
import threading
import time

from requests.adapters import HTTPAdapter
from requests.auth import AuthBase, HTTPBasicAuth, HTTPDigestAuth
from urllib3 import disable_warnings
from requests_ntlm import HttpNtlmAuth
from urllib.parse import urlparse

# 导入项目内部模块
from lib.core.data import options
from lib.core.decorators import cached
from lib.core.exceptions import RequestException
from lib.core.logger import logger
from lib.core.settings import (
    RATE_UPDATE_DELAY,
    READ_RESPONSE_ERROR_REGEX,
    SCRIPT_PATH,
    PROXY_SCHEMES,
)
from lib.core.structures import CaseInsensitiveDict
from lib.connection.dns import cached_getaddrinfo
from lib.connection.response import Response
from lib.utils.common import safequote
from lib.utils.file import FileUtils
from lib.utils.mimetype import guess_mimetype

# 禁用 urllib3 的 InsecureRequestWarning 警告
disable_warnings()
# 使用自定义的 socket.getaddrinfo 方法以支持 DNS 缓存功能
socket.getaddrinfo = cached_getaddrinfo


class HTTPBearerAuth(AuthBase):
    """
    自定义 Bearer Token 认证类

    Args:
        token (str): JWT 或其他类型的 Bearer Token

    Returns:
        request: 添加了 Authorization 头部的请求对象
    """

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


class Requester:
    """
    HTTP 请求发送器类，用于构建和发送 HTTP 请求，并处理认证、代理等配置

    Attributes:
        _url (str): 目标 URL 基础路径
        _proxy_cred (str): 代理认证凭据
        _rate (int): 当前请求速率计数
        headers (CaseInsensitiveDict): HTTP 请求头字典
        agents (list): 用户代理列表
        session (requests.Session): requests 库会话对象
    """

    def __init__(self):
        """初始化 Requester 实例"""
        self._url = None
        self._proxy_cred = None
        self._rate = 0
        self.headers = CaseInsensitiveDict(options["headers"])
        self.agents = []
        self.session = requests.Session()
        self.session.verify = False
        self.session.cert = (
            options["cert_file"],
            options["key_file"],
        )

        # 如果启用了随机 User-Agent，则加载用户代理列表
        if options["random_agents"]:
            self._fetch_agents()

        # 如果有请求数据且未指定 Content-Type，则自动猜测 MIME 类型
        if options["data"] and "content-type" not in self.headers:
            self.set_header("content-type", guess_mimetype(options["data"]))

        # 配置 HTTP 和 HTTPS 协议适配器，设置最大连接池大小
        for scheme in ("http://", "https://"):
            self.session.mount(
                scheme, HTTPAdapter(max_retries=0, pool_maxsize=options["thread_count"])
            )

    def _fetch_agents(self):
        """从文件中读取并设置用户代理列表"""
        self.agents = FileUtils.get_lines(
            FileUtils.build_path(SCRIPT_PATH, "db", "user-agents.txt")
        )

    def set_url(self, url):
        """
        设置目标基础 URL

        Args:
            url (str): 完整的目标 URL 地址
        """
        self._url = url

    def set_header(self, key, value):
        """
        设置 HTTP 请求头部字段

        Args:
            key (str): 头部字段名
            value (str): 头部字段值
        """
        self.headers[key] = value.lstrip()

    def set_auth(self, type, credential):
        """
        根据类型设置不同的认证方式

        Args:
            type (str): 认证类型（basic/digest/bearer/jwt/oath2/ntlm）
            credential (str): 认证凭据信息
        """
        if type in ("bearer", "jwt", "oath2"):
            self.session.auth = HTTPBearerAuth(credential)
        else:
            try:
                user, password = credential.split(":", 1)
            except ValueError:
                user = credential
                password = ""

            if type == "basic":
                self.session.auth = HTTPBasicAuth(user, password)
            elif type == "digest":
                self.session.auth = HTTPDigestAuth(user, password)
            else:
                self.session.auth = HttpNtlmAuth(user, password)

    def set_proxy(self, proxy):
        """
        设置 HTTP 代理服务器

        Args:
            proxy (str): 代理服务器地址
        """
        if not proxy:
            return

        logger.debug(f"Attempting to set proxy: {proxy}")

        # 如果没有协议前缀，默认使用 http 协议
        if not proxy.startswith(PROXY_SCHEMES):
            proxy = f"http://{proxy}"
            logger.debug(f"Proxy scheme added: {proxy}")

        # 如果存在代理认证凭据并且 URL 中不含认证信息，则插入认证凭据
        if self._proxy_cred and "@" not in proxy:
            proxy = proxy.replace("://", f"://{self._proxy_cred}@", 1)
            logger.debug(f"Proxy credentials added: {proxy}")

        # 同时为 HTTP 和 HTTPS 设置代理
        self.session.proxies = {
            "http": proxy,
            "https": proxy
        }

        logger.debug(f"Proxy set successfully for both HTTP and HTTPS: {proxy}")

        # 对于 SOCKS4a 代理提供额外调试信息
        if "socks4a" in proxy.lower():
            logger.info(f"Using SOCKS4a proxy: {proxy}. Note: SOCKS4a may require additional configuration.")

    def set_proxy_auth(self, credential):
        """
        设置代理服务器认证凭据

        Args:
            credential (str): 代理认证凭据字符串
        """
        self._proxy_cred = credential

    def request(self, path, proxy=None):
        """
        发送 HTTP 请求到指定路径

        Args:
            path (str): 请求路径（不应以 '/' 开头）
            proxy (str, optional): 指定使用的代理服务器

        Returns:
            Response: 包含响应结果的对象

        Raises:
            RequestException: 当请求失败时抛出异常
        """
        # 控制请求频率不超过最大限制
        while self.is_rate_exceeded():
            time.sleep(0.1)

        self.increase_rate()

        err_msg = None

        # 对特殊字符进行安全编码防止被错误转义
        url = safequote(self._url + path if self._url else path)

        # 循环重试直到达到最大尝试次数
        for _ in range(options["max_retries"] + 1):
            try:
                try:
                    # 尝试选择一个代理服务器
                    proxy = proxy or random.choice(options["proxies"])
                    self.set_proxy(proxy)
                except IndexError:
                    pass

                # 如果启用了随机 User-Agent，则从中随机选取一个
                if self.agents:
                    self.set_header("user-agent", random.choice(self.agents))

                # 构建预处理请求避免 URL 路径被标准化
                request = requests.Request(
                    options["http_method"],
                    url,
                    headers=self.headers,
                    data=options["data"],
                )
                prepped = self.session.prepare_request(request)
                prepped.url = url

                # 发送实际请求
                response = self.session.send(
                    prepped,
                    allow_redirects=options["follow_redirects"],
                    timeout=options["timeout"],
                    stream=True,
                )

                response = Response(response)

                # 构造日志消息记录请求详情
                log_msg = f'"{options["http_method"]} {response.url}" {response.status} - {response.length}B'

                if response.redirect:
                    log_msg += f" - LOCATION: {response.redirect}"

                logger.info(log_msg)

                return response

            except Exception as e:
                logger.exception(e)
                logger.debug(f"Detailed error information: {str(type(e))}: {str(e)}")

                # 分析具体异常类型并构造对应错误信息
                if isinstance(e, socket.gaierror):
                    err_msg = f"DNS resolution failed for {urlparse(url).netloc}: {str(e)}"
                elif "SSLError" in str(type(e)):
                    err_msg = f"SSL error connecting to {url}: {str(e)}"
                elif "TooManyRedirects" in str(type(e)):
                    err_msg = f"Too many redirects: {url}"
                elif "ProxyError" in str(type(e)):
                    err_msg = f"Proxy error with {proxy}: {str(e)}"
                    # 移除无效代理以防再次使用
                    if proxy in options["proxies"] and len(options["proxies"]) > 1:
                        options["proxies"].remove(proxy)
                elif "InvalidURL" in str(type(e)):
                    err_msg = f"Invalid URL: {url}"
                elif "InvalidProxyURL" in str(type(e)):
                    err_msg = f"Invalid proxy URL: {proxy}"
                elif "ConnectionError" in str(type(e)):
                    err_msg = f"Connection failed to {urlparse(url).netloc}: {str(e)}"
                elif re.search(READ_RESPONSE_ERROR_REGEX, str(e)):
                    err_msg = f"Failed to read response body: {url}"
                elif "Timeout" in str(type(e)) or isinstance(e, (http.client.IncompleteRead, socket.timeout)):
                    err_msg = f"Request timeout after {options['timeout']}s: {url}"
                    # 特别提示 SOCKS4a 可能需要更长超时时间或额外配置
                    if proxy and "socks4a" in proxy.lower():
                        err_msg += " (SOCKS4a might require longer timeout or additional configuration)"
                else:
                    err_msg = (
                        f"Request failed: {url} - {str(type(e))}: {str(e)}"
                    )

        raise RequestException(err_msg)

    def is_rate_exceeded(self):
        """
        判断当前请求速率是否超过设定上限

        Returns:
            bool: True 表示已超出限制，False 表示未超出
        """
        return self._rate >= options["max_rate"] > 0

    def decrease_rate(self):
        """减少当前请求速率计数"""
        self._rate -= 1

    def increase_rate(self):
        """增加当前请求速率计数并在一秒后自动减一"""
        self._rate += 1
        threading.Timer(1, self.decrease_rate).start()

    @property
    @cached(RATE_UPDATE_DELAY)
    def rate(self):
        """
        获取当前请求速率（带缓存）

        Returns:
            int: 当前每秒请求数量
        """
        return self._rate
