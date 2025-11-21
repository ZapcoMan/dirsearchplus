#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import deno_vm, os, re, sqlite3
from urllib.parse import urlparse
from .common.utils import Utils
from .Database import DatabaseType
from .DownloadJs import DownloadJs
from .common.groupBy import GroupBy
from .common.CreatLog import creatLog


class RecoverSpilt():
    """
    恢复JS代码分割的主类，用于识别并恢复被分割的JavaScript文件。

    Attributes:
        name_list (list): 名称列表
        remotePaths (list): 远程路径列表
        jsFileNames (list): JS文件名列表
        localFileNames (list): 本地文件名列表
        remoteFileURLs (list): 远程文件URL列表
        js_compile_results (list): JS编译结果列表
        projectTag (str): 项目标识
        options (object): 配置选项对象
        log (Logger): 日志记录器
    """

    def __init__(self, projectTag, options):
        """
        初始化RecoverSpilt实例

        Args:
            projectTag (str): 项目标识符
            options (object): 配置选项对象
        """
        self.name_list = []
        self.remotePaths = []
        self.jsFileNames = []
        self.localFileNames = []
        self.remoteFileURLs = []
        self.js_compile_results = []
        self.projectTag = projectTag
        self.options = options
        self.log = creatLog().get_logger()

    def jsCodeCompile(self, jsCode, jsFilePath):
        """
        编译JavaScript代码以恢复分割的文件路径

        Args:
            jsCode (str): 要编译的JavaScript代码
            jsFilePath (str): JavaScript文件路径

        Returns:
            int: 成功返回None，失败返回0
        """
        try:
            self.log.info(Utils().tellTime() + Utils().getMyWord("{get_codesplit}"))
            variable = re.findall(r'\[.*?\]', jsCode)
            if "[" and "]" in variable[0]:
                variable = variable[0].replace("[", "").replace("]", "")
            jsCodeFunc = "function js_compile(%s){js_url=" % (variable) + jsCode + "\nreturn js_url}"
            pattern_jscode = re.compile(r"\(\{\}\[(.*?)\]\|\|.\)", re.DOTALL)
            flag_code = pattern_jscode.findall(jsCodeFunc)
            if flag_code:
                jsCodeFunc = jsCodeFunc.replace("({}[%s]||%s)" % (flag_code[0], flag_code[0]), flag_code[0])
            pattern1 = re.compile(r"\{(.*?)\:")
            pattern2 = re.compile(r"\,(.*?)\:")
            nameList1 = pattern1.findall(jsCode)
            nameList2 = pattern2.findall(jsCode)
            nameList = nameList1 + nameList2
            nameList = list(set(nameList))
            projectDBPath = DatabaseType(self.projectTag).getPathfromDB() + self.projectTag + ".db"
            connect = sqlite3.connect(os.sep.join(projectDBPath.split('/')))
            cursor = connect.cursor()
            connect.isolation_level = None
            localFile = jsFilePath.split(os.sep)[-1]
            sql = "insert into js_split_tree(jsCode,js_name) values('%s','%s')" % (jsCode, localFile)
            cursor.execute(sql)
            connect.commit()
            cursor.execute("select id from js_split_tree where js_name='%s'" % (localFile))
            jsSplitId = cursor.fetchone()[0]
            cursor.execute("select path from js_file where local='%s'" % (localFile))
            jsUrlPath = cursor.fetchone()[0]
            connect.close()

            # 使用deno_vm执行JavaScript代码来获取实际文件路径
            with deno_vm.VM() as vm:
                vm.run(jsCodeFunc)
                for name in nameList:
                    if "\"" in name:
                        name = name.replace("\"", "")
                    if "undefined" not in vm.call("js_compile", name):
                        jsFileName = vm.call("js_compile", name)
                        self.jsFileNames.append(jsFileName)
            self.log.info(Utils().tellTime() + Utils().getMyWord("{run_codesplit_s}") + str(len(self.jsFileNames)))
            self.getRealFilePath(jsSplitId, self.jsFileNames, jsUrlPath)
            self.log.debug("jscodecomplie模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)  # 这块有问题，逻辑要改进
            return 0

    def checkCodeSpilting(self, jsFilePath):
        """
        检查JavaScript文件是否存在代码分割特征

        Args:
            jsFilePath (str): JavaScript文件路径
        """
        jsOpen = open(jsFilePath, 'r', encoding='UTF-8',errors="ignore")  # 防编码报错
        jsFile = jsOpen.readlines()
        jsFile = str(jsFile)  # 二次转换防报错
        if "document.createElement(\"script\");" in jsFile:
            self.log.info(
                Utils().tellTime() + Utils().getMyWord("{maybe_have_codesplit}") + Utils().getFilename(jsFilePath))
            pattern = re.compile(r"\w\.p\+\"(.*?)\.js", re.DOTALL)
            if pattern:
                jsCodeList = pattern.findall(jsFile)
                for jsCode in jsCodeList:
                    if len(jsCode) < 30000:
                        jsCode = "\"" + jsCode + ".js\""
                        self.jsCodeCompile(jsCode, jsFilePath)

    def getRealFilePath(self, jsSplitId, jsFileNames, jsUrlpath):
        """
        获取真实的文件路径并下载对应的JavaScript文件

        Args:
            jsSplitId (int): JS分割ID
            jsFileNames (list): JS文件名列表
            jsUrlpath (str): JS URL路径
        """
        # 我是没见过webpack异步加载的js和放异步的js不在同一个目录下的，这版先不管不同目录的情况吧
        jsRealPaths = []
        res = urlparse(jsUrlpath)
        resForDB = urlparse(self.options.url) # 但是会有js和扫描目标不在同一个域名的情况 现在我遇到了 这样保证数据库能正常载入
        if "§§§" in jsUrlpath:  # html中script情況
            jsUrlpath = jsUrlpath.split('§§§')[0]
            tmpUrl = jsUrlpath.split("/")
            if "." in tmpUrl[-1]:
                del tmpUrl[-1]
            base_url = "/".join(tmpUrl)
            for jsFileName in jsFileNames:
                jsFileName = base_url + jsFileName
                jsRealPaths.append(jsFileName)
        else:
            tmpUrl = jsUrlpath.split("/")
            del tmpUrl[-1]
            base_url = "/".join(tmpUrl) + "/"
            for jsFileName in jsFileNames:
                jsFileName = Utils().getFilename(jsFileName)  # 获取js名称
                jsFileName = base_url + jsFileName
                jsRealPaths.append(jsFileName)
        try:
            domain = resForDB.netloc
            if ":" in domain:
                domain = str(domain).replace(":", "_") #处理端口号
            DownloadJs(jsRealPaths,self.options).downloadJs(self.projectTag, domain, jsSplitId)
            self.log.debug("downjs功能正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def checkSpiltingTwice(self, projectPath):
        """
        二次检查代码分割，通过模式匹配和爆破方式发现可能的分割文件

        Args:
            projectPath (str): 项目路径
        """
        self.log.info(Utils().tellTime() + Utils().getMyWord("{check_codesplit_twice}"))
        for parent, dirnames, filenames in os.walk(projectPath, followlinks=True):
            for filename in filenames:
                if filename != self.projectTag + ".db":
                    tmpName = filename.split(".")
                    if len(tmpName) == 4:
                        localFileName = "." + tmpName[-2] + ".js"
                        self.localFileNames.append(localFileName)
                        remotePath = DatabaseType(self.projectTag).getJsUrlFromDB(filename, projectPath)
                        tmpRemotePath = remotePath.split("/")
                        del tmpRemotePath[-1]
                        newRemotePath = "/".join(tmpRemotePath) + "/"
                        self.remotePaths.append(newRemotePath)
        self.remotePaths = list(set(self.remotePaths))

        # 根据文件数量选择不同的处理策略
        if len(self.localFileNames) > 3:  # 一切随缘
            localFileName = self.localFileNames[0]
            for baseurl in self.remotePaths:
                tmpRemoteFileURLs = []
                res = urlparse(baseurl)
                i = 0
                while i < 500:
                    remoteFileURL = baseurl + str(i) + localFileName
                    i = i + 1
                    tmpRemoteFileURLs.append(remoteFileURL)
                GroupBy(tmpRemoteFileURLs,self.options).stat()
                tmpRemoteFileURLs = GroupBy(tmpRemoteFileURLs,self.options).start()
                for remoteFileURL in tmpRemoteFileURLs:
                    self.remoteFileURLs.append(remoteFileURL)
        else:
            for localFileName in self.localFileNames:
                for baseurl in self.remotePaths:
                    tmpRemoteFileURLs = []
                    res = urlparse(baseurl)
                    i = 0
                    while i < 500:
                        remoteFileURL = baseurl + str(i) + localFileName
                        i = i + 1
                        tmpRemoteFileURLs.append(remoteFileURL)
                    GroupBy(tmpRemoteFileURLs,self.options).stat()
                    tmpRemoteFileURLs = GroupBy(tmpRemoteFileURLs,self.options).start()
                    for remoteFileURL in tmpRemoteFileURLs:
                        self.remoteFileURLs.append(remoteFileURL)
        if self.remoteFileURLs != []:
            domain = res.netloc
            if ":" in domain:
                domain = str(domain).replace(":", "_") #处理端口号
            self.remoteFileURLs = list(set(self.remoteFileURLs))  # 其实不会重复
            self.log.info(Utils().tellTime() + Utils().getMyWord("{check_codesplit_twice_fini_1}") + str(len(self.remoteFileURLs)) + Utils().getMyWord("{check_codesplit_twice_fini_2}"))
            DownloadJs(self.remoteFileURLs,self.options).downloadJs(self.projectTag, domain, 999)  # 999表示爆破

    def recoverStart(self):
        """
        启动代码分割恢复过程的主函数
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()

        # 遍历项目路径下的所有文件进行代码分割检查
        for parent, dirnames, filenames in os.walk(projectPath, followlinks=True):
            for filename in filenames:
                if filename != self.projectTag + ".db":
                    filePath = os.path.join(parent, filename)
                    self.checkCodeSpilting(filePath)
        try:
            self.checkSpiltingTwice(projectPath)
            self.log.debug("checkSpiltingTwice模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)
        self.log.info(Utils().tellTime() + Utils().getMyWord("{check_js_fini}"))

