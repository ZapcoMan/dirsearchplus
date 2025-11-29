#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#import sys; print("运行脚本的Python路径：", sys.executable); exit()
import re,requests,warnings,sqlite3,os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from lib.common.utils import Utils
from lib.Database import DatabaseType
from lib.DownloadJs import DownloadJs
from lib.common.CreatLog import creatLog
from lib.common.cmdline import CommandLines


class ParseJs():  # 获取js进行提取
    """
    解析网页中的JavaScript资源并下载处理

    Attributes:
        url (str): 目标URL地址
        jsPaths (list): 存储从页面中提取到的相对或绝对路径的JS链接
        jsRealPaths (list): 经过处理后得到的真实完整的JS文件路径列表
        jsPathList (list): 通过正则匹配等方式额外抓取到的JS路径集合
        projectTag (str): 当前项目的唯一标识符
        options (object): 命令行传入的各种配置选项对象
        proxy_data (dict): HTTP代理设置信息
        header (dict): 请求头信息，包括User-Agent、Cookie等
        log (Logger): 日志记录器实例
    """

    def __init__(self, projectTag, url, options):
        """
        初始化ParseJs类

        Args:
            projectTag (str): 项目标签名，用于数据库和临时目录命名
            url (str): 待分析的目标网站URL
            options (object): 包含命令行参数的对象（如代理、cookie、头部信息等）
        """
        warnings.filterwarnings('ignore') #不显示警告，后期可以优化为全局的
        self.url = url
        self.jsPaths = []
        self.jsRealPaths = []
        self.jsPathList = []
        self.projectTag = projectTag
        self.options = options
        self.proxy_data = {'http': self.options.proxy,'https': self.options.proxy}
        if self.options.cookie != None:
            self.header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
                           "Cookie":options.cookie,
                           self.options.head.split(':')[0]: self.options.head.split(':')[1],
                           }
        else:
            self.header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }
        DatabaseType(self.projectTag).createProjectDatabase(self.url, 1, "0")
        self.log = creatLog().get_logger()

    def requestUrl(self):
        """
        发起HTTP请求获取目标网页源码，并从中提取所有<script>标签内的src属性以及内联JS内容。
        同时还会尝试查找<link>标签中可能存在的JS引用。
        提取的内容将保存至本地数据库与临时文件系统中供后续使用。
        """
        headers = self.header
        url = self.url
        self.log.info(Utils().tellTime() + Utils().getMyWord("{target_url}") + url)
        self.log.info(Utils().tellTime() + Utils().getMyWord("{pares_js}"))
        sslFlag = int(self.options.ssl_flag)
        if sslFlag == 1:
            demo = requests.get(url=url, headers=headers, proxies=self.proxy_data,verify=False).text
        else:
            demo = requests.get(url=url, headers=headers,proxies=self.proxy_data).text
        demo = demo.replace("<!--", "").replace("-->", "")  # 删去html注释
        soup = BeautifulSoup(demo, "html.parser")

        # 遍历所有的script标签，提取外部JS链接和内部JS内容
        for item in soup.find_all("script"):
            jsPath = item.get("src")
            if jsPath:  # 处理src空情况
                self.jsPaths.append(jsPath)
            jsPathInScript = item.text #处理script标签里面的js内容
            jsPathInScript = jsPathInScript.encode()
            if jsPathInScript:
                # 创建一个随机标签作为JS文件名
                jsTag = Utils().creatTag(6)
                res = urlparse(self.url)
                domain = res.netloc
                if ":" in domain:
                    domain = str(domain).replace(":", "_")
                PATH = "tmp/" + self.projectTag + "_" + domain +'/' + self.projectTag + ".db"

                conn = sqlite3.connect(os.sep.join(PATH.split('/')))
                cursor = conn.cursor()
                conn.isolation_level = None
                if "#" in self.url:
                    inurl = self.url.split("#")[0] + "/§§§"
                else:
                    inurl = self.url + "/§§§"
                sql = "insert into js_file(name,path,local) values('%s','%s','%s')" % (jsTag + ".js" , inurl , jsTag + ".js")
                cursor.execute(sql)
                with open("tmp" + os.sep + self.projectTag + "_" + domain + os.sep + jsTag + ".js", "wb") as js_file:
                    js_file.write(jsPathInScript)
                    js_file.close()
                    cursor.execute("UPDATE js_file SET success = 1 WHERE local='%s';" % (jsTag + ".js"))
                    conn.commit()
                conn.close()

        # 检查是否存在通过link引入的js文件（虽然少见但需要兼容）
        for item in soup.find_all("link"):  # 防止使用link标签情况
            jsPath = item.get("href")
            try:
                if jsPath[-2:] == "js":  # 防止提取css
                    self.jsPaths.append(jsPath)
            except:
                pass

        # 使用scriptCrawling方法进一步挖掘隐藏在脚本中的JS路径
        try:
            jsInScript = self.scriptCrawling(demo)
            self.log.debug("scriptCrawling模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)
        for jsPath in jsInScript:
            self.jsPaths.append(jsPath)

        # 对收集到的所有JS路径执行统一处理流程
        try:
            self.dealJs(self.jsPaths)
            self.log.debug("dealjs函数正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def dealJs(self, js_paths):  # 生成js绝对路径
        """
        将原始提取出的JS路径转换为可访问的标准URL格式，并调用DownloadJs类完成实际下载任务

        Args:
            js_paths (list): 来自不同来源的原始JS路径列表（可能是相对路径或片段）
        """
        res = urlparse(self.url)  # 处理url多余部分
        if res.path == "":
            baseUrl = res.scheme + "://" + res.netloc + "/"
        else:
            baseUrl = res.scheme + "://" + res.netloc + res.path
            if res.path[-1:] != "/":  # 文件夹没"/",若输入的是文件也会被加上，但是影响不大
                try:
                    if res.path[-3:] == "htm" or res.path[-4:] == "html":
                        baseUrl = baseUrl.rsplit("/",1)[0] + "/"
                    else:
                        baseUrl = baseUrl + "/"
                except:
                    baseUrl = baseUrl + "/"

        # 根据不同的路径类型构造正确的完整URL
        for jsPath in js_paths:  # 路径处理多种情况./ ../ / http
            if jsPath[:2] == "./":
                jsPath = jsPath.replace("./", "")
                jsRealPath = baseUrl + jsPath
                self.jsRealPaths.append(jsRealPath)
            elif jsPath[:3] == "../":
                tmpPath = res.path.split('/')
                if res.path[-1] != "/":
                    tmpPath = res.path + "/"
                    tmpPath = tmpPath.split('/')
                new_tmpPath = tmpPath[:]  # 防止解析报错
                dirCount = jsPath.count('../') + 1
                tmpCount = 1
                jsPath = jsPath.replace("../", "")
                try:
                    while tmpCount <= dirCount:
                        del new_tmpPath[-1]
                        tmpCount = tmpCount + 1
                except:
                    pass #防止有人在主路径内引用文件用多个../
                baseUrl = res.scheme + "://" + res.netloc + "/".join(new_tmpPath) + "/"
                jsRealPath = baseUrl + jsPath
                self.jsRealPaths.append(jsRealPath)
            elif jsPath[:2] == "//":  # 自适应域名js
                jsRealPath = res.scheme + ":" + jsPath
                self.jsRealPaths.append(jsRealPath)
            elif jsPath[:1] == "/":
                jsRealPath = res.scheme + "://" + res.netloc + jsPath
                self.jsRealPaths.append(jsRealPath)
            elif jsPath[:4] == "http":
                jsRealPath = jsPath
                self.jsRealPaths.append(jsRealPath)
            else:
                #jsRealPath = res.scheme + "://" + res.netloc + "/" + jsPath
                jsRealPath = baseUrl + jsPath
                self.jsRealPaths.append(jsRealPath)

        self.log.info(Utils().tellTime() + Utils().getMyWord("{pares_js_fini_1}") + str(len(self.jsRealPaths)) + Utils().getMyWord("{pares_js_fini_2}"))
        domain = res.netloc
        if ":" in domain:
            domain = str(domain).replace(":", "_") #处理端口号

        # 开始批量下载已整理好的JS文件
        DownloadJs(self.jsRealPaths,self.options).downloadJs(self.projectTag, domain, 0)

        # 如果用户指定了额外要加载的JS文件，则一并加入下载队列
        extJS = CommandLines().cmd().js
        if extJS != None:
            extJSs = extJS.split(',')
            DownloadJs(extJSs,self.options).downloadJs(self.projectTag, domain, 0)

    def scriptCrawling(self, demo):  # 处理动态生成的js内容及html内的script
        """
        进一步扫描HTML文档中的<script>标签文本区域，
        利用正则表达式识别其中嵌套定义的其他JS资源路径

        Args:
            demo (str): 已经获取到的HTML页面源代码字符串

        Returns:
            list: 找到的新JS路径列表
        """
        res = urlparse(self.url)  # 处理url多余部分
        domain = res.netloc
        if ":" in domain:
            domain = str(domain).replace(":", "_") #处理端口号
        scriptInside = "" #初始为空
        soup = BeautifulSoup(demo, "html.parser")

        # 在每个script标签内部搜索潜在的JS引用
        for item in soup.find_all("script"):
            scriptString = str(item.string)  # 防止特殊情况报错
            listSrc = re.findall(r'src=\"(.*?)\.js', scriptString)
            listSrc = list(filter(None, listSrc))
            listSrc_new = []
            for list_s in listSrc:
                listSrc_new.append(list_s + ".js")
            if not listSrc_new == []:
                for jsPath in listSrc_new:
                    self.jsPathList.append(jsPath)
            if scriptString != "None": #None被转成字符串了
                scriptInside = scriptInside + scriptString

        # 若发现有新的内联JS内容，则创建对应的临时文件存储
        if scriptInside != "":
            DownloadJs(self.jsRealPaths,self.options).creatInsideJs(self.projectTag, domain, scriptInside, self.url)
        return self.jsPathList

    def parseJsStart(self):
        """
        启动整个JS解析流程的核心入口函数
        """
        # unique_tag = DatabaseType().createProjectDatabase(self.url, 1, "0")
        # print(self.url)
        self.requestUrl()

