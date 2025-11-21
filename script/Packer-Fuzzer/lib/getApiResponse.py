#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import urllib3,random,requests
from time import sleep
from tqdm import tqdm,trange
from lib.common.utils import Utils
from lib.common.CreatLog import creatLog
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED


class ApiResponse(object):
    """
    API响应处理类，用于批量检测URL的HTTP状态码并分类

    参数:
        urls (list): 待检测的URL列表
        options (object): 配置选项对象，包含请求相关的配置参数

    属性:
        log: 日志记录器实例
        UserAgent (list): 用户代理字符串列表，用于模拟不同浏览器
        codes (list): 状态码存储列表（未使用）
        url (list): URL存储列表（未使用）
        urls (list): 待检测的URL列表
        res (dict): 存储URL检测结果的字典
        options (object): 配置选项对象
        proxy_data (dict): 代理配置数据
    """

    def __init__(self, urls,options):
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
        检测单个URL的HTTP状态码并进行分类处理

        参数:
            url (str): 待检测的URL地址

        返回值:
            无直接返回值，结果存储在self.res字典中
            状态码分类:
                1: 非404状态码（表示资源存在）
                2: 405或401状态码（表示方法不允许或需要认证）
                0: 404状态码（表示资源不存在）
        """
        urllib3.disable_warnings()  # 禁止跳出来对warning

        # 设置Content-Type请求头
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
                'Cookie':self.options.cookie,
                self.options.head.split(':')[0]: self.options.head.split(':')[1]

            }
        else:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': contenttype,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                self.options.head.split(':')[0]: self.options.head.split(':')[1]

            }

        s = requests.Session()
        s.keep_alive = False
        sslFlag = int(self.options.ssl_flag)

        try:
            # 根据SSL标志选择是否验证证书
            if sslFlag == 1:
                code = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data, verify=False).status_code)  # 正常的返回code是int类型
            else:
                code = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data).status_code)

            # 根据状态码进行分类处理
            if code != "404":
                self.res[url] = 1

            if code == "405" or code == "401":
                self.res[url] = 2

            elif code == "404":
                self.res[url] = 0

        except Exception as e:
            self.log.error("[Err] %s" % e)

    def run(self):
        """
        执行批量URL检测任务

        返回值:
            dict: 包含所有URL检测结果的字典，键为URL，值为状态分类码
        """
        # target = (url for url in self.urls)
        self.log.info(Utils().tellTime() + Utils().getMyWord("{response_start}"))
        nums = len(self.urls)

        # 显示进度条动画
        for _ in trange(nums):
            sleep(0.01)

        # 创建线程池并发执行检测任务
        pool = ThreadPoolExecutor(20)
        allTask = [pool.submit(self.check, domain) for domain in self.urls]
        wait(allTask, return_when=ALL_COMPLETED)
        return self.res
        # for future in as_completed(allTask):
        #     data = future.result()
        #     print(data)

# if __name__ == '__main__':

