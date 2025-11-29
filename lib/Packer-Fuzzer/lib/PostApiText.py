#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import urllib3,random,requests
from .common.CreatLog import creatLog
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED


class PostApiText(object):
    """
    用于批量发送POST请求并获取响应结果的类

    Attributes:
        log: 日志记录器实例
        UserAgent: 用户代理字符串列表，用于模拟不同浏览器
        codes: 状态码列表（未使用）
        url: URL列表（未使用）
        urls: 待检测的URL列表
        res: 存储URL及其响应内容的字典
        options: 命令行参数配置对象
        proxy_data: 代理配置字典
    """

    def __init__(self, urls, options):
        """
        初始化PostApiText实例

        Args:
            urls (list): 需要检测的URL列表
            options (object): 包含各种配置选项的对象，如proxy、contenttype、cookie等
        """
        self.log = creatLog().get_logger()
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
        self.codes = []
        self.url = []
        self.urls = urls
        self.res = {}
        self.options = options
        self.proxy_data = {'http': self.options.proxy,'https': self.options.proxy}

    def check(self, url):
        """
        对单个URL发送POST请求并处理响应

        主要功能包括：
        1. 根据配置构建请求头和数据
        2. 发送POST请求并获取响应
        3. 处理特定状态码(415, 401)的重试机制
        4. 支持多种Content-Type格式的自动切换

        Args:
            url (str): 需要检测的URL地址

        Returns:
            None: 结果直接存储在实例变量self.res中
        """
        urllib3.disable_warnings()  # 禁止跳出来对warning
        if self.options.contenttype != None:
            contenttype = self.options.contenttype
        else:
            contenttype = 'application/x-www-form-urlencoded'
        if self.options.cookie != None:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': contenttype,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cookie': self.options.cookie,
                self.options.head.split(':')[0]:self.options.head.split(':')[1]
            }
        else:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': contenttype,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                self.options.head.split(':')[0]:self.options.head.split(':')[1]
            }
        if self.options.postdata != None:
            data = self.options.postdata
        else:
            data = "a=1"
        # s = requests.Session()
        # s.keep_alive = False
        try:
            tag = 0
            sslFlag = int(self.options.ssl_flag)
            if sslFlag == 1:
                text = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data, verify=False).text)  # 正常的返回code是int类型
                code = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data,verify=False).status_code)
            else:
                text = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data).text)
                code = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data).status_code)
            if (code != "404") and (code != "415"):
                self.res[url] = text
            while (code == "415" or code == "401"):
                tag += 1
                if tag == 1:
                    if self.options.contenttype != None:
                        contenttype = self.options.contenttype
                    else:
                        contenttype = 'application/json'
                    if self.options.cookie != None:
                        header = {
                            'User-Agent': random.choice(self.UserAgent),
                            'Content-Type': contenttype,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Cookie': self.options.cookie,
                            self.options.head.split(':')[0]: self.options.head.split(':')[1]

                        }
                    else:
                        header = {
                            'User-Agent': random.choice(self.UserAgent),
                            'Content-Type': contenttype,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            self.options.head.split(':')[0]: self.options.head.split(':')[1]

                        }
                    if self.options.postdata != None:
                        data = self.options.postdata
                    else:
                        data = '{"a": "1"}'
                    code = str(requests.post(url, headers=header, timeout=6, data=data, proxies=self.proxy_data, allow_redirects=False, verify=False).status_code)
                    if code == "200":
                        text = str(
                            requests.post(url, headers=header, timeout=6, data=data, proxies=self.proxy_data, verify=False).text)  # 正常的返回code是int类型
                        self.res[url] = text
                        break

                if tag == 2:
                    if self.options.contenttype != None:
                        contenttype = self.options.contenttype
                    else:
                        contenttype = 'application/xml'
                    if self.options.cookie != None:
                        header = {
                            'User-Agent': random.choice(self.UserAgent),
                            'Content-Type': contenttype,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Cookie': self.options.cookie,
                            self.options.head.split(':')[0]: self.options.head.split(':')[1]
                        }
                    else:
                        header = {
                            'User-Agent': random.choice(self.UserAgent),
                            'Content-Type': contenttype,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            self.options.head.split(':')[0]: self.options.head.split(':')[1]

                        }
                    if self.options.postdata != None:
                        data = self.options.postdata
                    else:
                        data = '<a>1</a>'
                    if sslFlag == 1:
                        code = str(requests.post(url, headers=header, timeout=6, data=data, proxies=self.proxy_data,allow_redirects=False,verify=False).status_code)
                    else:
                        code = str(requests.post(url, headers=header, timeout=6, data=data, proxies=self.proxy_data,allow_redirects=False).status_code)
                    if code == "200":
                        if sslFlag == 1:
                            text = str(requests.post(url, headers=header, timeout=6, data=data,proxies=self.proxy_data,allow_redirects=False,verify=False).text)
                        else:
                            text = str(requests.post(url, headers=header, timeout=6, data=data,proxies=self.proxy_data,allow_redirects=False).text)
                        self.res[url] = text
                        break
                # 如果状态码还是415 同时已经有了三次了
                if (tag > 2):
                    break

            # self.res[url] = text
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def run(self):
        """
        并发执行所有URL的检测任务

        使用线程池并发处理多个URL的POST请求，
        提高检测效率

        Returns:
            dict: 包含所有成功请求的URL及其响应内容的字典
        """
        pool = ThreadPoolExecutor(20)
        allTask = [pool.submit(self.check, domain) for domain in self.urls]
        wait(allTask, return_when=ALL_COMPLETED)
        return self.res

# if __name__ == '__main__':
#     try:
#         # banner()
#         che = Checkstatus()
#         che.run()
#     except KeyboardInterrupt:
#         print("停止中...")

