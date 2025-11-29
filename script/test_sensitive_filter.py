#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试敏感信息过滤功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.JSFinder import extract_sensitive_info

def test_sensitive_info_filtering():
    """测试敏感信息过滤功能"""
    
    # 测试用的JS内容，包含真实敏感信息和误报
    test_js_content = '''
    var apiKey = "api_key=sk-1234567890abcdef";  // 真实API密钥
    var password = "password: mysecretpassword123";  // 真实密码
    var token = 'token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"';  // 真实Token
    
    // 测试数据，应该被过滤掉
    var testApiKey = "api_key=sk_test1234567890abcdef";  // 测试API密钥
    var samplePassword = "password: password123";  // 示例密码
    var exampleEmail = "contact@example.com";  // 示例邮箱
    
    // 真实的邮箱地址
    var adminEmail = "admin@company.com";
    
    function login() {
        var secret = "secret_key=supersecretkey";
        var accessKey = 'access_key: "AKIA1234567890EXAMPLE"';
        console.log("Logging in with credentials");
    }
    
    // 测试用的私钥示例（模拟）- 应该被过滤
    var fakePrivateKey = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQ...\\n-----END PRIVATE KEY-----";
    
    // 敏感URL示例
    var apiUrl = "https://api.company.com/admin/dashboard.php";
    var loginUrl = "https://company.com/login.jsp";
    '''
    
    print("测试JS文件敏感信息检测和过滤功能")
    print("=" * 50)
    
    # 检测敏感信息
    sensitive_info = extract_sensitive_info(test_js_content)
    
    if sensitive_info:
        print("发现的敏感信息:")
        for info_type, values in sensitive_info.items():
            print(f"\n{info_type.upper()}:")
            for value in values:
                print(f"  - {value}")
    else:
        print("未发现敏感信息")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_sensitive_info_filtering()