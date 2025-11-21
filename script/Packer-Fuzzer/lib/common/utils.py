# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os,random,locale,time,shutil
from lib.common import readConfig
from lib.common.cmdline import CommandLines


class Utils():
    """
    工具类，提供各种常用功能的封装
    """

    def creatTag(self, num):
        """
        生成指定长度的随机字符串（由字母和数字组成）

        :param num: 随机字符串的长度
        :return: 生成的随机字符串
        """
        H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(num):
            salt += random.choice(H)
        return salt

    def getFilename(self, url):
        """
        从URL中提取文件名

        :param url: 完整的URL地址
        :return: 提取到的文件名
        """
        filename = url.split('/')[-1]
        filename = filename.split('?')[0]
        return filename

    def creatSometing(self, choice, path):
        """
        根据选择创建文件夹或文件路径

        :param choice: 选择类型，1表示创建文件夹，2表示创建文件路径
        :param path: 要创建的路径（使用'/'分隔符）
        :return: 0表示已存在，1表示创建成功，2表示创建失败
        """
        # choice1文件夹，2文件
        if choice == 1:
            path = path.split('/')  # 输入统一用 /
            path = os.sep.join(path)
            path = os.getcwd() + os.sep + path
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
                    return 1
            except:
                return 2
            return 0
        if choice == 2:
            path = path.split('/')
            del path[-1]
            path = os.sep.join(path)    #
            path = os.getcwd() + os.sep + path
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
                    return 1
            except:
                return 2
            return 0

    def getMiddleStr(self, content, startStr, endStr):
        """
        从文本内容中提取两个指定字符串之间的子字符串

        :param content: 原始文本内容
        :param startStr: 开始标识字符串
        :param endStr: 结束标识字符串
        :return: 提取到的中间字符串
        """
        # 获取中间字符串通用函数
        startIndex = content.index(startStr)
        if startIndex >= 0:
            startIndex += len(startStr)
        endIndex = content.index(endStr)
        return content[startIndex:endIndex]

    def getMyWord(self, someWord):
        """
        根据系统语言环境获取对应的本地化文本

        :param someWord: 需要本地化的关键词
        :return: 对应语言的文本内容
        """
        lang = CommandLines().cmd().language
        if lang:
            localLang = lang
        else:
            try:
                localLang = locale.getdefaultlocale()[0][0:2]
            except:
                localLang = 'en' #默认英语
        try:
            myWord = readConfig.ReadConfig().getLang(localLang,someWord)[0]
        except:
            myWord = readConfig.ReadConfig().getLang('en',someWord)[0] #默认英语
        return myWord

    def tellTime(self):
        """
        获取当前时间并格式化为[HH:MM:SS]格式

        :return: 格式化后的时间字符串
        """
        #时间输出
        localtime = "[" + str(time.strftime('%H:%M:%S',time.localtime(time.time()))) + "] "
        return localtime

    def getMD5(self,file_path):
        """
        计算文件的MD5值

        :param file_path: 文件路径
        :return: 文件的MD5哈希值
        """
        files_md5 = os.popen('md5 %s' % file_path).read().strip()
        file_md5 = files_md5.replace('MD5 (%s) = ' % file_path, '')
        return file_md5

    def copyPath(self,path,out):
        """
        复制目录及其内容到目标位置，只复制不同的文件

        :param path: 源目录路径
        :param out: 目标目录路径
        """
        out = out + os.sep + path.split(os.sep)[-1]
        os.mkdir(out)
        for files in os.listdir(path):
            name = os.path.join(path, files)
            back_name = os.path.join(out, files)
            if os.path.isfile(name):
                # 如果源文件和目标文件都存在且MD5不同则复制
                if os.path.isfile(back_name):
                    if self.getMD5(name) != self.getMD5(back_name):
                        shutil.copy(name,back_name)
                else:
                    shutil.copy(name, back_name)
            else:
                # 递归处理子目录
                if not os.path.isdir(back_name):
                    os.makedirs(back_name)
                self.main(name, back_name)
