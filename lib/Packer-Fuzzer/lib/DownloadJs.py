# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os,requests,sqlite3,warnings,random
from urllib.parse import urlparse
from lib.common import readConfig
from lib.common.utils import Utils
from lib.common.CreatLog import creatLog


class DownloadJs():
    """
    JS文件下载处理类

    用于处理JS文件的下载、过滤黑名单域名和文件名，并将相关信息存储到数据库中
    """

    def __init__(self, jsRealPaths, options):
        """
        初始化DownloadJs类

        :param jsRealPaths: JS文件的真实路径列表
        :param options: 配置选项对象，包含代理、cookie等配置信息
        """
        # 传入的js文件的路径
        warnings.filterwarnings('ignore')
        self.jsRealPaths = jsRealPaths
        self.blacklist_domains = readConfig.ReadConfig().getValue('blacklist', 'domain')[0]
        self.blacklistFilenames = readConfig.ReadConfig().getValue('blacklist', 'filename')[0]
        self.options = options
        self.proxy_data = {'http': self.options.proxy,'https': self.options.proxy}
        self.UserAgent = ["Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
                          "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
                          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
                          "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36",
                          "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)",
                          "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
                          "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
                          "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0",
                          "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
                          "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"]
        self.log = creatLog().get_logger()

    def jsBlacklist(self):
        """
        过滤JS文件路径中的黑名单域名和文件名

        根据配置文件中的黑名单域名和文件名列表，过滤掉匹配的JS文件路径
        :return: 过滤后的JS文件路径列表
        """
        newList = self.jsRealPaths[:]  # 防止遍历不全
        for jsRealPath in newList:  # 遍历js路径
            res = urlparse(jsRealPath)
            jsRealPathDomain = res.netloc.lower()  # js的主域名
            jsRealPathFilename = Utils().getFilename(jsRealPath).lower()  # 获取js名称
            for blacklistDomain in self.blacklist_domains.split(","):  # 遍历黑名单列表
                if blacklistDomain in jsRealPathDomain:
                    flag = 1
                    break
                else:
                    flag = 0
            if flag:  # 判断js路径中是否存在黑名单
                self.jsRealPaths.remove(jsRealPath)  # 如果有就进行删除
            for blacklistFilename in self.blacklistFilenames.split(","):
                if blacklistFilename in jsRealPathFilename:
                    flag = 1
                    break
                else:
                    flag = 0
            if flag:
                if jsRealPath in self.jsRealPaths:
                    self.jsRealPaths.remove(jsRealPath)
        return self.jsRealPaths

    def downloadJs(self, tag, host, spiltId):
        """
        下载JS文件并存储到本地和数据库

        :param tag: 标签标识符
        :param host: 主机地址
        :param spiltId: 分割ID，用于区分不同的分割部分
        """
        # 构造请求头信息
        if self.options.cookie != None:
            header = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cookie': self.options.cookie,
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }
        else:
            header = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }
        self.jsRealPaths = list(set(self.jsRealPaths)) # list清单去重
        try:
            self.jsRealPaths = self.jsBlacklist()  # 不能放for循环内
            self.log.debug("js黑名单函数正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # 遍历JS文件路径并下载
        for jsRealPath in self.jsRealPaths:
            jsFilename = Utils().getFilename(jsRealPath)
            jsTag = Utils().creatTag(6)
            PATH = "tmp/" + tag + "_" + host + "/" + tag + ".db"
            conn = sqlite3.connect(os.sep.join(PATH.split('/')))
            cursor = conn.cursor()
            conn.isolation_level = None
            checkSql = "select * from js_file where name = '" + jsFilename + "'"

            # 根据spiltId构造不同的SQL语句
            if spiltId == 0:
                sql = "insert into js_file(name,path,local) values('%s','%s','%s')" % (
                    jsFilename, jsRealPath, jsTag + "." + jsFilename)
            else:
                sql = "insert into js_file(name,path,local,spilt) values('%s','%s','%s',%d)" % (
                    jsFilename, jsRealPath, jsTag + "." + jsFilename, spiltId)

            cursor.execute(checkSql)
            res = cursor.fetchall()

            # 检查文件是否已存在
            if len(res) > 0:
                self.log.info(Utils().tellTime() + Utils().getMyWord("{have_it}") + jsFilename)
                conn.close()
            else:
                cursor.execute(sql)
                conn.commit()
                self.log.info(Utils().tellTime() + Utils().getMyWord("{downloading}") + jsFilename)

                # 根据SSL标志选择是否验证证书
                sslFlag = int(self.options.ssl_flag)
                if sslFlag == 1:
                    jsFileData = requests.get(url=jsRealPath, headers=header, proxies=self.proxy_data, verify=False).content
                else:
                    jsFileData = requests.get(url=jsRealPath, proxies=self.proxy_data, headers=header).content

                # 写入文件并更新数据库状态
                with open("tmp" + os.sep + tag + "_" + host + os.sep + jsTag + "." + jsFilename, "wb") as js_file:
                    js_file.write(jsFileData)
                    js_file.close()
                    cursor.execute("UPDATE js_file SET success = 1 WHERE local='%s';" % (jsTag + "." + jsFilename))
                    conn.commit()
                conn.close()

    def creatInsideJs(self, tag, host, scriptInside, url):
        """
        创建内联JS文件（HTML中的script标签内容）

        :param tag: 标签标识符
        :param host: 主机地址
        :param scriptInside: script标签内的内容
        :param url: URL地址
        """
        try:
            jsRealPath = url
            jsFilename = "7777777.script.inside.html.js" #随便来一个
            jsTag = Utils().creatTag(6)
            PATH = "tmp/" + tag + "_" + host + "/" + tag + ".db"
            conn = sqlite3.connect(os.sep.join(PATH.split('/')))
            cursor = conn.cursor()
            conn.isolation_level = None
            sql = "insert into js_file(name,path,local) values('%s','%s','%s')" % (
                        jsFilename, jsRealPath, jsTag + "." + jsFilename)
            cursor.execute(sql)
            conn.commit()
            self.log.info(Utils().tellTime() + Utils().getMyWord("{downloading}") + jsFilename)

            # 将script内容写入文件并更新数据库
            with open("tmp" + os.sep + tag + "_" + host + os.sep + jsTag + "." + jsFilename, "wb") as js_file:
                js_file.write(str.encode(scriptInside))
                js_file.close()
                cursor.execute("UPDATE js_file SET success = 1 WHERE local='%s';" % (jsTag + "." + jsFilename))
                conn.commit()
            conn.close()
        except Exception as e:
            self.log.error("[Err] %s" % e)

