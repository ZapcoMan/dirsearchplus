# 模块功能详解

> 本文档从主 [README](../README.md) 抽离，收录 dirsearchPlus 各增强模块的详细说明。
> 返回文档目录：[docs/README.md](README.md)

dirsearchPlus 在 dirsearch 基础上集成了多个安全测试模块。下表为总览，随后是每个模块的使用方式。

| 模块 | 启用参数 | 作用 |
|------|----------|------|
| 目录扫描 | 默认 | 基于 dirsearch 的路径/目录爆破 |
| 403 绕过 | `-b yes` | 对扫描结果中 403 状态的路径进行绕过测试 |
| JS 信息收集 | `-j yes` | 从 JS 文件中提取 URL 与子域名 |
| 指纹识别 | `-z yes` | 使用 EHole 识别目标技术框架 |
| Packer-Fuzzer | `-p yes` | 前端打包器（Webpack 等）检测与模糊测试 |
| Swagger 扫描 | `--swagger yes` | 对发现的 Swagger 接口进行未授权访问测试 |
| 子域名爆破 | `-d yes` | 使用 SubFinder 进行子域名爆破 |
| 参数污染检测 | 随 Packer-Fuzzer | HPP/HFP 行为差异检测 |
| SSRF 深度探测 | 随 Packer-Fuzzer | 服务端请求伪造漏洞自动探测 |
| 动态 API 枚举 | 自动 | 基于行为推断发现隐藏 API |
| 全模块启动 | `-a` / `--all` | 一键启用上述所有模块 |

---

## 目录扫描 (dirsearch)

基础目录扫描功能，支持多种自定义选项（线程、字典、状态码过滤、递归等）。

```bash
python dirsearchplus.py -u "http://www.example.com/"
```

## 403 绕过测试 (-b yes)

对扫描结果中 403 状态的路径进行绕过测试。

```bash
python dirsearchplus.py -u "http://www.example.com/" -b yes
```

单独对指定目录进行绕过测试：

```bash
python single_403pass.py -u "http://www.example.com/" -p "/index.php"
```

## JS 信息收集 (-j yes)

从目标网站的 JavaScript 文件中提取 URL 和子域名信息。

```bash
python dirsearchplus.py -u "http://www.example.com/" -j yes
```

## 指纹识别 (-z yes)

使用 EHole 进行网站指纹识别，识别目标使用的技术框架。

```bash
python dirsearchplus.py -u "http://www.example.com/" -z yes
```

## Packer-Fuzzer (-p yes)

针对前端打包器（如 Webpack）的检测和模糊测试工具。

```bash
python dirsearchplus.py -u "http://www.example.com/" -p yes
```

注意：

- 如果提示模块已安装但仍报错，请删除 `/Packer-Fuzzer` 目录下的 `venv` 文件夹后重新运行。
- 首次启用时若本地无该模块，会从 GitHub 浅克隆；建议设置环境变量 `PACKER_FUZZER_REF` 锁定标签/分支或提交 SHA，以降低动态克隆的供应链风险。

## Swagger 扫描 (--swagger yes)

对发现的 Swagger 接口进行未授权访问测试。

```bash
python dirsearchplus.py -u "http://www.example.com/" --swagger yes
```

> Swagger 模块依赖浏览器/报表相关可选依赖（Selenium、openpyxl 等）。若未安装 `requirements-browser.txt`，该阶段会自动优雅跳过，不影响整条流水线。

## 子域名爆破 (-d yes)

使用 SubFinder 进行子域名爆破，发现目标的子域名信息。

```bash
python dirsearchplus.py -u "http://www.example.com/" -d yes
```

该模块会自动从 `resources/bypass403_url.txt` 文件中读取目标域名，并进行子域名扫描。扫描结果将显示发现的子域名及其相关信息。

## 参数污染检测 (HPP/HFP)

自动检测 HTTP 参数污染漏洞，包括：

- URL 参数重复 key 行为差异
- JSON 重复字段行为差异
- 表单 key 重复行为差异
- 数组展开解析差异
- Spring MVC 参数绑定漏洞

输出示例：同样 `/api/user?id=1&id=2`，不同框架差异巨大，可触发越权。

## SSRF 深度探测

自动化 SSRF 深度探测功能，用于检测服务端请求伪造漏洞：

* 检测所有可能的 URL 参数（包括隐藏字段）
* 对参数注入内部网探测 payload
* 分析响应时间、错误差异、DNS 出站等间接特征

该功能已集成到 Packer-Fuzzer 模块中，会在漏洞检测阶段自动运行。

## 动态 API 枚举（基于行为推断）

基于行为推断的动态 API 枚举功能，替代传统的字典扫描方式：

* 根据前端 JS、请求链路、按钮事件推测后端 API 结构
* 通过 BFS 推导出隐藏 API
* 提高 API 发现的准确性和覆盖率

该功能会自动分析目标网站的 JavaScript 代码、请求模式和 DOM 事件，通过行为推断生成候选 API 路径，然后进行验证。

## 全模块启动 (-a)

使用单一参数启用上述所有功能模块（bypass、jsfind、zwsb、packer-fuzzer、swagger、subfinder）。

```bash
python dirsearchplus.py -u "http://www.example.com/" -a
```

---

返回主文档：[README](../README.md) ｜ 文档目录：[docs/README.md](README.md)
