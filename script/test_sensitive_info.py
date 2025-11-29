#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试JS文件敏感信息检测功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.JSFinder import extract_sensitive_info

def test_sensitive_info_detection():
    """测试敏感信息检测功能"""
    
    # 测试用的JS内容，包含各种敏感信息
    test_js_content = '''
    var apiKey = "api_key=sk-1234567890abcdef";
    var password = "password: mysecretpassword123";
    var token = 'token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"';
    var email = "contact@example.com";
    var phone = "13812345678";
    var idCard = "110101199001011234";
    var jdbcUrl = "jdbc:mysql://localhost:3306/mydb?user=root&password=123456";
    var awsKey = "AKIAIOSFODNN7EXAMPLE";
    
    function login() {
        var secret = "secret_key=supersecretkey";
        var accessKey = 'access_key: "AKIA1234567890EXAMPLE"';
        console.log("Logging in with credentials");
    }
    
    // 私钥示例（模拟）
    var privateKey = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQ...\\n-----END PRIVATE KEY-----";
    
    // 敏感URL示例
    var apiUrl = "https://api.example.com/admin/dashboard.php";
    var loginUrl = "https://example.com/login.jsp";
    '''
    
    print("测试JS文件敏感信息检测功能")
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

if __name__ == "__main__":
    test_sensitive_info_detection()