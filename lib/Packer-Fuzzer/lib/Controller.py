# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
from lib.ParseJs import ParseJs
from lib.vulnTest import vulnTest
from lib.common.utils import Utils
from lib.getApiText import ApiText
from lib.ApiCollect import Apicollect
from lib.Database import DatabaseType
from lib.FuzzParam import FuzzerParam
from lib.CheckPacker import CheckPacker
from lib.PostApiText import PostApiText
from lib.common.beautyJS import BeautyJs
from lib.Recoverspilt import RecoverSpilt
from lib.CreateReport import CreateReport
from lib.getApiResponse import ApiResponse
from lib.LoadExtensions import loadExtensions
from lib.BehavioralDiffEngine import BehavioralDiffEngine
from lib.ParameterPollutionDetector import ParameterPollutionDetector
from lib.BehavioralApiDiscovery import BehavioralApiDiscovery
from lib.reports.CreatWord import Docx_replace
from lib.common.CreatLog import creatLog,log_name,logs


class Project():

    def __init__(self, url, options):
        self.url = url
        self.codes = {}
        self.options = options

    def parseStart(self):
        projectTag = logs
        if self.options.silent != None:
            print("[TAG]" + projectTag)
        DatabaseType(projectTag).createDatabase()
        ParseJs(projectTag, self.url, self.options).parseJsStart()
        path_log = os.path.abspath(log_name)
        path_db = os.path.abspath(DatabaseType(projectTag).getPathfromDB() + projectTag + ".db")
        # 使用Packer-Fuzzer自带的日志系统
        creatLog().get_logger().info("[!] " + Utils().getMyWord("{db_path}") + path_db)  #显示数据库文件路径
        creatLog().get_logger().info("[!] " + Utils().getMyWord("{log_path}") + path_log) #显示log文件路径
        checkResult = CheckPacker(projectTag, self.url, self.options).checkStart()
        if checkResult == 1 or checkResult == 777: #打包器检测模块
            if checkResult != 777: #确保检测报错也能运行
                creatLog().get_logger().info("[!] " + Utils().getMyWord("{check_pack_s}"))
            RecoverSpilt(projectTag, self.options).recoverStart()
        else:
            creatLog().get_logger().info("[!] " + Utils().getMyWord("{check_pack_f}"))
        Apicollect(projectTag, self.options).apireCoverStart()
        apis = DatabaseType(projectTag).apiPathFromDB()  # 从数据库中提取出来的api
        self.codes = ApiResponse(apis,self.options).run()
        DatabaseType(projectTag).insertResultFrom(self.codes)
        if self.options.sendtype == "GET" or self.options.sendtype == "get":
            allPaths = DatabaseType(projectTag).allPathFromDB()
            getTexts = ApiText(allPaths,self.options).run()    # 对get请求进行一个获取返回包
            DatabaseType(projectTag).updatePathsMethod(1)
            DatabaseType(projectTag).insertTextFromDB(getTexts)
        elif self.options.sendtype == "POST" or self.options.sendtype == "post":
            allPaths = DatabaseType(projectTag).allPathFromDB()
            postTexts = PostApiText(allPaths,self.options).run()
            DatabaseType(projectTag).updatePathsMethod(2)
            DatabaseType(projectTag).insertTextFromDB(postTexts)
        else:
            getPaths = DatabaseType(projectTag).sucesssPathFromDB()   # 获取get请求的path
            getTexts = ApiText(getPaths,self.options).run()    # 对get请求进行一个获取返回包
            postPaths = DatabaseType(projectTag).wrongMethodFromDB()  # 获取post请求的path
            if len(postPaths) != 0:
                postTexts = PostApiText(postPaths,self.options).run()
                DatabaseType(projectTag).insertTextFromDB(postTexts)
            DatabaseType(projectTag).insertTextFromDB(getTexts)
        if self.options.type == "adv":
            creatLog().get_logger().info("[!] " + Utils().getMyWord("{adv_start}"))
            creatLog().get_logger().info(Utils().tellTime() + Utils().getMyWord("{beauty_js}"))
            BeautyJs(projectTag).rewrite_js()
            creatLog().get_logger().info(Utils().tellTime() + Utils().getMyWord("{fuzzer_param}"))
            FuzzerParam(projectTag).FuzzerCollect()
        creatLog().get_logger().info(Utils().tellTime() + Utils().getMyWord("{response_end}"))
        # 运行行为差异分析
        creatLog().get_logger().info(Utils().tellTime() + "[*] 开始行为差异分析...")
        try:
            bde = BehavioralDiffEngine(self.url, options=self.options)
            # 对一些关键路径进行分析
            key_paths = [
                "/api", "/admin", "/login", "/register", "/upload", 
                "/user", "/users", "/profile", "/settings", "/dashboard",
                "/config", "/admin/config", "/admin/settings", "/admin/users",
                "/api/v1", "/api/v2", "/v1/api", "/v2/api", 
                "/auth", "/authentication", "/oauth", "/sso",
                "/backup", "/backups", "/debug", "/logs", 
                "/test", "/testing", "/dev", "/development"
            ]
            for path in key_paths:
                try:
                    result = bde.send_requests_and_analyze(path)
                    if result['differences'] or result['potential_issues']:
                        creatLog().get_logger().info(f"[!] 在路径 {path} 发现行为差异")
                        for diff in result['differences']:
                            creatLog().get_logger().info(f"  [-] 差异: {diff['description']}")
                        for issue in result['potential_issues']:
                            creatLog().get_logger().info(f"  [-] 潜在问题 ({issue['severity']}): {issue['description']}")
                except Exception as e:
                    creatLog().get_logger().warning(f"[!] 行为差异分析在路径 {path} 出错: {str(e)}")
        except Exception as e:
            creatLog().get_logger().warning(f"[!] 行为差异分析模块初始化失败: {str(e)}")
            
        # 运行参数污染检测
        creatLog().get_logger().info(Utils().tellTime() + "[*] 开始参数污染检测...")
        try:
            ppd = ParameterPollutionDetector(self.url, options=self.options)
            # 对一些关键路径进行参数污染检测
            key_paths = [
                "/api", "/login", "/user", "/profile", "/admin",
                "/api/v1", "/api/v2", "/v1/api", "/v2/api"
            ]
            test_params = {
                "id": "1",
                "user": "test",
                "action": "view"
            }
            
            for path in key_paths:
                try:
                    result = ppd.detect_parameter_pollution(path, test_params)
                    if result['vulnerabilities']:
                        creatLog().get_logger().info(f"[!] 在路径 {path} 发现参数污染漏洞")
                        report = ppd.format_vulnerability_report(result)
                        creatLog().get_logger().info(f"  [-] 检测报告:\n{report}")
                except Exception as e:
                    creatLog().get_logger().warning(f"[!] 参数污染检测在路径 {path} 出错: {str(e)}")
        except Exception as e:
            creatLog().get_logger().warning(f"[!] 参数污染检测模块初始化失败: {str(e)}")
        
        # 运行行为API发现
        creatLog().get_logger().info(Utils().tellTime() + "[*] 开始行为API发现...")
        try:
            # 获取JS文件内容
            js_contents = []
            db_paths = DatabaseType(projectTag).allPathFromDB()
            for path_info in db_paths:
                if path_info[2] and path_info[2].endswith('.js'):
                    js_contents.append(path_info[2])
            
            # 初始化行为API发现模块
            bad = BehavioralApiDiscovery(projectTag, options=self.options)
            discovery_results = bad.discover_hidden_apis(
                js_contents=js_contents,
                request_data=[],  # 在实际应用中这里会填入真实的请求数据
                dom_contents=[]   # 在实际应用中这里会填入真实的DOM内容
            )
            
            # 记录发现的候选API
            if discovery_results['candidates']:
                creatLog().get_logger().info(f"[!] 发现 {len(discovery_results['candidates'])} 个潜在API路径")
                for candidate in discovery_results['candidates'][:10]:  # 只显示前10个
                    creatLog().get_logger().info(f"  [-] 候选路径: {candidate}")
                if len(discovery_results['candidates']) > 10:
                    creatLog().get_logger().info(f"  [-] ... 还有 {len(discovery_results['candidates']) - 10} 个路径")
            
        except Exception as e:
            creatLog().get_logger().warning(f"[!] 行为API发现模块执行失败: {str(e)}")
        
        vulnTest(projectTag,self.options).testStart(self.url)
        if self.options.type == "adv":
            vulnTest(projectTag,self.options).advtestStart(self.options)
        if self.options.ext == "on":
            creatLog().get_logger().info("[+] " + Utils().getMyWord("{ext_start}"))
            loadExtensions(projectTag,self.options).runExt()
            creatLog().get_logger().info("[-] " + Utils().getMyWord("{ext_end}"))
        vuln_num = Docx_replace(projectTag).vuln_judge()
        co_vuln_num = vuln_num[1] + vuln_num[2] + vuln_num[3]
        creatLog().get_logger().info("[!] " + Utils().getMyWord("{co_discovery}") + str(co_vuln_num) + Utils().getMyWord("{effective_vuln}") + ": " + Utils().getMyWord("{r_l_h}") + str(vuln_num[1]) + Utils().getMyWord("{ge}") + ", " + Utils().getMyWord("{r_l_m}") + str(vuln_num[2]) + Utils().getMyWord("{ge}") + ", " + Utils().getMyWord("{r_l_l}") + str(vuln_num[3]) + Utils().getMyWord("{ge}"))
        CreateReport(projectTag).create_repoter()
        creatLog().get_logger().info("[-] " + Utils().getMyWord("{all_end}"))