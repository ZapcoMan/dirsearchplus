#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parameter Pollution Detector Module
==================================

核心功能：检测HTTP参数污染漏洞，包括：
* URL参数重复key行为差异
* JSON重复字段行为差异  
* 表单key重复行为差异
* 数组展开解析差异
* Spring MVC参数绑定漏洞

输出示例：
同样 `/api/user?id=1&id=2`，不同框架差异巨大，可触发越权。
"""

import urllib.parse
import random
import string
import copy
import json
from typing import List, Dict, Any, Tuple
import requests
import urllib3
from .common.CreatLog import creatLog


class ParameterPollutionDetector:
    """
    参数污染检测器，用于检测因参数处理不当引起的安全问题
    """

    def __init__(self, base_url: str, headers: Dict[str, str] = None, options=None):
        """
        初始化参数污染检测器
        
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
        self.UserAgent = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]

    def generate_url_parameter_pollution_variants(self, path: str, params: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成URL参数重复key行为检测变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        variants = []
        params = params or {}
        
        if not params:
            return [(path, params)]
            
        # 原始参数
        variants.append((path, copy.deepcopy(params)))
        
        # 创建具有重复key的参数变体
        for key, value in params.items():
            # 构造带有重复参数的URL
            query_params = copy.deepcopy(params)
            # 添加重复的参数key（在实际HTTP请求中这会产生重复的key）
            # 我们在这里保留原始参数，并在发送请求时特殊处理重复参数
            
            # 方式1: 直接重复参数
            polluted_params = copy.deepcopy(query_params)
            # 标记这是一个需要特殊处理的重复参数变体
            polluted_params[f"_hpp_repeat_{key}"] = str(value) + "_repeat"
            variants.append((path, polluted_params))
            
        return variants

    def generate_json_field_collision_variants(self, path: str, params: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成JSON重复字段行为检测变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        variants = []
        params = params or {}
        
        if not params:
            return [(path, params)]
            
        # 原始参数
        variants.append((path, copy.deepcopy(params)))
        
        # 创建JSON重复字段变体
        for key, value in params.items():
            # 构造JSON格式参数，包含重复字段
            json_payload = {}
            for k, v in params.items():
                json_payload[k] = v
                
            # 添加重复字段（使用相同键名）
            json_payload[key] = f"{value}_duplicate"
            
            # 将JSON作为参数发送
            json_params = {
                "json_data": json.dumps(json_payload),
                key: value  # 同时保留原始参数
            }
            variants.append((path, json_params))
            
        return variants

    def generate_form_key_collision_variants(self, path: str, params: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成表单key重复行为检测变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        variants = []
        params = params or {}
        
        if not params:
            return [(path, params)]
            
        # 原始参数
        variants.append((path, copy.deepcopy(params)))
        
        # 创建表单重复key变体
        for key, value in params.items():
            # 构造具有重复表单key的参数
            form_params = copy.deepcopy(params)
            
            # 添加重复的表单key（标记为需要特殊处理）
            form_params[f"_form_repeat_{key}"] = f"{value}_form_repeat"
            variants.append((path, form_params))
            
        return variants

    def generate_array_expansion_variants(self, path: str, params: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成数组展开解析差异检测变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        variants = []
        params = params or {}
        
        if not params:
            return [(path, params)]
            
        # 原始参数
        variants.append((path, copy.deepcopy(params)))
        
        # 创建不同数组格式的变体
        for key, value in params.items():
            # [] 格式
            array_bracket_params = copy.deepcopy(params)
            array_bracket_params[f"{key}[]"] = [value, f"{value}_arr1", f"{value}_arr2"]
            variants.append((path, array_bracket_params))
            
            # 重复key格式
            array_repeat_params = copy.deepcopy(params)
            # 标记为需要特殊处理的重复key
            array_repeat_params[f"_array_repeat_{key}"] = [value, f"{value}_rep1", f"{value}_rep2"]
            variants.append((path, array_repeat_params))
            
            # 索引格式
            array_index_params = copy.deepcopy(params)
            array_index_params[f"{key}[0]"] = value
            array_index_params[f"{key}[1]"] = f"{value}_idx1"
            array_index_params[f"{key}[2]"] = f"{value}_idx2"
            variants.append((path, array_index_params))
            
        return variants

    def generate_spring_mvc_binding_variants(self, path: str, params: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成Spring MVC参数绑定漏洞检测变体
        
        Args:
            path: 原始路径
            params: 原始参数
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: (路径, 参数) 元组列表
        """
        variants = []
        params = params or {}
        
        if not params:
            return [(path, params)]
            
        # 原始参数
        variants.append((path, copy.deepcopy(params)))
        
        # 创建Spring MVC对象绑定变体
        for key, value in params.items():
            # 点(.)表示法访问对象属性
            nested_params_dot = copy.deepcopy(params)
            nested_params_dot[f"{key}.property"] = f"{value}_nested_property"
            variants.append((path, nested_params_dot))
            
            # 下划线(_)表示法
            nested_params_underscore = copy.deepcopy(params)
            nested_params_underscore[f"{key}_property"] = f"{value}_nested_property"
            variants.append((path, nested_params_underscore))
            
            # 数组/列表访问
            list_params = copy.deepcopy(params)
            list_params[f"{key}[0]"] = value
            list_params[f"{key}[1]"] = f"{value}_list_item"
            variants.append((path, list_params))
            
        return variants

    def send_request(self, url: str, method: str = "GET", headers: Dict = None, params: Dict = None) -> Dict:
        """
        发送单个HTTP请求（增强版，支持参数污染特殊处理）
        
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
        original_params = params or {}
        
        # 处理特殊的参数污染标记
        processed_params = {}
        repeat_params = {}  # 存储需要重复的参数
        
        for key, value in original_params.items():
            if key.startswith("_hpp_repeat_"):
                # 处理URL参数重复key
                original_key = key[len("_hpp_repeat_"):]
                processed_params[original_key] = original_params.get(original_key, "")
                repeat_params[original_key] = value
            elif key.startswith("_form_repeat_"):
                # 处理表单重复key
                original_key = key[len("_form_repeat_"):]
                processed_params[original_key] = original_params.get(original_key, "")
                repeat_params[original_key] = value
            elif key.startswith("_array_repeat_"):
                # 处理数组重复key
                original_key = key[len("_array_repeat_"):]
                processed_params[original_key] = original_params.get(original_key, "")
                repeat_params[original_key] = value
            else:
                processed_params[key] = value
        
        # 设置默认User-Agent
        if 'User-Agent' not in headers:
            headers['User-Agent'] = random.choice(self.UserAgent)
            
        # 设置默认Content-Type
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
        # 设置默认Accept
        if 'Accept' not in headers:
            headers['Accept'] = 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            
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
            # 特殊处理GET请求中的重复参数
            if method.upper() == "GET":
                # 构造带有重复参数的URL
                if repeat_params:
                    # 手动构建查询字符串以支持重复参数
                    query_parts = []
                    for key, value in processed_params.items():
                        if isinstance(value, list):
                            for item in value:
                                query_parts.append(f"{urllib.parse.quote(str(key))}={urllib.parse.quote(str(item))}")
                        else:
                            query_parts.append(f"{urllib.parse.quote(str(key))}={urllib.parse.quote(str(value))}")
                            
                    # 添加重复参数
                    for key, value in repeat_params.items():
                        query_parts.append(f"{urllib.parse.quote(str(key))}={urllib.parse.quote(str(value))}")
                    
                    query_string = "&".join(query_parts)
                    if "?" in url:
                        full_url = f"{url}&{query_string}"
                    else:
                        full_url = f"{url}?{query_string}"
                else:
                    full_url = url
                    
                if ssl_flag == 1:
                    response = s.get(full_url, headers=headers, timeout=6, 
                                   proxies=proxy_data, verify=False)
                else:
                    response = s.get(full_url, headers=headers, timeout=6, 
                                   proxies=proxy_data)
                                   
            elif method.upper() == "POST":
                # POST请求中处理重复参数
                data_to_send = processed_params.copy()
                # 对于POST请求，重复参数会在requests内部正确处理
                
                if ssl_flag == 1:
                    response = s.post(url, headers=headers, data=data_to_send, timeout=6, 
                                    proxies=proxy_data, verify=False)
                else:
                    response = s.post(url, headers=headers, data=data_to_send, timeout=6, 
                                    proxies=proxy_data)
            else:
                # 其他方法使用默认处理
                if ssl_flag == 1:
                    response = s.get(url, headers=headers, params=processed_params, timeout=6, 
                                   proxies=proxy_data, verify=False)
                else:
                    response = s.get(url, headers=headers, params=processed_params, timeout=6, 
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

    def detect_parameter_pollution(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行完整的参数污染检测
        
        Args:
            path: 请求路径
            params: 请求参数
            
        Returns:
            Dict[str, Any]: 检测结果
        """
        results = {
            'path': path,
            'vulnerabilities': [],
            'responses': [],
            'details': []
        }
        
        params = params or {}
        
        # 生成所有类型的参数污染变体
        all_variants = []
        
        # 1. URL参数重复key行为检测
        url_variants = self.generate_url_parameter_pollution_variants(path, params)
        all_variants.extend([("url_pollution", v) for v in url_variants])
        
        # 2. JSON重复字段行为检测
        json_variants = self.generate_json_field_collision_variants(path, params)
        all_variants.extend([("json_collision", v) for v in json_variants])
        
        # 3. 表单key重复行为检测
        form_variants = self.generate_form_key_collision_variants(path, params)
        all_variants.extend([("form_collision", v) for v in form_variants])
        
        # 4. 数组展开解析差异检测
        array_variants = self.generate_array_expansion_variants(path, params)
        all_variants.extend([("array_expansion", v) for v in array_variants])
        
        # 5. Spring MVC参数绑定漏洞检测
        spring_variants = self.generate_spring_mvc_binding_variants(path, params)
        all_variants.extend([("spring_binding", v) for v in spring_variants])
        
        # 发送所有变体请求
        responses = []
        for test_type, (test_path, test_params) in all_variants:
            try:
                url = self.base_url + test_path
                response = self.send_request(url, "GET", copy.deepcopy(self.headers), test_params)
                response['test_type'] = test_type
                response['params'] = test_params
                responses.append(response)
            except Exception as e:
                error_resp = {
                    'error': str(e),
                    'test_type': test_type,
                    'params': test_params
                }
                responses.append(error_resp)
                
        results['responses'] = responses
        
        # 分析响应差异以识别潜在漏洞
        valid_responses = [r for r in responses if 'error' not in r]
        
        if len(valid_responses) > 1:
            # 按测试类型分组响应
            grouped_responses = {}
            for resp in valid_responses:
                test_type = resp.get('test_type', 'unknown')
                if test_type not in grouped_responses:
                    grouped_responses[test_type] = []
                grouped_responses[test_type].append(resp)
            
            # 分析每种测试类型的响应差异
            for test_type, type_responses in grouped_responses.items():
                if len(type_responses) > 1:
                    # 比较状态码
                    status_codes = [r.get('status_code', 0) for r in type_responses]
                    unique_status_codes = set(status_codes)
                    
                    if len(unique_status_codes) > 1:
                        results['vulnerabilities'].append({
                            'type': 'status_code_difference',
                            'test_type': test_type,
                            'severity': 'high',
                            'description': f'在{test_type}测试中发现状态码差异: {sorted(unique_status_codes)}'
                        })
                    
                    # 比较内容长度
                    content_lengths = [r.get('content_length', 0) for r in type_responses]
                    length_diff = max(content_lengths) - min(content_lengths)
                    if length_diff > 100:  # 差异超过100字节
                        results['vulnerabilities'].append({
                            'type': 'content_length_difference',
                            'test_type': test_type,
                            'severity': 'medium',
                            'description': f'在{test_type}测试中发现内容长度显著差异: {min(content_lengths)} -> {max(content_lengths)}'
                        })
                        
                    # 检查是否可能存在越权等安全问题
                    privileged_indicators = ['admin', 'root', 'password', 'secret', 'token']
                    for resp in type_responses:
                        content = resp.get('content', '').lower()
                        if any(indicator in content for indicator in privileged_indicators):
                            results['vulnerabilities'].append({
                                'type': 'privilege_disclosure',
                                'test_type': test_type,
                                'severity': 'high',
                                'description': f'在{test_type}测试中发现可能的特权信息泄露'
                            })
                            break
        
        # 添加详细的测试信息
        results['details'] = {
            'total_tests': len(all_variants),
            'successful_requests': len(valid_responses),
            'error_requests': len(responses) - len(valid_responses)
        }
        
        return results

    def format_vulnerability_report(self, detection_result: Dict[str, Any]) -> str:
        """
        格式化漏洞检测报告
        
        Args:
            detection_result: 检测结果
            
        Returns:
            str: 格式化的报告
        """
        if not detection_result.get('vulnerabilities'):
            return f"路径 {detection_result.get('path', '')} 未发现参数污染漏洞。"
            
        # 统计漏洞信息
        high_risk_count = sum(1 for v in detection_result.get('vulnerabilities', []) if v.get('severity') == 'high')
        medium_risk_count = sum(1 for v in detection_result.get('vulnerabilities', []) if v.get('severity') == 'medium')
        
        report = f"路径 {detection_result.get('path', '')}: 发现 {high_risk_count} 个高风险漏洞, {medium_risk_count} 个中风险漏洞"
        
        return report
