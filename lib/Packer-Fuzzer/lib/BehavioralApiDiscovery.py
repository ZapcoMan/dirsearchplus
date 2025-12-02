#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Behavioral API Discovery Module
==============================

基于行为推断的动态API枚举模块，通过分析前端JS、请求链路和按钮事件，
使用BFS算法推导出隐藏API接口，替代传统字典扫描方式。

Features:
- JavaScript代码分析，提取API端点模式
- 请求链路行为分析
- DOM事件与API关联推断
- BFS算法生成候选API路径
- 智能API结构推测
"""

import re
import json
import urllib.parse
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Any
from .common.CreatLog import creatLog


class BehavioralApiDiscovery:
    """
    基于行为推断的动态API发现类
    """

    def __init__(self, project_tag: str, options=None):
        """
        初始化行为API发现模块
        
        Args:
            project_tag: 项目标识符
            options: 配置选项对象
        """
        self.project_tag = project_tag
        self.options = options
        self.log = creatLog().get_logger()
        
        # API路径组件集合
        self.api_components = set()
        self.api_prefixes = set()
        self.api_suffixes = set()
        self.http_methods = set(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        
        # 已发现的API端点
        self.discovered_apis = set()
        
        # 创建一个默认的options对象以防传入None
        class DefaultOptions:
            def __init__(self):
                self.proxy = None
                self.ssl_flag = "0"
                self.cookie = None
                self.head = "Cache-Control:no-cache"
                
        if self.options is None:
            self.options = DefaultOptions()

    def extract_from_js(self, js_content: str) -> Dict[str, Any]:
        """
        从JavaScript代码中提取API相关信息
        
        Args:
            js_content: JavaScript代码内容
            
        Returns:
            Dict[str, Any]: 提取的结果
        """
        self.log.info("[BehavioralAPI] 开始从JavaScript代码中提取API信息")
        
        results = {
            'urls': set(),
            'components': set(),
            'methods': set(),
            'patterns': []
        }
        
        # 常见的API URL模式
        url_patterns = [
            r'["\'](/api/[^"\']+)["\']',
            r'["\'](/v\d+/[^"\']+)["\']',
            r'["\'](/rest/[^"\']+)["\']',
            r'["\'](https?://[^"\']*/api/[^"\']+)["\']',
            r'["\'](https?://[^"\']*/v\d+/[^"\']+)["\']',
            r'url\s*:?\s*["\']([^"\']+)["\']',
            r'endpoint\s*:?\s*["\']([^"\']+)["\']',
            r'path\s*:?\s*["\']([^"\']+)["\']'
        ]
        
        # 提取URL
        for pattern in url_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                results['urls'].add(match)
                
        # 提取HTTP方法
        method_patterns = [
            r'\.get\s*\(', r'\.post\s*\(', r'\.put\s*\(', 
            r'\.delete\s*\(', r'\.patch\s*\(',
            r'method\s*:?\s*["\'](GET|POST|PUT|DELETE|PATCH)["\']',
            r'type\s*:?\s*["\'](GET|POST|PUT|DELETE|PATCH)["\']'
        ]
        
        for pattern in method_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    results['methods'].update([m.upper() for m in match if m])
                else:
                    results['methods'].add(match.upper())
                    
        # 提取URL组件（路径片段）
        for url in results['urls']:
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.strip('/')
            if path:
                components = path.split('/')
                results['components'].update(components)
                if components:
                    results['patterns'].append({
                        'full_path': path,
                        'components': components,
                        'query_params': parsed.query
                    })
                    
        self.log.info(f"[BehavioralAPI] 从JavaScript中提取到 {len(results['urls'])} 个URL和 {len(results['components'])} 个组件")
        return results

    def analyze_request_patterns(self, request_data: List[Dict]) -> Dict[str, Any]:
        """
        分析请求模式数据
        
        Args:
            request_data: 请求数据列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        self.log.info("[BehavioralAPI] 开始分析请求模式")
        
        results = {
            'common_prefixes': set(),
            'common_suffixes': set(),
            'parameter_patterns': set(),
            'method_distribution': defaultdict(int)
        }
        
        # 分析请求路径模式
        paths = []
        for req in request_data:
            url = req.get('url', '')
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.strip('/')
            if path:
                paths.append(path)
                # 统计HTTP方法分布
                method = req.get('method', 'GET').upper()
                results['method_distribution'][method] += 1
                
        # 提取公共前缀和后缀
        if paths:
            # 简单的前缀分析（实际应该更复杂）
            for path in paths:
                components = path.split('/')
                if components:
                    results['common_prefixes'].add(components[0])
                    results['common_suffixes'].add(components[-1])
                    
        self.log.info(f"[BehavioralAPI] 分析完成，发现 {len(results['common_prefixes'])} 个公共前缀")
        return results

    def extract_from_dom_events(self, dom_content: str) -> Dict[str, Any]:
        """
        从DOM事件中提取API相关信息
        
        Args:
            dom_content: DOM内容
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        self.log.info("[BehavioralAPI] 开始从DOM事件中提取API信息")
        
        results = {
            'event_handlers': set(),
            'ajax_calls': set(),
            'form_actions': set()
        }
        
        # 查找事件处理器中的API调用
        event_patterns = [
            r'onclick\s*=\s*["\'][^"\']*[(.]*(ajax|fetch|XMLHttpRequest)[(.]',
            r'onsubmit\s*=\s*["\'][^"\']*[(.]*(ajax|fetch|XMLHttpRequest)[(.]',
            r'addEventListener\s*\([^,]*,\s*function[^}]*[(.]*(ajax|fetch|XMLHttpRequest)[(.]',
        ]
        
        for pattern in event_patterns:
            matches = re.findall(pattern, dom_content, re.IGNORECASE)
            results['event_handlers'].update(matches)
            
        # 查找AJAX调用
        ajax_patterns = [
            r'(fetch|axios\.get|axios\.post|axios\.put|axios\.delete)\s*\(\s*["\']([^"\']+)',
            r'XMLHttpRequest.*open\s*\([^,]*,\s*["\']([^"\']+)',
            r'\$\.ajax\s*\(\s*\{\s*url\s*:\s*["\']([^"\']+)',
            r'\$\.get\s*\(\s*["\']([^"\']+)',
            r'\$\.post\s*\(\s*["\']([^"\']+)',
        ]
        
        for pattern in ajax_patterns:
            matches = re.findall(pattern, dom_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    results['ajax_calls'].add(match[1] if len(match) > 1 else match[0])
                else:
                    results['ajax_calls'].add(match)
                    
        # 查找表单动作
        form_patterns = [
            r'<form[^>]*action\s*=\s*["\']([^"\']+)',
            r'formAction\s*=\s*["\']([^"\']+)',
        ]
        
        for pattern in form_patterns:
            matches = re.findall(pattern, dom_content, re.IGNORECASE)
            results['form_actions'].update(matches)
            
        self.log.info(f"[BehavioralAPI] 从DOM事件中提取到 {len(results['ajax_calls'])} 个AJAX调用")
        return results

    def bfs_generate_candidates(self, 
                               js_results: Dict[str, Any],
                               request_results: Dict[str, Any],
                               dom_results: Dict[str, Any]) -> List[str]:
        """
        使用BFS算法生成候选API路径
        
        Args:
            js_results: JavaScript分析结果
            request_results: 请求模式分析结果
            dom_results: DOM事件分析结果
            
        Returns:
            List[str]: 候选API路径列表
        """
        self.log.info("[BehavioralAPI] 开始使用BFS算法生成候选API路径")
        
        # 收集所有组件
        all_components = set()
        all_components.update(js_results.get('components', set()))
        all_components.update(request_results.get('common_prefixes', set()))
        all_components.update(request_results.get('common_suffixes', set()))
        
        # 添加一些常见的API组件
        common_components = [
            'api', 'v1', 'v2', 'v3', 'rest', 'user', 'users', 'admin', 'auth',
            'login', 'logout', 'register', 'profile', 'settings', 'config',
            'data', 'info', 'list', 'get', 'set', 'create', 'update', 'delete',
            'remove', 'add', 'edit', 'save', 'load', 'search', 'find', 'query',
            'upload', 'download', 'import', 'export', 'backup', 'restore'
        ]
        all_components.update(common_components)
        
        # BFS队列初始化
        queue = deque()
        visited = set()
        candidates = set()
        
        # 初始节点：所有组件和空路径
        initial_nodes = list(all_components) + ['']
        for node in initial_nodes:
            queue.append((node, 0))  # (当前路径, 深度)
            visited.add(node)
            
        max_depth = 3  # 最大路径深度
        max_candidates = 1000  # 最大候选项数
        
        # BFS搜索
        while queue and len(candidates) < max_candidates:
            current_path, depth = queue.popleft()
            
            # 如果达到最大深度，将当前路径加入候选
            if depth >= max_depth:
                if current_path:
                    candidates.add('/' + current_path.strip('/'))
                continue
                
            # 为当前路径添加子节点
            for component in all_components:
                if not component:
                    continue
                    
                # 生成新路径
                if current_path:
                    new_path = current_path + '/' + component
                else:
                    new_path = component
                    
                # 避免循环和重复
                if new_path not in visited and len(new_path.split('/')) <= max_depth:
                    visited.add(new_path)
                    queue.append((new_path, depth + 1))
                    
                    # 添加候选路径
                    formatted_path = '/' + new_path.strip('/')
                    if formatted_path and formatted_path not in candidates:
                        candidates.add(formatted_path)
                        
        self.log.info(f"[BehavioralAPI] BFS生成完成，共得到 {len(candidates)} 个候选API路径")
        return list(candidates)[:max_candidates]

    def discover_hidden_apis(self, 
                           js_contents: List[str] = None,
                           request_data: List[Dict] = None,
                           dom_contents: List[str] = None) -> Dict[str, Any]:
        """
        发现隐藏API接口的主函数
        
        Args:
            js_contents: JavaScript内容列表
            request_data: 请求数据列表
            dom_contents: DOM内容列表
            
        Returns:
            Dict[str, Any]: 发现结果
        """
        self.log.info("[BehavioralAPI] 开始发现隐藏API接口")
        
        # 初始化结果
        results = {
            'js_analysis': {},
            'request_analysis': {},
            'dom_analysis': {},
            'candidates': [],
            'discovered_apis': []
        }
        
        # 分析JavaScript代码
        all_js_content = '\n'.join(js_contents) if js_contents else ''
        if all_js_content:
            results['js_analysis'] = self.extract_from_js(all_js_content)
            
        # 分析请求模式
        if request_data:
            results['request_analysis'] = self.analyze_request_patterns(request_data)
            
        # 分析DOM事件
        all_dom_content = '\n'.join(dom_contents) if dom_contents else ''
        if all_dom_content:
            results['dom_analysis'] = self.extract_from_dom_events(all_dom_content)
            
        # 使用BFS生成候选API路径
        candidates = self.bfs_generate_candidates(
            results['js_analysis'],
            results['request_analysis'],
            results['dom_analysis']
        )
        results['candidates'] = candidates
        
        # 简单过滤：移除明显不合理的路径
        filtered_candidates = []
        for candidate in candidates:
            # 过滤过短或过长的路径
            path_parts = candidate.strip('/').split('/')
            if 1 <= len(path_parts) <= 4:  # 限制路径深度
                # 过滤包含特殊字符的路径
                if not re.search(r'[{}<>\\\[\]]', candidate):
                    filtered_candidates.append(candidate)
                    
        results['candidates'] = filtered_candidates
        results['discovered_apis'] = filtered_candidates  # 在实际应用中这里会有验证步骤
        
        self.log.info(f"[BehavioralAPI] 隐藏API发现完成，共发现 {len(filtered_candidates)} 个潜在API路径")
        return results

    def start_discovery(self):
        """
        启动API发现（预留接口）
        """
        self.log.info("[BehavioralAPI] 行为API发现模块已初始化")