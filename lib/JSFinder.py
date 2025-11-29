import requests, argparse, sys, re, csv, os
import urllib3
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from concurrent.futures import ThreadPoolExecutor

from lib.view.terminal import output
from lib.view.colors import set_color

# 从单独的文件导入敏感信息正则表达式模式
from lib.core.sensitive_patterns import SENSITIVE_PATTERNS


def load_whitelist():
    """
    加载敏感信息白名单

    Returns:
        set: 白名单条目集合
    """
    whitelist = set()
    whitelist_file = os.path.join(os.path.dirname(__file__), '..', 'db', 'sensitive_whitelist.txt')

    if os.path.exists(whitelist_file):
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('#'):
                    whitelist.add(line)

    return whitelist


def extract_sensitive_info(js_content):
    """
    从JavaScript内容中提取敏感信息

    Args:
        js_content (str): JavaScript文件内容

    Returns:
        dict: 包含各类敏感信息的字典
    """
    sensitive_info = {}

    # 加载白名单
    whitelist = load_whitelist()

    # 定义明显的测试/示例关键词，用于过滤误报
    test_keywords = [
        'test', 'sample', 'example', 'demo', 'dummy',
        'fake', 'mock', 'template', 'placeholder'
    ]

    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        matches = re.findall(pattern, js_content, re.IGNORECASE)
        if matches:
            # 过滤可能的误报
            filtered_matches = []
            for match in matches:
                # 将匹配转换为字符串（有些可能是元组）
                match_str = match if isinstance(match, str) else ''.join(match)

                # 检查是否在白名单中
                whitelist_entry = f"{pattern_name}:{match_str}"
                if whitelist_entry in whitelist:
                    continue  # 在白名单中，跳过

                # 检查匹配项周围是否有测试相关的关键词
                match_index = js_content.find(match_str)
                context_start = max(0, match_index - 50)
                context_end = min(len(js_content), match_index + len(match_str) + 50)
                context = js_content[context_start:context_end].lower()

                # 如果上下文中包含测试关键词，则认为是误报
                if not any(keyword in context for keyword in test_keywords):
                    filtered_matches.append(match)

            # 去重
            unique_matches = list(set(filtered_matches))
            if unique_matches:
                sensitive_info[pattern_name] = unique_matches

    return sensitive_info


def extract_URL(JS):
    """
    从JavaScript代码中提取URL链接

    Args:
        JS (str): 包含JavaScript代码的字符串

    Returns:
        list: 提取出的URL列表
    """
    pattern_raw = r"""
	  (?:"|')                               # Start newline delimiter
	  (
		((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
		[^"'/]{1,}\.                        # Match a domainname (any character + dot)
		[a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
		|
		((?:/|\.\./|\./)                    # Start with /,../,./
		[^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
		[^"'><,;|()]{1,})                   # Rest of the characters can't be
		|
		([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
		[a-zA-Z0-9_\-/]{1,}                 # Resource name
		\.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
		(?:[\?|/][^"|']{0,}|))              # ? mark with parameters
		|
		([a-zA-Z0-9_\-]{1,}                 # filename
		\.(?:php|asp|aspx|jsp|json|
			 action|html|js|txt|xml)             # . + extension
		(?:\?[^"|']{0,}|))                  # ? mark with parameters
	  )
	  (?:"|')                               # End newline delimiter
	"""
    pattern = re.compile(pattern_raw, re.VERBOSE)
    result = re.finditer(pattern, str(JS))
    if result == None:
        return None
    js_url = []
    return [match.group().strip('"').strip("'") for match in result
            if match.group() not in js_url]


# Get the page source
def Extract_html(URL):
    """
    获取指定URL的HTML页面源码

    Args:
        URL (str): 目标网页URL

    Returns:
        str: HTML页面源码，如果访问失败则返回None
    """
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36",
        }
    # "Cookie": args.cookie}
    try:
        raw = requests.get(URL, headers=header, timeout=3, verify=False)
        raw = raw.content.decode("utf-8", "ignore")
        return raw
    except:
        return None


# Handling relative URLs
def process_url(URL, re_URL):
    """
    处理相对URL，将其转换为完整的绝对URL

    Args:
        URL (str): 原始URL
        re_URL (str): 需要处理的相对URL

    Returns:
        str: 处理后的完整URL
    """
    black_url = ["javascript:"]  # Add some keyword for filter url.
    URL_raw = urlparse(URL)
    ab_URL = URL_raw.netloc
    host_URL = URL_raw.scheme
    if re_URL[0:2] == "//":
        result = host_URL + ":" + re_URL
    elif re_URL[0:4] == "http":
        result = re_URL
    elif re_URL[0:2] != "//" and re_URL not in black_url:
        if re_URL[0:1] == "/":
            result = host_URL + "://" + ab_URL + re_URL
        else:
            if re_URL[0:1] == ".":
                if re_URL[0:2] == "..":
                    result = host_URL + "://" + ab_URL + re_URL[2:]
                else:
                    result = host_URL + "://" + ab_URL + re_URL[1:]
            else:
                result = host_URL + "://" + ab_URL + "/" + re_URL
    else:
        result = URL
    return result


def find_last(string, str):
    """
    查找字符串中某个子串的所有出现位置

    Args:
        string (str): 源字符串
        str (str): 要查找的子串

    Returns:
        list: 所有匹配位置的索引列表
    """
    positions = []
    last_position = -1
    while True:
        position = string.find(str, last_position + 1)
        if position == -1: break
        last_position = position
        positions.append(position)
    return positions


def find_by_url(url, js = False):
    """
    从指定URL中提取所有链接

    Args:
        url (str): 目标网页URL
        js (bool): 是否只处理JavaScript文件，默认False

    Returns:
        list: 提取到的URL列表
    """
    if js == False:
        try:
            pass
            #print("url:" + url)
        except:
            print("Please specify a URL like https://www.baidu.com")
        html_raw = Extract_html(url)
        if html_raw == None:
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}]  Fail to access " + url
            output.error(message)
            return None
        #print(html_raw)
        html = BeautifulSoup(html_raw, "html.parser")
        html_scripts = html.findAll("script")
        script_array = {}
        script_temp = ""
        # 收集所有检测到的敏感信息
        all_sensitive_info = {}
        for html_script in html_scripts:
            script_src = html_script.get("src")
            if script_src == None:
                script_temp += html_script.get_text() + "\n"
                # 检测内联脚本中的敏感信息
                sensitive_info = extract_sensitive_info(html_script.get_text())
                if sensitive_info:
                    # 合并敏感信息
                    for info_type, values in sensitive_info.items():
                        if info_type not in all_sensitive_info:
                            all_sensitive_info[info_type] = []
                        all_sensitive_info[info_type].extend(values)
                    
                    current_time = time.strftime("%H:%M:%S")
                    message = f"[{current_time}]  在内联脚本中发现敏感信息:"
                    output.new_line(set_color(message, fore="red"))
                    for info_type, values in sensitive_info.items():
                        for value in values:
                            message = f"[{current_time}]    {info_type}: {value}"
                            output.new_line(set_color(message, fore="red"))
            else:
                purl = process_url(url, script_src)
                script_content = Extract_html(purl)
                script_array[purl] = script_content
                # 检测外部脚本文件中的敏感信息
                if script_content:
                    sensitive_info = extract_sensitive_info(script_content)
                    if sensitive_info:
                        # 合并敏感信息
                        for info_type, values in sensitive_info.items():
                            if info_type not in all_sensitive_info:
                                all_sensitive_info[info_type] = []
                            all_sensitive_info[info_type].extend(values)
                        
                        current_time = time.strftime("%H:%M:%S")
                        message = f"[{current_time}]  在外部脚本 {purl} 中发现敏感信息:"
                        output.new_line(set_color(message, fore="red"))
                        for info_type, values in sensitive_info.items():
                            for value in values:
                                message = f"[{current_time}]    {info_type}: {value}"
                                output.new_line(set_color(message, fore="red"))
        
        # 保存检测到的敏感信息到文件
        if all_sensitive_info:
            save_sensitive_info(all_sensitive_info, url)
        
        script_array[url] = script_temp
        allurls = []
        for script in script_array:
            #print(script)
            temp_urls = extract_URL(script_array[script])
            if len(temp_urls) == 0: continue
            for temp_url in temp_urls:
                allurls.append(process_url(script, temp_url))
        result = []
        for singerurl in allurls:
            url_raw = urlparse(url)
            domain = url_raw.netloc
            positions = find_last(domain, ".")
            miandomain = domain
            if len(positions) > 1:miandomain = domain[positions[-2] + 1:]
            #print(miandomain)
            suburl = urlparse(singerurl)
            subdomain = suburl.netloc
            #print(singerurl)
            if miandomain in subdomain or subdomain.strip() == "":
                if singerurl.strip() not in result:
                    result.append(singerurl)
        return result
    return sorted(set(extract_URL(Extract_html(url)))) or None


def find_subdomain(urls, mainurl):
    """
    从URL列表中提取子域名

    Args:
        urls (list): URL列表
        mainurl (str): 主域名URL

    Returns:
        list: 子域名列表
    """
    url_raw = urlparse(mainurl)
    domain = url_raw.netloc
    miandomain = domain
    positions = find_last(domain, ".")
    if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
    subdomains = []
    for url in urls:
        suburl = urlparse(url)
        subdomain = suburl.netloc
        #print(subdomain)
        if subdomain.strip() == "": continue
        if miandomain in subdomain:
            if subdomain not in subdomains:
                subdomains.append(subdomain)
    return subdomains


def find_by_url_deep(url):
    """
    深度扫描URL，递归提取链接

    Args:
        url (str): 目标网页URL

    Returns:
        list: 所有提取到的URL列表
    """
    html_raw = Extract_html(url)
    if html_raw == None:
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  Fail to access " + url
        output.error(message)
        return None
    html = BeautifulSoup(html_raw, "html.parser")
    html_as = html.findAll("a")
    links = []
    for html_a in html_as:
        src = html_a.get("href")
        if src == "" or src == None: continue
        link = process_url(url, src)
        if link not in links:
            links.append(link)
    if links == []: return None
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}]  ALL Find " + str(len(links)) + " links"
    output.new_line(set_color(message, fore="green", style="bright"))
    urls = []
    i = len(links)
    for link in links:
        temp_urls = find_by_url(link)
        if temp_urls == None: continue
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  Remaining " + str(i) + " | Find " + str(len(temp_urls)) + " URL in " + link
        output.new_line(set_color(message, fore="green"))
        for temp_url in temp_urls:
            if temp_url not in urls:
                urls.append(temp_url)
        i -= 1
    return urls


def find_by_file(file_path, js=False):
    """
    从文件中读取URL列表并提取链接

    Args:
        file_path (str): 包含URL的文件路径
        js (bool): 是否只处理JavaScript文件，默认False

    Returns:
        list: 提.extract到的URL列表
    """
    with open(file_path, "r") as fobject:
        links = fobject.read().split("\n")
    if links == []: return None
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}]  ALL Find " + str(len(links)) + " links"
    output.new_line(set_color(message, fore="green", style="bright"))
    urls = []
    i = len(links)
    for link in links:
        if js == False:
            temp_urls = find_by_url(link)
        else:
            temp_urls = find_by_url(link, js=True)
            # 如果是JS文件，直接检测敏感信息
            if temp_urls is not None:
                try:
                    js_content = Extract_html(link)
                    if js_content:
                        sensitive_info = extract_sensitive_info(js_content)
                        if sensitive_info:
                            current_time = time.strftime("%H:%M:%S")
                            message = f"[{current_time}]  在JS文件 {link} 中发现敏感信息:"
                            output.new_line(set_color(message, fore="red"))
                            for info_type, values in sensitive_info.items():
                                for value in values:
                                    message = f"[{current_time}]    {info_type}: {value}"
                                    output.new_line(set_color(message, fore="red"))
                            # 保存检测到的敏感信息到文件
                            save_sensitive_info(sensitive_info, link)
                except Exception as e:
                    pass
        if temp_urls == None: continue
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  " + str(i) + " Find " + str(len(temp_urls)) + " URL in " + link
        output.new_line(set_color(message, fore="green"))
        for temp_url in temp_urls:
            if temp_url not in urls:
                urls.append(temp_url)
        i -= 1
    return urls


def giveresult(urls, domian):
    """
    处理和输出结果，包括状态码检测和文件保存

    Args:
        urls (list): URL列表
        domian (str): 域名

    Returns:
        None
    """
    sss = []
    if urls == None:
        return None
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}]  Find " + str(len(urls)) + " URL:"
    output.new_line(set_color(message, fore="magenta"))
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}]  Start testing for survival!"
    output.new_line(set_color(message, fore="yellow"))
    content_url = ""
    content_subdomain = ""

    def process_url(url):
        """
        处理单个URL，检查其可访问性并获取状态码
        """
        import time
        title = ''
        Exclusions = ['.js', '.png', '.jpg', '.ico', '.css', '.gif', '.svg', '.mp3', '.wav', '.mp4', '.webm']
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
            res = requests.get(url, headers=headers, verify=False, timeout=2)
            status_code = res.status_code
            soup = BeautifulSoup(res.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text
        except:
            status_code = 404

        if status_code in (200, 201, 204):
            colour = set_color(str(status_code), fore="green")
        elif status_code == 401:
            colour = set_color(str(status_code), fore="yellow")
        elif status_code == 403:
            colour = set_color(str(status_code), fore="blue")
        elif status_code in range(500, 600):
            colour = set_color(str(status_code), fore="red")
        elif status_code in range(300, 400):
            colour = set_color(str(status_code), fore="cyan")
        else:
            colour = set_color(str(status_code), fore="magenta")
        if status_code != 404:
            if not any(url.endswith(ext) for ext in Exclusions):

                sss.append({"URL": url, "Code": str(status_code), "title": str(title)})
                if status_code == 403:
                    try:
                        with open('jsfind403list.txt', 'a+') as f:
                            f.write(str(url) + '\n')
                    except:
                        pass

    def main():
        """
        使用线程池并发处理URL列表
        """
        with ThreadPoolExecutor() as executor:
            executor.map(process_url, urls)

    main()

    def GreateFile(sss, domian):
        """
        将结果保存到CSV文件

        Args:
            sss (list): 结果数据列表
            domian (str): 域名
        """
        parsed_url = urlparse(domian)
        domain1 = parsed_url.netloc
        domain1 = domain1.replace('.', '_').replace(':', '_')
        with open("reports/" + domain1 + '.csv', 'w', newline='', encoding='UTF-8') as csvf:
            fieldnames = ['URL', 'Code', 'title']
            writer = csv.DictWriter(csvf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sss)

    GreateFile(sss, domian)

    # print(Style.RESET_ALL)
    subdomains = find_subdomain(urls, domian)
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}]  Find " + str(len(subdomains)) + " Subdomain:"
    output.new_line(set_color(message, fore="magenta"))
    # print(Style.RESET_ALL)

    # 获取当前路径
    # path_get = os.getcwd()
    for subdomain in subdomains:
        # http_url=subdomain
        # if 'http' not in http_url:
        # 	try:
        # 		http_url='http://'+http_url
        # 		requests.get(http_url,timeout=4)
        # 	except:
        # 		http_url='https://'+http_url
        # with open(path_get+'/ehole/ehole.txt','a+') as f:
        # 	f.write(http_url+'\n')
        content_subdomain += subdomain + "\n"
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  " + subdomain
        output.new_line(set_color(message, fore="blue"))
    
    # 检测并保存敏感信息
    try:
        # 从域名获取HTML内容并检测敏感信息
        html_content = Extract_html(domian)
        if html_content:
            sensitive_info = extract_sensitive_info(html_content)
            if sensitive_info:
                save_sensitive_info(sensitive_info, domian)
    except Exception as e:
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  检测敏感信息时出错: {str(e)}"
        output.new_line(set_color(message, fore="red"))


def jsfind():
    import lib.JSFinder
    from lib.core.options import parse_options
    from lib.view.terminal import output
    from lib.view.colors import set_color
    import time
    # current_time = time.strftime("%H:%M:%S")
    # message = f"[{current_time}] jsfind "
    # output.new_line(set_color(message, fore="cyan"))
    if (parse_options()['jsfind']) == None:
        pass
    else:
        jsf="".join(parse_options()['jsfind'])
        if jsf=='yes':
            # print(Fore.GREEN + Style.BRIGHT+"开始JsFind！"+Style.RESET_ALL)
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}] 开始JsFind！"
            output.new_line(set_color(message, fore="green", style="bright"))
            url="".join(parse_options()['urls'])
            urls = lib.JSFinder.find_by_url(url)
            lib.JSFinder.giveresult(urls, url)
        else:
            pass


# 添加敏感信息保存功能
def save_sensitive_info(sensitive_data, domain):
    """
    保存敏感信息到文件

    Args:
        sensitive_data (dict): 敏感信息字典
        domain (str): 域名
    """
    if not sensitive_data:
        return

    try:
        parsed_url = urlparse(domain)
        domain_name = parsed_url.netloc
        safe_domain_name = domain_name.replace('.', '_').replace(':', '_')

        # 保存敏感信息到文件
        with open(f"reports/{safe_domain_name}_sensitive_info.txt", 'w', encoding='utf-8') as f:
            f.write(f"敏感信息检测报告\n")
            f.write(f"目标域名: {domain}\n")
            f.write(f"检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")

            for info_type, values in sensitive_data.items():
                f.write(f"{info_type.upper()}:\n")
                for value in values:
                    f.write(f"  - {value}\n")
                f.write("\n")

        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  敏感信息已保存到 reports/{safe_domain_name}_sensitive_info.txt"
        output.new_line(set_color(message, fore="red"))
    except Exception as e:
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]  保存敏感信息时出错: {str(e)}"
        output.new_line(set_color(message, fore="red"))
