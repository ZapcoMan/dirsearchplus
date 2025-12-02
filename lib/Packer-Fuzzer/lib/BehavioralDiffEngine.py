#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Behavioral Difference Engine Module
==================================

核心功能：对同一路径，构造同语义不同编码、同语义不同顺序、伪随机扰动的N份请求，
自动检测服务端响应的行为差异，发现：
* WAF 缺陷
* 参数解析差异
* URL router 在不同编码下的行为偏差
* 框架处理链漏洞（Spring / Flask / Django）

"""

import urllib.parse
import random
import string
import copy
import base64
import codecs
from typing import List, Dict, Any, Tuple
import requests
import urllib3
from .common.CreatLog import creatLog


class BehavioralDiffEngine:
    """
    行为差异引擎，用于检测服务端在不同请求形式下的响应差异
    """

    def __init__(self, base_url: str, headers: Dict[str, str] = None, options=None):
        """
        初始化行为差异引擎
        
        Args:
            base_url: 目标基础URL
            headers: HTTP请求头
            options: 配置选项对象
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.options = options
        self.log = creatLog().get_logger()
        # 创建一个默认的options对象以防传入None
        class DefaultOptions:
            def __init__(self):
                self.proxy = None
                self.ssl_flag = "0"
                self.cookie = None
                self.head = "Cache-Control:no-cache"
                
        if self.options is None:
            self.options = DefaultOptions()
            
        # 初始化UserAgent列表
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
        
    def generate_encoding_variants(self, path: str, params: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成路径和参数的不同编码变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        variants = []
        params = params or {}
        variants.append((path, copy.deepcopy(params)))  # 原始路径和参数
        
        # URL编码变体
        encoded_path = urllib.parse.quote(path, safe='/')
        variants.append((encoded_path, copy.deepcopy(params)))
        
        # 双重URL编码
        double_encoded = urllib.parse.quote(encoded_path, safe='/')
        variants.append((double_encoded, copy.deepcopy(params)))
        
        # Unicode编码变体
        try:
            unicode_path = path.encode('unicode_escape').decode('utf-8')
            variants.append((unicode_path, copy.deepcopy(params)))
        except:
            pass
        
        # Base64编码路径（作为参数）
        try:
            b64_path = base64.b64encode(path.encode('utf-8')).decode('utf-8')
            b64_params = copy.deepcopy(params)
            b64_params['path_b64'] = b64_path
            variants.append((path, b64_params))
        except:
            pass
        
        # 路径规范化变体
        if '../' not in path:  # 避免破坏已有的路径遍历
            normalized = './' + path.lstrip('/')
            variants.append((normalized, copy.deepcopy(params)))
            
        # 添加随机路径分隔符变化（如果适用）
        if '/' in path:
            backslash_variant = path.replace('/', '\\')
            variants.append((backslash_variant, copy.deepcopy(params)))
            
        # 参数编码变体
        if params:
            # URL编码参数值
            encoded_params = {}
            for k, v in params.items():
                encoded_params[urllib.parse.quote(str(k))] = urllib.parse.quote(str(v))
            variants.append((path, copy.deepcopy(encoded_params)))
            
            # Unicode编码参数
            try:
                unicode_params = {}
                for k, v in params.items():
                    unicode_params[k.encode('unicode_escape').decode('utf-8')] = str(v).encode('unicode_escape').decode('utf-8')
                variants.append((path, copy.deepcopy(unicode_params)))
            except:
                pass
                
            # Base64编码参数值
            try:
                b64_params = {}
                for k, v in params.items():
                    b64_params[k] = base64.b64encode(str(v).encode('utf-8')).decode('utf-8')
                variants.append((path, copy.deepcopy(b64_params)))
            except:
                pass
                
        return variants
        
    def generate_parameter_variants(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成参数的不同排列变体
        
        Args:
            params: 原始参数字典
            
        Returns:
            List[Dict[str, Any]]: 不同参数顺序的列表
        """
        if not params:
            return [{}]
            
        variants = []
        variants.append(copy.deepcopy(params))  # 原始参数
        
        # 参数顺序变化
        keys = list(params.keys())
        for _ in range(min(5, len(keys) * 2)):  # 生成最多5个变体
            shuffled_keys = keys[:]
            random.shuffle(shuffled_keys)
            variant = {k: params[k] for k in shuffled_keys}
            variants.append(copy.deepcopy(variant))
            
        # 添加随机参数干扰
        for _ in range(3):
            variant = copy.deepcopy(params)
            # 添加随机参数
            rand_key = ''.join(random.choices(string.ascii_lowercase, k=5))
            rand_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            variant[rand_key] = rand_value
            variants.append(copy.deepcopy(variant))
            
        # HTTP参数污染 - 重复参数
        if params:
            for _ in range(3):
                variant = copy.deepcopy(params)
                # 随机选择一个参数进行重复
                chosen_key = random.choice(list(params.keys()))
                variant[chosen_key + "_copy"] = variant[chosen_key]  # 添加副本
                variants.append(copy.deepcopy(variant))
                
        # 大小写混合参数名
        if params:
            variant = {}
            for k, v in params.items():
                # 随机大小写变化
                mixed_case_key = ''.join(random.choice([c.upper(), c.lower()]) for c in k)
                variant[mixed_case_key] = v
            variants.append(copy.deepcopy(variant))
            
        return variants
        
    def generate_pseudo_random_disturbances(self, path: str, params: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成伪随机扰动变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        disturbances = []
        params = params or {}
        
        # 路径扰动
        for _ in range(5):
            # 在路径中添加随机查询参数
            rand_param = ''.join(random.choices(string.ascii_lowercase, k=3))
            rand_value = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            
            disturbed_path = path + ('&' if '?' in path else '?') + f"{rand_param}={rand_value}"
            disturbances.append((disturbed_path, copy.deepcopy(params)))
            
        # 参数扰动
        for _ in range(5):
            disturbed_params = copy.deepcopy(params)
            if disturbed_params:
                # 随机修改一个参数值
                rand_key = random.choice(list(disturbed_params.keys()))
                rand_suffix = ''.join(random.choices(string.ascii_letters, k=3))
                disturbed_params[rand_key] = str(disturbed_params[rand_key]) + rand_suffix
                disturbances.append((path, copy.deepcopy(disturbed_params)))
            else:
                # 如果没有参数，添加一个随机参数
                rand_key = ''.join(random.choices(string.ascii_lowercase, k=4))
                rand_value = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                disturbed_params[rand_key] = rand_value
                disturbances.append((path, copy.deepcopy(disturbed_params)))
                
        return disturbances
        
    def generate_http_method_variants(self, path: str) -> List[str]:
        """
        生成不同HTTP方法变体
        
        Args:
            path: 原始路径
            
        Returns:
            List[str]: 不同HTTP方法列表
        """
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]
        return methods
        
    def generate_header_variants(self) -> List[Dict[str, str]]:
        """
        生成不同的HTTP头变体
        
        Returns:
            List[Dict[str, str]]: 不同HTTP头配置列表
        """
        variants = []
        
        # 原始头
        variants.append(copy.deepcopy(self.headers or {}))
        
        # User-Agent变体
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "curl/7.64.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "python-requests/2.25.1"
        ]
        
        for ua in user_agents:
            variant = copy.deepcopy(self.headers or {})
            variant["User-Agent"] = ua
            variants.append(copy.deepcopy(variant))
            
        # Content-Type变体
        content_types = [
            "application/json",
            "application/xml",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain"
        ]
        
        for ct in content_types:
            variant = copy.deepcopy(self.headers or {})
            variant["Content-Type"] = ct
            variants.append(copy.deepcopy(variant))
            
        # 大小写变体
        if self.headers:
            variant = {}
            for k, v in self.headers.items():
                # 随机大小写变化
                mixed_case_key = ''.join(random.choice([c.upper(), c.lower()]) for c in k)
                variant[mixed_case_key] = v
            variants.append(copy.deepcopy(variant))
            
        return variants
        
    def generate_cookie_variants(self) -> List[str]:
        """
        生成不同的Cookie变体
        
        Returns:
            List[str]: 不同Cookie值列表
        """
        variants = []
        
        # 原始Cookie
        if hasattr(self.options, 'cookie') and self.options.cookie:
            variants.append(self.options.cookie)
        else:
            variants.append("")
            
        # 空Cookie
        variants.append("")
        
        # 随机Cookie
        rand_key = ''.join(random.choices(string.ascii_lowercase, k=5))
        rand_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        variants.append(f"{rand_key}={rand_value}")
        
        # 多个Cookie
        cookie_pairs = []
        for _ in range(3):
            key = ''.join(random.choices(string.ascii_lowercase, k=4))
            value = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            cookie_pairs.append(f"{key}={value}")
        variants.append("; ".join(cookie_pairs))
        
        return variants
        
    def generate_path_traversal_variants(self, path: str) -> List[str]:
        """
        生成路径遍历变体
        
        Args:
            path: 原始路径
            
        Returns:
            List[str]: 路径遍历变体列表
        """
        variants = [path]
        
        # 基本路径遍历
        if not path.startswith("/"):
            variants.append("../" + path)
            variants.append("..\\\\" + path)
            
        # URL编码路径遍历
        variants.append("%2e%2e%2f" + path.lstrip("/"))
        variants.append("%2e%2e%5c" + path.lstrip("/"))
        
        # Unicode编码路径遍历
        try:
            variants.append("..\\u002f" + path.lstrip("/"))
            variants.append("..\\u005c" + path.lstrip("/"))
        except:
            pass
            
        # 双重编码
        variants.append("%252e%252e%252f" + path.lstrip("/"))
        
        return variants
        
    def generate_multipart_form_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成multipart/form-data变体
        
        Args:
            params: 原始参数
            
        Returns:
            List[Dict[str, Any]]: multipart/form-data变体列表
        """
        if not params:
            return [{}]
            
        variants = [copy.deepcopy(params)]
        
        # 添加boundary变化
        boundary_chars = string.ascii_letters + string.digits
        for _ in range(3):
            boundary = ''.join(random.choices(boundary_chars, k=20))
            # 这里只是示意，实际使用时需要在请求中设置Content-Type头
            variant = copy.deepcopy(params)
            variant['_boundary'] = boundary
            variants.append(copy.deepcopy(variant))
            
        return variants
        
    def send_request(self, url: str, method: str = "GET", headers: Dict = None, params: Dict = None) -> Dict:
        """
        发送单个HTTP请求
        
        Args:
            url: 请求URL
            method: HTTP方法
            headers: 请求头
            params: 请求参数
            
        Returns:
            Dict: 响应数据
        """
        urllib3.disable_warnings()
        headers = headers or {}
        params = params or {}
        
        # 设置默认User-Agent
        if 'User-Agent' not in headers:
            headers['User-Agent'] = random.choice(self.UserAgent)
            
        # 设置默认Content-Type
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
        # 设置默认Accept
        if 'Accept' not in headers:
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            
        # 添加Cookie（如果存在）
        if hasattr(self.options, 'cookie') and self.options.cookie:
            headers['Cookie'] = self.options.cookie
            
        # 处理自定义头部
        if hasattr(self.options, 'head') and self.options.head and ':' in self.options.head:
            try:
                key, value = self.options.head.split(':', 1)
                headers[key.strip()] = value.strip()
            except:
                pass
                
        ssl_flag = int(getattr(self.options, 'ssl_flag', "0"))
        proxy_data = {'http': getattr(self.options, 'proxy', None), 
                      'https': getattr(self.options, 'proxy', None)}
        
        s = requests.Session()
        s.keep_alive = False
        
        try:
            if method.upper() == "GET":
                if ssl_flag == 1:
                    response = s.get(url, headers=headers, params=params, timeout=6, 
                                   proxies=proxy_data, verify=False)
                else:
                    response = s.get(url, headers=headers, params=params, timeout=6, 
                                   proxies=proxy_data)
            elif method.upper() == "POST":
                if ssl_flag == 1:
                    response = s.post(url, headers=headers, data=params, timeout=6, 
                                    proxies=proxy_data, verify=False)
                else:
                    response = s.post(url, headers=headers, data=params, timeout=6, 
                                    proxies=proxy_data)
            elif method.upper() == "PUT":
                if ssl_flag == 1:
                    response = s.put(url, headers=headers, data=params, timeout=6, 
                                   proxies=proxy_data, verify=False)
                else:
                    response = s.put(url, headers=headers, data=params, timeout=6, 
                                   proxies=proxy_data)
            elif method.upper() == "DELETE":
                if ssl_flag == 1:
                    response = s.delete(url, headers=headers, params=params, timeout=6, 
                                      proxies=proxy_data, verify=False)
                else:
                    response = s.delete(url, headers=headers, params=params, timeout=6, 
                                      proxies=proxy_data)
            elif method.upper() == "HEAD":
                if ssl_flag == 1:
                    response = s.head(url, headers=headers, params=params, timeout=6, 
                                    proxies=proxy_data, verify=False)
                else:
                    response = s.head(url, headers=headers, params=params, timeout=6, 
                                    proxies=proxy_data)
            elif method.upper() == "OPTIONS":
                if ssl_flag == 1:
                    response = s.options(url, headers=headers, params=params, timeout=6, 
                                       proxies=proxy_data, verify=False)
                else:
                    response = s.options(url, headers=headers, params=params, timeout=6, 
                                       proxies=proxy_data)
            elif method.upper() == "PATCH":
                if ssl_flag == 1:
                    response = s.patch(url, headers=headers, data=params, timeout=6, 
                                     proxies=proxy_data, verify=False)
                else:
                    response = s.patch(url, headers=headers, data=params, timeout=6, 
                                     proxies=proxy_data)
            else:
                # 默认使用GET
                if ssl_flag == 1:
                    response = s.get(url, headers=headers, params=params, timeout=6, 
                                   proxies=proxy_data, verify=False)
                else:
                    response = s.get(url, headers=headers, params=params, timeout=6, 
                                   proxies=proxy_data)
                    
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'content_length': len(response.text),
                'url': url,
                'method': method
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'url': url,
                'method': method
            }
        
    def send_requests_and_analyze(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送多种变体请求并分析响应差异
        
        Args:
            path: 请求路径
            params: 请求参数
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        results = {
            'path': path,
            'responses': [],
            'differences': [],
            'potential_issues': []
        }
        
        params = params or {}
        
        # 生成所有变体
        encoding_variants = self.generate_encoding_variants(path, params)
        param_variants = self.generate_parameter_variants(params)
        disturbance_variants = self.generate_pseudo_random_disturbances(path, params)
        method_variants = self.generate_http_method_variants(path)
        header_variants = self.generate_header_variants()
        cookie_variants = self.generate_cookie_variants()
        traversal_variants = self.generate_path_traversal_variants(path)
        multipart_variants = self.generate_multipart_form_data(params)
        
        # 收集所有请求变体
        requests_to_send = []
        
        # 路径和参数编码变体
        requests_to_send.extend(encoding_variants)
        
        # 参数顺序变体
        for param_variant in param_variants:
            requests_to_send.append((path, copy.deepcopy(param_variant)))
            
        # 扰动变体
        requests_to_send.extend(disturbance_variants)
        
        # 方法变体（只选取一部分避免过多请求）
        for method in method_variants[:3]:  # 限制方法数量
            requests_to_send.append((path, copy.deepcopy(params), method))
            
        # 头部变体（只选取一部分）
        for header_variant in header_variants[:3]:
            requests_to_send.append((path, copy.deepcopy(params), "GET", copy.deepcopy(header_variant)))
            
        # Cookie变体
        for cookie_variant in cookie_variants[:2]:
            header_with_cookie = copy.deepcopy(self.headers or {})
            if cookie_variant:
                header_with_cookie['Cookie'] = cookie_variant
            requests_to_send.append((path, copy.deepcopy(params), "GET", header_with_cookie))
            
        # 路径遍历变体
        for traversal_path in traversal_variants:
            requests_to_send.append((traversal_path, copy.deepcopy(params)))
            
        # multipart变体
        for multipart_param in multipart_variants:
            requests_to_send.append((path, copy.deepcopy(multipart_param)))
        
        # 发送请求并收集响应
        responses = []
        for request_item in requests_to_send[:30]:  # 限制请求数量避免过多请求
            try:
                if len(request_item) == 2:
                    req_path, req_params = request_item
                    url = self.base_url + req_path
                    response = self.send_request(url, "GET", copy.deepcopy(self.headers), req_params)
                elif len(request_item) == 3:
                    req_path, req_params, method = request_item
                    url = self.base_url + req_path
                    response = self.send_request(url, method, copy.deepcopy(self.headers), req_params)
                elif len(request_item) == 4:
                    req_path, req_params, method, headers = request_item
                    url = self.base_url + req_path
                    response = self.send_request(url, method, headers, req_params)
                else:
                    continue
                    
                responses.append(response)
            except Exception as e:
                url = self.base_url + path
                if len(request_item) >= 1 and isinstance(request_item[0], str):
                    url = self.base_url + request_item[0]
                    
                resp_data = {
                    'url': url,
                    'error': str(e)
                }
                responses.append(resp_data)
                
        results['responses'] = responses
        
        # 分析响应差异
        results['differences'] = self._analyze_response_differences(responses)
        
        # 识别潜在问题
        results['potential_issues'] = self._identify_potential_issues(responses)
        
        return results
        
    def _analyze_response_differences(self, responses: List[Dict]) -> List[Dict]:
        """
        分析响应之间的差异
        
        Args:
            responses: 响应列表
            
        Returns:
            List[Dict]: 差异分析结果
        """
        differences = []
        
        if len(responses) < 2:
            return differences
            
        # 提取有效的响应（排除错误）
        valid_responses = [r for r in responses if 'error' not in r]
        
        if len(valid_responses) < 2:
            return differences
            
        # 比较状态码差异
        status_codes = [r.get('status_code', 0) for r in valid_responses]
        unique_status_codes = set(status_codes)
        
        if len(unique_status_codes) > 1:
            differences.append({
                'type': 'status_code',
                'description': f'不同响应变体返回了不同的状态码: {sorted(unique_status_codes)}'
            })
            
        # 比较内容长度差异
        content_lengths = [r.get('content_length', 0) for r in valid_responses]
        if max(content_lengths) - min(content_lengths) > 100:  # 差异超过100字节
            differences.append({
                'type': 'content_length',
                'description': f'响应内容长度存在显著差异，最小: {min(content_lengths)}, 最大: {max(content_lengths)}'
            })
            
        # 比较响应头差异
        header_keys = set()
        for r in valid_responses:
            if 'headers' in r:
                header_keys.update(r['headers'].keys())
            
        for header_key in list(header_keys)[:10]:  # 限制检查的头部数量
            header_values = []
            for r in valid_responses:
                if 'headers' in r and header_key in r['headers']:
                    header_values.append(r['headers'][header_key])
                    
            unique_header_values = set(header_values)
            if len(unique_header_values) > 1:
                differences.append({
                    'type': 'response_header',
                    'description': f'响应头 "{header_key}" 在不同变体中有不同值: {list(unique_header_values)[:3]}'  # 限制显示数量
                })
                
        return differences
        
    def _identify_potential_issues(self, responses: List[Dict]) -> List[Dict]:
        """
        识别潜在的安全问题
        
        Args:
            responses: 响应列表
            
        Returns:
            List[Dict]: 潜在问题列表
        """
        issues = []
        
        # WAF绕过检测 - 查找某些变体可以绕过WAF的情况
        valid_responses = [r for r in responses if 'error' not in r]
        
        waf_indicators = ['waf', 'firewall', 'blocked', 'forbidden', 'access denied']
        blocked_responses = []
        allowed_responses = []
        
        for r in valid_responses:
            content_lower = r.get('content', '').lower()
            is_blocked = any(indicator in content_lower for indicator in waf_indicators)
            # 检查状态码是否表示被阻止
            status_code_blocked = r.get('status_code') in [403, 406, 429]
            
            if is_blocked or status_code_blocked:
                blocked_responses.append(r)
            else:
                allowed_responses.append(r)
                
        if blocked_responses and allowed_responses:
            issues.append({
                'type': 'waf_bypass',
                'severity': 'high',
                'description': f'检测到可能的WAF绕过: {len(blocked_responses)}个变体被阻止, {len(allowed_responses)}个变体被允许'
            })
            
        # 参数解析差异
        if len(responses) > 1:
            issues.append({
                'type': 'param_parsing',
                'severity': 'medium',
                'description': '多个请求变体已发送，可用于检测参数解析差异'
            })
            
        # 检查是否有错误响应
        error_responses = [r for r in responses if 'error' in r]
        if error_responses:
            issues.append({
                'type': 'request_error',
                'severity': 'low',
                'description': f'{len(error_responses)}个请求在发送过程中出现错误'
            })
            
        return issues