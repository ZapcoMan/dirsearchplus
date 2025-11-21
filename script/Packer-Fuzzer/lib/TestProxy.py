# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import requests,sys
from .common.utils import Utils
from .common.cmdline import CommandLines

def testProxy(options,show):
    """
    测试代理连接并获取代理IP地址

    参数:
        options: 命令行选项对象，包含proxy和silent属性
        show: 控制是否显示输出的标志位，1表示显示，其他值表示不显示

    返回值:
        str: 代理服务器的IP地址，如果测试失败则返回默认值"127.0.0.1"
    """
    try:
        # 使用ipify服务获取公网IP地址
        # url = "http://ifconfig.me/ip" 这节点居然不能用了...
        # url = "https://api.my-ip.io/ip" 备用一个 Backup
        url = "http://api.ipify.org/?format=txt"

        # 构造代理配置字典，同时设置HTTP和HTTPS代理
        proxy_data = {
            'http': options.proxy,
            'https': options.proxy,
        }

        # 初始化默认IP地址
        ipAddr = "127.0.0.1"

        # 发送HTTP请求获取代理IP地址
        ipAddr = requests.get(url, proxies=proxy_data, timeout=7, verify=False).text.strip()

        # 根据show参数和静默模式控制是否输出结果
        if show == 1:
            if options.silent == None:
                print("[+] " + Utils().getMyWord("{connect_s}") + ipAddr)
        return ipAddr
    except:
        # 异常处理：保持返回默认IP地址
        if show == 1:
            if options.silent == None:
                pass
        return ipAddr

