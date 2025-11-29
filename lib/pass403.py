import requests, validators, os, tldextract,sys
from colorama import init, Fore, Style
from pyfiglet import Figlet
from requests.packages import urllib3

from lib.view.terminal import output
from lib.view.colors import set_color

urllib3.disable_warnings()
import time

init()

class Arguments():
    """
    参数处理类，用于解析和验证输入的URL或目录参数。

    Attributes:
        url (str): 单个目标URL。
        urllist (str): 包含多个URL的文件路径。
        dir (str): 单个目标目录路径。
        dirlist (str): 包含多个目录的文件路径。
        urls (list): 存储所有有效的URL列表。
        dirs (list): 存储所有有效的目录列表。
    """

    def __init__(self, url, urllist, dir, dirlist):
        """
        初始化Arguments实例，并进行参数校验。

        Args:
            url (str): 单个目标URL。
            urllist (str): 包含多个URL的文件路径。
            dir (str): 单个目标目录路径。
            dirlist (str): 包含多个目录的文件路径。
        """
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
        返回已处理好的URL列表。

        Returns:
            list: 所有有效URL组成的列表。
        """
        return self.urls

    def return_dirs(self):
        """
        返回已处理好的目录列表。

        Returns:
            list: 所有有效目录组成的列表。
        """
        return self.dirs

    def checkURL(self):
        """
        校验并加载URL参数。支持单个URL或从文件中读取多个URL。
        """
        if self.url:
            if not validators.url(self.url):
                #print("You must specify a valid URL for -u (--url) argument! Exitting...\n")
                sys.exit()

            if self.url.endswith("/"):
                self.url = self.url.rstrip("/")

            self.urls.append(self.url)
        elif self.urllist:
            if not os.path.exists(self.urllist):
                #print("The specified path to URL list does not exist! Exitting...\n")
                sys.exit()

            with open(self.urllist, 'r') as file:
                temp = file.readlines()

            for x in temp:
                self.urls.append(x.strip())
        else:
            #print("Please provide a single URL or a list either! (-u or -U)\n")
            sys.exit()

    def checkDir(self):
        """
        校验并加载目录参数。支持单个目录或从文件中读取多个目录。
        """
        if self.dir:
            if not self.dir.startswith("/"):
                self.dir = "/" + self.dir

            if self.dir.endswith("/") and self.dir != "/":
                self.dir = self.dir.rstrip("/")
            self.dirs.append(self.dir)
        elif self.dirlist:
            if not os.path.exists(self.dirlist):
                #print("The specified path to directory list does not exist! Exitting...\n")
                sys.exit()

            with open(self.dirlist, 'r') as file:
                temp = file.readlines()

            for x in temp:
                self.dirs.append(x.strip())
        else:
            self.dir = "/"


class PathRepository():
    """
    路径操作仓库类，用于生成各种绕过检测的路径变体及HTTP头信息。

    Attributes:
        path (str): 原始路径。
        newPaths (list): 经过编码、拼接等变换后的路径集合。
        newHeaders (list): 伪造IP地址相关的头部信息集合。
        rewriteHeaders (list): 用于重写原始URL的头部信息集合。
    """

    def __init__(self, path):
        """
        初始化PathRepository实例，并构建路径与头部数据。

        Args:
            path (str): 需要被转换的目标路径。
        """
        self.path = path
        self.newPaths = []
        self.newHeaders = []
        self.rewriteHeaders = []

        self.createNewPaths()
        self.createNewHeaders()

    def createNewPaths(self):
        """
        构造多种可能绕过的路径格式，包括双斜杠、点号、特殊字符结尾等方式。
        """
        self.newPaths.append(self.path)

        pairs = [["/", "//"], ["/.", "/./"]]

        leadings = ["/%2e"]

        trailings = ["/","/*/","/*", "..;/", "/..;/", "%20", "%09", "%00",
                     ".json", ".css", ".html", "?", "??", "???",
                     "?testparam", "#", "#test", "/."]

        for pair in pairs:
            self.newPaths.append(pair[0] + self.path + pair[1])

        for leading in leadings:
            self.newPaths.append(leading + self.path)

        for trailing in trailings:
            self.newPaths.append(self.path + trailing)

    def createNewHeaders(self):
        """
        构建伪造来源IP的HTTP头部信息以及URL重写的头部信息。
        """


class Query():
    """
    查询执行器类，负责发送不同类型的请求（GET/POST）并分析响应结果。

    Attributes:
        url (str): 目标网站的基础URL。
        dir (str): 当前测试的路径。
        dirObject (PathRepository): 对应路径的操作对象。
        domain (str): 提取自URL的主域名部分。
        session (requests.Session): 请求会话对象，用于保持连接状态。
        timeout (int): 请求超时时间，默认为10秒。
        max_retries (int): 最大重试次数，默认为3次。
    """

    def __init__(self, url, dir, dirObject, session=None, timeout=10):
        """
        初始化Query实例。

        Args:
            url (str): 目标网站基础URL。
            dir (str): 测试路径。
            dirObject (PathRepository): 路径操作对象。
            session (requests.Session, optional): 可选的请求会话对象。
            timeout (int): 请求超时时间，默认为10秒。
        """
        self.url = url
        self.dir = dir  # call pathrepo by this
        self.dirObject = dirObject
        self.domain = tldextract.extract(self.url).domain
        # 使用会话对象以复用连接
        self.session = session or requests.Session()
        self.timeout = timeout  # 设置超时时间
        self.max_retries = 3  # 设置最大重试次数

    def checkStatusCode(self, status_code):
        """
        根据HTTP状态码返回对应的颜色标记字符串。

        Args:
            status_code (int): HTTP响应状态码。

        Returns:
            str: 表示颜色的ANSI转义序列。
        """
        if status_code in (200, 201, 204):
            colour = set_color(str(status_code), fore="green")
        elif status_code == 401:
            colour = set_color(str(status_code), fore="yellow")
        elif status_code == 403:
            colour = set_color(str(status_code), fore="blue")
        elif status_code in range(500, 600):
            colour = set_color(str(status_code), fore="red")
        elif status_code in range(300, 400):
            colour = set_color(str(status_code), fore="cyan")
        else:
            colour = set_color(str(status_code), fore="magenta")

        return colour

    def writeToFile(self, array):
        """
        将结果数组中的每一项写入到以域名为名的文本文件中。

        Args:
            array (list): 待保存的结果列表。
        """
        with open(self.domain + ".txt", "a") as file:
            for line in array:
                file.write(line + "\n")

    def send_request(self, method, url, **kwargs):
        """
        发送指定方法的HTTP请求，并实现指数退避重试机制。

        Args:
            method (str): HTTP方法类型，如'GET'或'POST'。
            url (str): 完整的请求URL。
            **kwargs: 其他传递给requests.request的参数。

        Returns:
            Response or None: 成功则返回Response对象，失败超过最大尝试次数后返回None。
        """
        # 发送请求并添加重试机制
        retries = 0
        while retries <= self.max_retries:
            try:
                response = self.session.request(method, url, timeout=self.timeout, verify=False, **kwargs)
                return response
            except requests.RequestException as e:
                retries += 1
                if retries > self.max_retries:
                    return None
                # 指数退避策略
                time.sleep(0.5 * (2 ** (retries - 1)))

    def manipulateRequest(self):
        """
        执行初始POST请求探测，并调用后续路径和头部操纵逻辑。
        """
        #print((" Target URL: " + self.url + "\tTarget Path: " + self.dir + " ").center(121, "="))
        results = []

        p = self.send_request('POST', self.url + self.dir)
        if p is None:
            return

        colour = self.checkStatusCode(p.status_code)
        reset = Style.RESET_ALL

        line_width = 70
        target_address = "POST --> " + self.url + self.dir
        target_address = set_color(target_address, fore="green")
        info = f"STATUS: {colour}\tSIZE: {len(p.content)}"
        info = set_color(info, fore="green")
        info_pure = f"STATUS: {p.status_code}\tSIZE: {len(p.content)}"
        info_pure = set_color(info_pure, fore="green")
        remaining = line_width - len(target_address)
        if p.status_code !=403:
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}] " + target_address + " " * remaining + info
            output.new_line(set_color(message, fore="green"))

        if p.status_code==200:
            res_h = self.send_request('GET', self.url)
            if res_h and len(p.content) != len(res_h.content):
                # results.append(target_address + " " * remaining + info_pure)
                message = target_address + " " * remaining + info_pure
                results.append(set_color(message, fore="green"))
        else:
            message = target_address + " " * remaining + info_pure
            results.append(set_color(message, fore="green"))

        self.writeToFile(results)

        self.manipulatePath()

    def manipulatePath(self):
        """
        遍历所有构造的新路径，逐个发起GET请求并记录结果。
        """
        results = []
        reset = Style.RESET_ALL
        line_width = 70

        for path in self.dirObject.newPaths:
            r = self.send_request('GET', self.url + path)
            if r is None:
                continue

            colour = self.checkStatusCode(r.status_code)

            target_address =  "GET --> "+ self.url + path
            target_address = set_color(target_address, fore="green")
            info = f"STATUS: {colour}\tSIZE: {len(r.content)}"
            info = set_color(info, fore="green")
            info_pure = f"STATUS: {r.status_code}\tSIZE: {len(r.content)}"
            info_pure = set_color(info_pure, fore="green")
            remaining = line_width - len(target_address)
            if r.status_code != 403:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] " + target_address + " " * remaining + info
                output.new_line(set_color(message, fore="green"))
            if r.status_code==200:
                res_h = self.send_request('GET', self.url)
                if res_h and len(r.content) != len(res_h.content):
                    message = target_address + " " * remaining + info_pure
                    results.append(set_color(message, fore="green"))
            else:
                message = target_address + " " * remaining + info_pure
                results.append(set_color(message, fore="yellow"))

        self.writeToFile(results)
        self.manipulateHeaders()

    def manipulateHeaders(self):
        """
        利用伪造IP和URL重写头部分别进行GET请求探测，并输出结果。
        """
        results = []
        line_width = 70

        for header in self.dirObject.newHeaders:
            r = self.send_request('GET', self.url + self.dir, headers=header)
            if r is None:
                continue

            colour = self.checkStatusCode(r.status_code)
            reset = Style.RESET_ALL

            target_address = set_color(" GET -->" , fore="green") + self.url + self.dir
            target_address = set_color(target_address, fore="green")
            info = f"STATUS: {colour}\tSIZE: {len(r.content)}"
            info_pure = f"STATUS: {r.status_code}\tSIZE: {len(r.content)}"
            info_pure = set_color(info_pure, fore="green")
            remaining = line_width - len(target_address)

            if r.status_code != 403:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] " + target_address + " " * remaining + info
                output.new_line(set_color(message, fore="green"))
                
                header_message = f"[{current_time}] Header= {header}"
                # output.new_line(header_message)
                output.new_line(set_color(header_message, fore="green"))
            if r.status_code==200:
                res_h = self.send_request('GET', self.url)
                if res_h and len(r.content) !=len(res_h.content):
                    message = "\n" + target_address + " " * remaining + info_pure+ f"---Header= {header}"
                    results.append(set_color(message, fore="green"))
            else:
                message ="\n" + target_address + " " * remaining + info_pure + f"---Header= {header}"
                results.append(set_color(message, fore="yellow"))
        self.writeToFile(results)

        results_2 = []
        for header in self.dirObject.rewriteHeaders:
            r = self.send_request('GET', self.url, headers=header)
            if r is None:
                continue

            colour = self.checkStatusCode(r.status_code)
            reset = Style.RESET_ALL

            target_address = "GET --> " + self.url
            target_address = set_color(target_address, fore="green")
            info = f"" + set_color("STATUS:", fore="green") + " {colour}\tSIZE: {len(r.content)}"
            info = set_color(info, fore="green")
            info_pure = f"STATUS: {r.status_code}\tSIZE: {len(r.content)}"
            info_pure = set_color(info_pure, fore="green")
            remaining = line_width - len(target_address)

            if r.status_code != 403:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] " + target_address + " " * remaining + info
                output.new_line(set_color(message, fore="green"))
                
                header_message = f"[{current_time}] Header= {header}"
                output.new_line(set_color(header_message, fore="green"))
            if r.status_code ==200:
                res_h = self.send_request('GET', self.url)
                if res_h and len(r.content) != len(res_h.content):
                    results_2.append(set_color("\n" + target_address + " " * remaining + info_pure + f"---Header= {header}", fore="green"))
            else:
                results_2.append(set_color("\n" + target_address + " " * remaining + info_pure + f"---Header= {header}", fore="yellow"))

        self.writeToFile(results_2)


class Program():
    """
    主程序控制类，协调整个扫描流程。

    Attributes:
        urllist (list): 所有待测URL列表。
        dirlist (list): 所有待测目录列表。
        sessions (dict): 为每个URL维护独立的Session对象字典。
    """

    def __init__(self, urllist, dirlist):
        """
        初始化Program实例。

        Args:
            urllist (list): 待测URL列表。
            dirlist (list): 待测目录列表。
        """
        self.urllist = urllist
        self.dirlist = dirlist
        # 为每个URL创建一个会话以复用连接
        self.sessions = {url: requests.Session() for url in urllist}

    def initialise(self):
        """
        启动扫描任务：遍历所有URL和目录组合，依次执行路径探测。
        """
        for u in self.urllist:
            session = self.sessions[u]
            for d in self.dirlist:
                if d != "/":
                    dir_objname = d.lstrip("/")
                else:
                    dir_objname = "_rootPath"
                locals()[dir_objname] = PathRepository(d)
                domain_name = tldextract.extract(u).domain
                locals()[domain_name] = Query(u, d, locals()[dir_objname], session=session)
                locals()[domain_name].manipulateRequest()

