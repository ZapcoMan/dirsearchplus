#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import urllib3,random,requests,json
from lib.common.CreatLog import creatLog
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED


class PostsDataText(object):
    """
    用于向指定URL发送POST请求并收集响应结果的类

    Attributes:
        log: 日志记录器实例
        UserAgent: 用户代理字符串列表，用于模拟不同浏览器
        codes: 状态码列表（未使用）
        url: 目标URL地址
        res: 存储响应结果的字典
        options: 命令行选项配置对象
        proxy_data: 代理配置字典
    """

    def __init__(self, url, options):
        """
        初始化PostsDataText实例

        Args:
            url (str): 目标URL地址
            options (object): 包含请求配置的选项对象，应包含contenttype、cookie、head、proxy、ssl_flag等属性
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
        self.url = url
        self.res = {}
        self.options = options
        self.proxy_data = {'http': self.options.proxy,'https': self.options.proxy}

    def check(self, url, data, jsondata):
        """
        向指定URL发送POST请求并处理响应

        该方法会根据配置发送POST请求，如果遇到415或401状态码会尝试切换Content-Type为application/json重试

        Args:
            url (str): 请求的目标URL
            data: 表单格式的数据
            jsondata: JSON格式的数据

        Returns:
            None: 结果存储在实例变量self.res中
        """
        urllib3.disable_warnings()  # 禁止跳出来对warning

        # 设置Content-Type，默认为application/x-www-form-urlencoded
        if self.options.contenttype != None:
            contenttype = self.options.contenttype
        else:
            contenttype = 'application/x-www-form-urlencoded'

        # 根据是否提供cookie设置请求头
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

        try:
            tag = 0
            sslFlag = int(self.options.ssl_flag)

            # 根据SSL标志决定是否验证证书
            if sslFlag == 1:
                text = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data, verify=False).text)
                code = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data,verify=False).status_code)
            else:
                text = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data).text)
                code = str(requests.post(url, headers=headers, timeout=6, data=data, proxies=self.proxy_data).status_code)

            # 如果状态码不是404或415，则保存响应结果
            if (code != "404") and (code != "415"):
                self.res[str(jsondata)] = text

            # 处理415或401状态码，尝试切换到JSON格式重试
            while (code == "415" or code == "401"):
                tag += 1
                if tag == 1:
                    # 切换Content-Type为application/json
                    if self.options.contenttype != None:
                        contenttype = self.options.contenttype
                    else:
                        contenttype = 'application/json'

                    # 重新设置请求头
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

                    # 发送新的请求
                    if sslFlag == 1:
                        code = str(requests.post(url, headers=header, timeout=6, data=jsondata,proxies=self.proxy_data,allow_redirects=False,verify=False).status_code)
                    else:
                        code = str(requests.post(url, headers=header, timeout=6, data=jsondata,proxies=self.proxy_data,allow_redirects=False).status_code)

                    # 如果成功则保存结果
                    if code == "200":
                        if sslFlag == 1:
                            text = str(requests.post(url, headers=header, timeout=6, data=jsondata, proxies=self.proxy_data,verify=False).text)
                        else:
                            text = str(requests.post(url, headers=header, timeout=6, data=jsondata, proxies=self.proxy_data).text)
                        self.res[str(jsondata)] = text
                        break

                # 如果重试次数超过1次则退出循环
                if (tag > 1):
                    break

        except Exception as e:
            self.log.error("[Err] %s" % e)

    def run(self, datas, jsondatas):
        """
        使用线程池并发执行多个POST请求

        Args:
            datas (list): 表单数据列表
            jsondatas (list): JSON数据列表

        Returns:
            dict: 包含所有请求响应结果的字典
        """
        pool = ThreadPoolExecutor(20)
        # 创建所有任务组合的列表
        allTask = [pool.submit(self.check, self.url, data, json.dumps(jsondata))  for data in datas for jsondata in jsondatas]
        # 等待所有任务完成
        wait(allTask, return_when=ALL_COMPLETED)
        return self.res

# if __name__ == '__main__':
#     try:
#         # banner()
#         che = Checkstatus()
#         che.run()
#     except KeyboardInterrupt:
#         print("停止中...")

