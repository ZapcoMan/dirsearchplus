# 更新日志 (Change Log)

> 本文档从主 [README](../README.md) 抽离，集中记录 dirsearchPlus 的版本变更与历史提交。
> 返回文档目录：[docs/README.md](README.md)

格式参考 [Keep a Changelog](https://keepachangelog.com/)，版本号与代码中 `lib/core/settings.py` 的 `VERSION` 保持一致（`<主>.<次>.<修订>`）。

> **编号说明**：所有版本号以代码 `lib/core/settings.py` 的 `VERSION` 为准，并按发布顺序从当前版本依次递减 1 排布（当前 `[1.5.12]`，上一版 `[1.5.11]`，以此类推）。早期文档中的 `0.1.x`、以及 dirsearch 引擎时期的 `3.x` / `2023.x` 记录，均已统一映射到该连续序列。

## [1.5.12] - 稳定性与安全加固

### 新增功能
- 新增运行时开关 `--debug` / `--secure` / `--insecure` 及环境变量 `DIRSEARCHPLUS_DEBUG` / `DIRSEARCHPLUS_INSECURE` / `DIRSEARCHPLUS_VERIFY_TLS`，集中控制日志与 TLS 校验（TLS 默认仍不校验）
- 新增 `PACKER_FUZZER_REF` 以锁定 Packer-Fuzzer 克隆来源，并对运行时克隆做浅克隆 + 入口脚本完整性校验
- 新增 `requirements-browser.txt`，将浏览器/报表相关可选依赖与核心依赖分离
- 扫描流水线阶段化容错：单个阶段异常（含 `sys.exit`）不再中断整条流水线，并输出各阶段耗时

### 缺陷修复
- 修复 403 绕过（`pass403.py`）`createNewHeaders` 空实现导致头部绕过静默失效；修正 `locals()` 动态赋值不可靠问题
- 修复 JS 发现的 403 路径拼接丢失前导斜杠且截断多级路径，导致绕过请求命中畸形 URL 的问题（改用 `urlparse`）
- 修复 SubFinder 子进程管道死锁：`Popen` 只 poll 不读取管道，大输出会挂起（改为流式读取并合并 stderr）
- 修复报告路径文件 `dir_file_path.txt` 在文件名去重调整之前写入、导致指向错误文件的问题
- 修复 JSFinder 在 `reports/` 目录缺失时写 CSV/敏感信息文件崩溃的问题（自动创建目录）
- 将多处静默 `except: pass` 补充为日志记录；`single_403pass.py` 不再吞掉异常
- 修正 README 中错误的入口文件名（`dirsearchX.py` → `dirsearchplus.py`）

## [1.5.11] - 新功能集成

### 新增功能
- 集成参数污染检测模块（HPP/HFP），用于检测 URL 参数重复 key、JSON 重复字段、表单 key 重复、数组展开解析差异及 Spring MVC 参数绑定漏洞等场景
- 集成 SubFinder 子域名扫描模块，用于发现目标的子域名信息
- 添加 `-d yes` 参数启用子域名扫描功能
- 集成 SSRF 深度探测功能，自动检测服务端请求伪造漏洞
- 集成动态 API 枚举功能，基于行为推断发现隐藏 API
- 优化各模块间的数据传递和协调工作

## [1.5.10] - by ZapcoMan

### 新增功能
- 集成 SubFinder 子域名扫描模块，用于发现目标的子域名信息
- 添加 `-d yes` 参数启用子域名扫描功能
- 优化各模块间的数据传递和协调工作

## [1.5.9] - by ZapcoMan

### 新增功能
- 集成 Packer-Fuzzer 模块，用于前端打包器检测和模糊测试
- 集成 Swagger 未授权访问扫描功能
- 添加多个专用 API 字典文件：
  - `db/api-endpoints.txt`：通用 API 端点字典
  - `db/spring-boot-endpoints.txt`：Spring Boot 专用字典
  - `db/spring-boot-actuator.txt`：Spring Boot Actuator 字典
  - `db/ruoyi-endpoints.txt`：RuoYI 框架字典

### 改进优化
- 优化 403 绕过功能，提供单独路径绕过能力
- 改进 JSFinder 模块，增强子域名发现功能
- 统一各模块日志输出格式，与 dirsearch 保持一致
- 修复 ehole 模块中"系统找不到指定的路径"错误问题
- 修复 Packer-Fuzzer 模块导入错误问题

### 使用说明更新
- 添加 `-p yes` 参数启用 Packer-Fuzzer 模块
- 添加 `--swagger yes` 参数启用 Swagger 扫描
- 添加 `-a` 或 `--all` 参数一键启用所有模块
- 更新 API 接口扫描指南和使用示例

## [1.5.8] - 全模块一键启用

### 新增功能
- 添加 `-a` 或 `--all` 参数，可一键启用所有功能模块

## [1.5.7] - Packer-Fuzzer 与 Swagger 集成

### 新增功能
- 集成 Packer-Fuzzer 模块，用于前端打包器检测和模糊测试
- 集成 Swagger 未授权访问扫描功能

## [1.5.6] - 单路径 403 绕过

### 改进优化
- 优化原版 403bypasser，支持单独对某一指定路径进行 403 绕过
- 添加 `single_403pass.py` 脚本，可对单个 URL 的指定路径进行 403 绕过

## 历史提交记录

根据 git 历史记录，主要更新包括：

1. **feat(ParameterPollution)**：集成参数污染检测功能
   - 添加 ParameterPollutionDetector 模块，用于 HTTP 参数污染检测
   - 实现 URL 参数重复 key、JSON 重复字段、表单 key 重复、数组展开解析差异及 Spring MVC 参数绑定漏洞检测
   - 集成到 Packer-Fuzzer 扫描流程中，自动检测参数处理差异引起的安全问题

2. **feat(SubFinder)**：集成子域名扫描功能
   - 添加 SubFinder 模块，用于子域名爆破扫描
   - 集成 subfinder-x.exe 工具，支持 HTTP 扫描和指纹识别
   - 优化文件路径处理，确保在不同环境下都能正确运行
   - 统一控制台输出格式，增强可读性与调试便利性

3. **feat(Packer-Fuzzer)**：集成自定义日志系统并优化错误处理
   - 在多个模块中引入并使用 Packer-Fuzzer 自带的 CreatLog 日志系统
   - 为 HTML 检查过程添加异常捕获和错误日志记录
   - 统一控制台输出格式，增强可读性与调试便利性
   - 更新语言配置文件中的提示文本内容
   - 优化代理测试模块的异常处理逻辑
   - 规范化代码注释与日志输出内容的表述方式

4. **feat(cli)**：添加全模块启动选项
   - 添加 `-a` 或 `--all` 参数，可一键启用所有功能模块（bypass, jsfind, zwsb, packer-fuzzer, swagger, subfinder）

5. **feat(core)**：增强终端输出功能并优化日志显示

6. **feat(dirsearchplus)**：优化 JsFind 和 Packer-Fuzzer 功能并改进输出格式

7. **feat(ehole)**：更新指纹识别规则并优化扫描输出格式

---

返回主文档：[README](../README.md) ｜ 文档目录：[docs/README.md](README.md)
