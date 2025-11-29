# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import optparse,sys


class CommandLines():
    """
    命令行参数解析类，用于定义和解析程序运行时所需的命令行选项。

    方法:
        cmd(): 定义并解析命令行参数，返回解析后的选项对象。
               如果未提供URL参数，则打印帮助信息并退出程序。
    """

    def cmd(self):
        # 创建一个OptionParser实例，用于处理命令行参数
        parse = optparse.OptionParser()

        # 添加各种命令行选项
        parse.add_option('-u', '--url', dest='url', help='请输入目标站点')
        parse.add_option('-c', '--cookie', dest='cookie', help='请输入站点Cookies')
        parse.add_option('-d', '--head', dest='head', default='Cache-Control:no-cache', help='请输入额外的HTTP头')
        parse.add_option('-l', '--lang', dest='language', help='请选择语言')
        parse.add_option('-t', '--type', dest='type', default='simple', help='请选择扫描模式')
        parse.add_option('-p', '--proxy', dest='proxy', type=str, help='请输入您自己的代理地址')
        parse.add_option('-j', '--js', dest='js', type=str, help='额外的JS文件')
        parse.add_option('-b', '--base', dest='baseurl', type=str, help='请输入基础URL')
        parse.add_option('-r', '--report', dest='report', default='html,doc', type=str, help='选择您的报告类型')
        parse.add_option('-e', '--ext', dest='ext', default='off', type=str, help='启用扩展')
        parse.add_option('-f', '--flag', dest='ssl_flag', default='0', type=str, help='SSL安全标志')
        parse.add_option('-s', '--silent', dest='silent', type=str, help='静默模式（自定义报告名称）')
        parse.add_option('--st', '--sendtype', dest='sendtype', type=str, help='HTTP请求类型POST或GET')
        parse.add_option('--ct', '--contenttype', dest='contenttype', type=str, help='HTTP请求头Content-Type')
        parse.add_option('--pd', '--postdata', dest='postdata', type=str, help='HTTP请求PostData（扫描时）')
        parse.add_option('--ah', '--apihost', dest='apihost', type=str, help='API主机如：https://pocsir.com:777/')
        parse.add_option('--fe', '--fileext', dest='filenameextension', type=str, help='API文件扩展名如：.json')

        # 解析命令行参数
        (options, args) = parse.parse_args()

        # 检查是否提供了目标URL，如果没有则输出帮助信息并退出
        if options.url == None:
            parse.print_help()
            sys.exit(0)

        # 返回解析后的选项对象
        return options


if __name__ == '__main__':
    # 实例化CommandLines类，并调用cmd方法获取cookie参数进行打印
    print(CommandLines().cmd().cookie)
