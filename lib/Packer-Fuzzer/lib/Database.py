#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sqlite3, os, time
from html import escape
from urllib.parse import quote
from urllib.parse import urlparse
from lib.common.utils import Utils
from lib.common.CreatLog import creatLog
from lib.common.readConfig import ReadConfig


class DatabaseType():
    """
    数据库操作类，用于管理主数据库和项目数据库的创建、读取与更新。

    Attributes:
        projectTag (str): 项目的唯一标识符。
        log (Logger): 日志记录器实例。
    """

    def __init__(self, project_tag):
        """
        初始化DatabaseType对象。

        Args:
            project_tag (str): 项目的标签名称。
        """
        self.projectTag = project_tag
        self.log = creatLog().get_logger()

    def createDatabase(self):
        """
        创建主数据库（main.db）及其中的project表。如果数据库已存在则跳过创建过程。
        """
        path = os.getcwd() + os.sep + "main.db"
        try:
            if not os.path.exists(path):
                connect = sqlite3.connect(path)
                cursor = connect.cursor()
                connect.isolation_level = None
                cursor.execute('''CREATE TABLE if not exists project(
                             id         INTEGER PRIMARY KEY     autoincrement,
                             tag        TEXT                    NOT NULL,
                             host       TEXT                            ,
                             time       INT                             ,
                             process    TEXT                            ,
                             finish     INT                             );''')
                connect.commit()
                connect.close()
            self.log.debug("主数据库创建成功")
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def createProjectDatabase(self, url, type, cloneTag):
        """
        根据给定的URL和类型信息创建项目专用数据库，并初始化相关数据表。

        Args:
            url (str): 目标网站的URL地址。
            type (int): 类型标识，1表示简单模式，其他值表示高级模式。
            cloneTag (str): 克隆任务的标记。
        """
        if type == 1:
            typeValue = "simple"
        else:
            typeValue = "adv"
        unixTime = int(time.time())
        res = urlparse(url)
        domain = res.netloc
        if ":" in domain:
            domain = str(domain).replace(":", "_")
        PATH = "tmp/" + self.projectTag + "_" + domain + '/' + self.projectTag + ".db"
        try:
            if Utils().creatSometing(2, PATH) == 1:
                connect = sqlite3.connect(os.sep.join(PATH.split('/')))
                cursor = connect.cursor()
                connect.isolation_level = None
                cursor.execute('''CREATE TABLE if not exists info(
                             name       TEXT    PRIMARY KEY     NOT NULL,
                             vaule      TEXT                            );''')
                cursor.execute('''CREATE TABLE if not exists js_file(
                             id         INTEGER PRIMARY KEY     autoincrement,
                             name       TEXT                    NOT NULL,
                             path       TEXT                            ,
                             local      TEXT                            ,
                             success    INT                             ,
                             spilt      INT                             );''')
                cursor.execute('''CREATE TABLE if not exists js_split_tree(
                             id         INTEGER PRIMARY KEY     autoincrement,
                             jsCode    TEXT                            ,
                             js_name    TEXT                            ,
                             js_result  TEXT                            ,
                             success    INT                             );''')
                cursor.execute('''CREATE TABLE if not exists api_tree(
                             id         INTEGER PRIMARY KEY     autoincrement,
                             path       TEXT                            ,
                             name       TEXT                    NOT NULL,
                             option     TEXT                            ,
                             result     TEXT                            ,
                             success    INT                             ,
                             from_js    INT                             );''')
                cursor.execute('''CREATE TABLE if not exists vuln(
                             id         INTEGER PRIMARY KEY     autoincrement,
                             api_id     INT                     NOT NULL,
                             js_id      INT                     NOT NULL,
                             type       TEXT                            ,
                             sure       INT                             ,
                             request_b  TEXT                            ,
                             response_b TEXT                            ,
                             response_h TEXT                            ,
                             des        TEXT                            );''')
            cursor.execute("insert into info values('time', '%s')" % (unixTime))
            cursor.execute("insert into info values('url', '%s')" % (url))
            cursor.execute("insert into info values('host','%s')" % (domain))
            cursor.execute("insert into info values('type', '%s')" % (typeValue))
            cursor.execute("insert into info values('tag', '%s')" % (self.projectTag))
            cursor.execute("insert into info (name) VALUES ('clone')")
            connect.commit()
            connect.close()
            conn2 = sqlite3.connect(os.getcwd() + os.sep + "main.db")
            cursor2 = conn2.cursor()
            conn2.isolation_level = None
            sql = "INSERT into project (tag,host,time) VALUES ('" + self.projectTag + "', '" + domain + "', " + str(
                unixTime) + ")"
            cursor2.execute(sql)
            conn2.commit()
            conn2.close()
            self.log.debug("数据库创建成功")
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def getPathfromDB(self):
        """
        从主数据库中获取指定项目的存储路径。

        Returns:
            str: 项目对应的文件夹路径；若未找到对应项目，则返回默认路径。
        """
        path = os.getcwd() + os.sep + "main.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select host from project where tag = '" + self.projectTag + "'")
        result = cursor.fetchone()
        conn.close()
        if result:
            host = result[0]  # 第一个结果
            projectPath = "tmp" + os.sep + self.projectTag + "_" + host + os.sep
            return projectPath
        else:
            # 如果没有找到项目，返回默认路径
            return "tmp" + os.sep + self.projectTag + "_unknown" + os.sep

    def getJsUrlFromDB(self, localFileName, projectPath):
        """
        从项目数据库中根据本地JS文件名查询其远程路径。

        Args:
            localFileName (str): JS文件的本地名称。
            projectPath (str): 项目所在目录路径。

        Returns:
            str: 对应的远程JS文件路径。
        """
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select path from js_file where local = '" + localFileName + "'")
        remotePath = cursor.fetchone()[0]  # 第一个即可
        conn.close()
        return remotePath

    def getJsIDFromDB(self, localFileName, projectPath):
        """
        从项目数据库中根据本地JS文件名查询其ID。

        Args:
            localFileName (str): JS文件的本地名称。
            projectPath (str): 项目所在目录路径。

        Returns:
            int: 对应的JS文件ID。
        """
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select id from js_file where local = '" + localFileName + "'")
        jsFileID = cursor.fetchone()[0]  # 第一个即可
        conn.close()
        return jsFileID

    def apiRecordToDB(self, js_path, api_path):
        """
        将解析出的API路径记录到项目数据库中的api_tree表。

        Args:
            js_path (str): JS文件的路径。
            api_path (str): 解析得到的API路径。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        connect = sqlite3.connect(os.sep.join(projectDBPath.split('/')))
        cursor = connect.cursor()
        localFileName = js_path.split(os.sep)[-1]
        jsFileID = DatabaseType(self.projectTag).getJsIDFromDB(localFileName, projectPath)
        connect.isolation_level = None
        sql = "insert into api_tree(path,name,from_js) values(\"" + api_path + "\",\"" + api_path.split("/")[
            -1] + "\"," + str(jsFileID) + ")"
        cursor.execute(sql)
        connect.commit()
        connect.close()

    # 判断API在数据库内是否已经存在
    def apiHaveOrNot(self, api_path):
        """
        检查某个API路径是否已经在数据库中存在。

        Args:
            api_path (str): 要检查的API路径。

        Returns:
            bool: 若不存在返回True，否则返回False。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select path from api_tree where path = \"" + api_path + "\"")
        row = cursor.fetchone()
        conn.close()
        if row == None:
            return True
        else:
            return False

    # 获取数据库里面的path
    def apiPathFromDB(self):
        """
        从项目数据库中提取所有API路径。

        Returns:
            list[str]: 所有API路径组成的列表。
        """
        apis = []
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select path from api_tree")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            # print("".join(row))
            api = "".join(row)
            apis.append(api)
        return apis

    def insertResultFrom(self, res):
        """
        更新API扫描状态至数据库。

        Args:
            res (dict): 键为API路径，值为其扫描状态码。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        for path, suc in res.items():
            # print(path, suc)
            sql = "UPDATE api_tree SET success=" + str(suc) + " WHERE path=\"" + path + '\"'
            cursor.execute(sql)
            # conn.commit()
        conn.close()

    def getURLfromDB(self):
        """
        从项目数据库中获取目标站点的原始URL。

        Returns:
            str: 原始URL字符串；如果没有找到则返回空字符串。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select vaule from info where name = 'url'")
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]  # 返回第一个结果
        else:
            return ""  # 如果没有结果，返回空字符串

    # 获取success为1的路径
    def sucesssPathFromDB(self):
        """
        提取数据库中扫描成功的API路径（success=1）。

        Returns:
            list[str]: 成功路径列表。
        """
        paths = []
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select path from api_tree where success=1")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            api = "".join(row)
            paths.append(api)
        return paths

    # 获取sucess为2的路径 post请求
    def wrongMethodFromDB(self):
        """
        提取数据库中标记为POST方法但实际是GET的API路径（success=2）。

        Returns:
            list[str]: 需要重新测试的路径列表。
        """
        paths = []
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select path from api_tree where success=2")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            api = "".join(row)
            paths.append(api)
        return paths

    # 获取sucess为1和2的所有存在路径
    def allPathFromDB(self):
        """
        合并获取success为1和2的所有有效路径。

        Returns:
            list[str]: 包含所有有效路径的列表。
        """
        paths = []
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        cursor.execute("select path from api_tree where success=1 or success=2")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            api = "".join(row)
            paths.append(api)
        return paths

    #更新请求类型 POST或GET
    def updatePathsMethod(self,code):
        """
        根据传入的状态码切换API路径的请求方式（GET <-> POST）。

        Args:
            code (int): 状态码，1表示将success=2改为1，其他情况相反。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        if code == 1:
            sql = "UPDATE api_tree SET success = 1 WHERE success = 2"
        else:
            sql = "UPDATE api_tree SET success = 2 WHERE success = 1"
        cursor.execute(sql)
        conn.close()

    # 将结果写入数据库
    def insertTextFromDB(self, res):
        """
        将API响应内容写入数据库，同时过滤掉无效或黑名单扩展的内容。

        Args:
            res (dict): 键为API路径，值为其响应文本。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        for url, text in res.items():
            blacks = ReadConfig()
            blacks.getValue("blacklist", "apiExts")
            black_ext = "".join(blacks.res).split(",")
            try:
                for ext in black_ext:
                    if ("<html" not in text) and ("PNG" not in text) and (len(text) != 0) and (url.split("/")[-1] != "favicon.ico")\
                            and (("." + str(url.split("/")[-1].split(".")[-1])) != ext):
                        sql = "UPDATE api_tree SET result=\'" + escape(text) + "\' WHERE path=\"" + url + '\"'
                    else:
                        sql = "UPDATE api_tree SET success=0 WHERE path=\"" + url + '\"'
                cursor.execute(sql)
                self.log.debug("数据库插入成功")
            except Exception as e:
                self.log.debug("插入时有些例外")
        conn.close()

    def insertCorsInfoIntoDB(self, request_b, response_h):
        """
        插入跨域资源共享(CORS)漏洞检测结果到vuln表。

        Args:
            request_b (dict): 请求头信息字典。
            response_h (dict): 响应头信息字典。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        request_b = "Origin: " + request_b['Origin']
        # response_h = "Access-Control-Allow-Origin: " + response_h['Access-Control-Allow-Origin'] +", Access-Control-Allow-Methods: " + response_h['Access-Control-Allow-Methods'] + ", Access-Control-Allow-Credentials: " + response_h['Access-Control-Allow-Credentials']
        response_h = "Access-Control-Allow-Origin: " + response_h['Access-Control-Allow-Origin']  + ", Access-Control-Allow-Credentials: " + response_h['Access-Control-Allow-Credentials']

        sql = "insert into vuln(sure,api_id,js_id,type,request_b,response_h) VALUES(1,7777777,7777777,'CORS',\"" + request_b + "\",\'" + response_h + "\');"
        cursor.execute(sql)
        conn.close()

    # 将弱口令成功的写入数据库
    def insertWeakPassInfoIntoDB(self, api_id,js_id,request_b, response_h):
        """
        记录弱密码漏洞检测结果到vuln表。

        Args:
            api_id (int): API ID。
            js_id (int): JS文件ID。
            request_b (str): 请求体内容。
            response_h (str): 响应体内容。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        sql = "insert into vuln(api_id,js_id,request_b,response_b,type,sure) values ('%d','%d','%s','%s','passWord',1)" % (
                        api_id, js_id, request_b, response_h)
        cursor.execute(sql)
        conn.close()


    def insertBacInfoIntoDB(self, api_id,js_id,request_b, response_h):
        """
        记录越权访问(BAC)漏洞检测结果到vuln表。

        Args:
            api_id (int): API ID。
            js_id (int): JS文件ID。
            request_b (str): 请求体内容。
            response_h (str): 响应体内容。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        sql = "insert into vuln(api_id,js_id,request_b,response_b,type,sure) values ('%d','%d','%s','%s','BAC',1)" % (
                        api_id, js_id, request_b, response_h)
        cursor.execute(sql)
        conn.close()

    def insertUploadInfoIntoDB(self, api_id,js_id,request_b, response_h):
        """
        记录任意文件上传漏洞检测结果到vuln表。

        Args:
            api_id (int): API ID。
            js_id (int): JS文件ID。
            request_b (str): 请求体内容。
            response_h (str): 响应体内容。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        sql = "insert into vuln(api_id,js_id,request_b,response_b,type,sure) values ('%d','%d','%s','%s','upLoad',1)" % (
                        api_id, js_id, request_b, response_h)
        cursor.execute(sql)
        conn.close()

    def insertSQLInfoIntoDB(self, api_id, js_id, request_b, response_h):
        """
        记录SQL注入漏洞检测结果到vuln表。

        Args:
            api_id (int): API ID。
            js_id (int): JS文件ID。
            request_b (str): 请求体内容。
            response_h (str): 响应体内容。
        """
        projectPath = DatabaseType(self.projectTag).getPathfromDB()
        projectDBPath = projectPath + self.projectTag + ".db"
        conn = sqlite3.connect(projectDBPath)
        cursor = conn.cursor()
        conn.isolation_level = None
        sql = "insert into vuln(api_id,js_id,request_b,response_b,type,sure) values ('%d','%d','%s','%s','SQL',1)" % (
            api_id, js_id, request_b, response_h)
        cursor.execute(sql)
        conn.close()
