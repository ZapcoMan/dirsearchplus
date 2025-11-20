## dirsearchPlus

在安全测试时，安全测试人员信息收集中时可使用它进行目录枚举，目录进行指纹识别，枚举出来的403状态目录可尝试进行绕过，绕过403有可能获取管理员权限。不影响dirsearch原本功能使用

### 运行流程

dirsearch进行目录扫描--->将所有403状态的目录进行保存-->是否进行jsfind-->是(进行js爬取url和域名，将爬取到的url进行状态码识别如果是403状态则进行保存)-->进行403绕过-->目录进行指纹识别

### python环境
建议使用python<3.10，，高版本可能存在兼容问题

测试环境python=3.8.20

### 使用说明

默认不启用jsfind和403bypass

403bypass : -b yes

```
python dirsearchplus.py -u "http://www.xxx.com/" -b yes
```

jsfind ：-j yes

```
python dirsearchplus.py -u "http://www.xxx.com/" -j yes
```

jsfind和403bypass ： -b yes -j yes

```
python dirsearchplus.py -u "http://www.xxx.com/" -j yes -b yes
```

单独对指定目录进行bypass

```
python single_403pass.py -u "http://www.xxx.com/" -p "/index.php" # -p 指定路径
```

对扫描出来的目录进行指纹识别(结果会自动保存在reports目录下的.josn文件中)

```
python dirsearchplus.py -u "http://www.xxx.com/" -z yes
```

#### 2023.5.11
优化原版403bypasser，单独对某一指定路径进行403bypass

昨天同事在使用时遇到问题：发现一个403页面，如果运行dirsearch则会目录扫描后再403bypass

single_403pass.py 单独对一个url指定路径进行403bypass

```
python single_403pass.py -u "http://www.xxx.com/" -p "/index.php" # -p 指定路径
```

#### 

对目录进行指纹识别(结果会自动保存在reports目录下的.josn文件中)

```
python dirsearchplus.py -u "http://www.xxx.com/" -z yes
```

#### 

对404状态码和0B数据进行过滤不进行指纹识别

3.1 融合Packer-Fuzzer

如果提示模块已经安装还提示未安装，在/Packer-Fuzzer目录下将venv删除重新运行即可

```
python dirsearchplus.py -u "http://www.xxx.com/" -p yes
```

3.2 增加对swagger的未授权扫描

如果在目录扫描中出现swagger的路径并且未200，size大小不为0，则在目录扫描后会进行swagger未授权测试

```
python dirsearchplus.py -u "http://www.xxx.com/" --swagger yes
```

### API 接口扫描指南

现代 Web 应用程序通常使用前后端分离架构，API 接口扫描已经成为渗透测试的重要环节。以下是一些针对 API 接口扫描的建议和技巧：

#### 使用专门的字典文件
```bash
# 扫描常见 API 端点
python3 dirsearchplus.py -u https://target.com -w db/api-endpoints.txt -e json,xml

# 扫描 RESTful 资源
python3 dirsearchplus.py -u https://target.com --wordlists db/api-endpoints.txt

# 扫描 Spring Boot 应用
python3 dirsearchplus.py -u https://target.com --wordlists db/spring-boot-endpoints.txt

# 扫描 Spring Boot Actuator 端点
python3 dirsearchplus.py -u https://target.com --wordlists db/spring-boot-actuator.txt

# 扫描 RuoYI 框架应用
python3 dirsearchplus.py -u https://target.com --wordlists db/ruoyi-endpoints.txt
```

#### 框架专用字典说明

本工具针对常见的Java Web框架提供了专用的API端点字典文件：

1. **通用API字典** (`db/api-endpoints.txt`)
   - 包含500多个常见的API端点路径
   - 适用于各种Web应用的初步扫描

2. **Spring Boot专用字典** (`db/spring-boot-endpoints-clean.txt`)
   - 包含600多个Spring Boot应用常见端点
   - 涵盖Actuator、业务API、安全认证等路径
   - 适用于Spring Boot单体和微服务应用

3. **Spring Boot Actuator字典** (`db/spring-boot-actuator.txt`)
   - 专门针对Spring Boot Actuator管理端点
   - 包含健康检查、监控、配置等敏感路径
   - 用于发现未正确保护的管理接口

4. **RuoYI框架字典** (`db/ruoyi-endpoints-clean.txt`)
   - 专门针对RuoYI开源框架的API端点
   - 包含用户管理、角色权限、系统监控等模块路径
   - 适用于RuoYI单体和微服务版本

所有字典文件均采用无注释格式，可直接用于dirsearch扫描，避免无效请求。

#### 针对 API 响应特点的处理
由于现代 API 通常返回 200 状态码，即使是错误响应，因此需要基于响应内容进行过滤：
```bash
# 排除常见的错误响应内容
python3 dirsearchplus.py -u https://target.com \
  --exclude-text "Not Found" \
  --exclude-text "Error" \
  --exclude-text "404" \
  --exclude-regex "\"error\":\s*true"

# 根据响应大小过滤
python3 dirsearchplus.py -u https://target.com \
  --exclude-sizes 0B,2KB \
  --exclude-text "页面不存在"
```

#### RESTful API 扫描策略
```bash
# 扫描常见的 RESTful 资源和 HTTP 方法
python3 dirsearchplus.py -u https://target.com/api/ \
  -w db/api-endpoints.txt \
  --exclude-status 405

# 使用递归扫描深入 API 结构
python3 dirsearchplus.py -u https://target.com/api/ \
  -r --deep-recursive \
  --recursion-status 200-399
```

#### 自定义请求头和认证
API 通常需要特定的请求头或认证：
```bash
# 添加 API 密钥或认证头
python3 dirsearchplus.py -u https://target.com/api/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

#### 处理 JSON 响应
对于返回 JSON 的 API，可以使用以下策略：
```bash
# 查找返回特定 JSON 结构的响应
python3 dirsearchplus.py -u https://target.com/api/ \
  --exclude-regex "^\s*\{\s*\"(error|message)\":\s*\".*\"\s*\}\s*$" \
  --include-status 200
```

### 参考优秀项目

> dirsearch：https://github.com/maurosoria/dirsearch

> 403bypasser：https://github.com/yunemse48/403bypasser

> JSFinder：https://github.com/Threezh1/JSFinder

> EHole：https://github.com/EdgeSecurityTeam/EHole

> Packer-Fuzzer:https://github.com/rtcatc/Packer-Fuzzer