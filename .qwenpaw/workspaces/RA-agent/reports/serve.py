#!/usr/bin/env python3
"""
需求文档 HTTP 服务 v2 - 优化排版，中文文件名显示
运行方式: python3 serve.py [端口]
默认端口: 8080
"""

import os
import sys
import http.server
import urllib.parse
from datetime import datetime
import re

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
REPORTS_DIR = os.path.dirname(os.path.abspath(__file__))

# 已知文件名 → 中文显示名映射
FILE_NAMES = {
    "AI辅助评审系统_需求分析文档.md": "AI辅助评审系统 · 需求分析文档",
    "AIш╛ЕхКйшпДхобч│╗ч╗Я_щЬАц▒ВхИЖцЮРцЦЗцбг.md": "AI辅助评审系统 · 需求分析文档",
    "RA-agent_智能体互动演示脚本.md": "RA-agent · 智能体互动演示脚本",
    "RA-agent_演示提问说明书.md": "RA-agent · 演示提问说明书",
    "工业智能制药_纸质转电子与AI工艺优化_需求设计文档.md": "工业智能制药 · 纸质转电子与AI工艺优化需求设计文档",
    "х╖еф╕ЪцЩ║шГ╜хИ╢шНп_ч║╕ш┤иш╜мчФ╡хнРф╕ОAIх╖ешЙ║ф╝ШхМЦ_щЬАц▒Вшо╛шобцЦЗцбг.md": "工业智能制药 · 纸质转电子与AI工艺优化需求设计文档",
    "客户经理_需求调研13问指引卡.md": "客户经理 · 需求调研13问指引卡",
    "工艺智能体_用户需求说明书.md": "工艺智能体 · 用户需求说明书",
}

def get_display_name(filename):
    if filename in FILE_NAMES:
        return FILE_NAMES[filename]
    base = filename.replace('.md', '')
    # 去掉乱码前缀：如果文件名包含大量 %XX 编码或 Unicode 乱码，尝试提取中文部分
    # 简单处理：如果base中含有中文字符，直接显示
    if any('\u4e00' <= c <= '\u9fff' for c in base):
        return base
    return base

def get_table_html(text):
    """把 markdown 表格文本转成 HTML 表格"""
    lines = [l for l in text.split('\n') if l.strip() and not l.strip().startswith('|---')]
    if not lines:
        return ''
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    if not rows:
        return ''
    html = '<table>'
    # 第一行作为表头
    if rows[0]:
        html += '<thead><tr>' + ''.join(f'<th>{html_escape(c)}</th>' for c in rows[0]) + '</tr></thead>'
    if len(rows) > 1:
        html += '<tbody>'
        for row in rows[1:]:
            html += '<tr>' + ''.join(f'<td>{html_escape(c)}</td>' for c in row) + '</tr>'
        html += '</tbody>'
    html += '</table>'
    return html


def md_to_html(md_text, filename):
    """把 Markdown 文本转成 HTML"""
    lines = md_text.split('\n')
    parts = []
    i = 0
    in_code = False
    code_lang = ""
    code_content = ""

    # 预处理：合并表格行（以 | 开头且连续的行）
    merged_lines = []
    table_buffer = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        is_table_row = '|' in line and stripped.startswith('|')
        is_separator = stripped.startswith('|---') or stripped.startswith('|--')
        
        if is_table_row and not is_separator:
            table_buffer.append(line)
            in_table = True
        else:
            if in_table and table_buffer:
                merged_lines.append(('__TABLE__', '\n'.join(table_buffer)))
                table_buffer = []
                in_table = False
            if is_separator:
                continue  # 跳过表格分隔行
            merged_lines.append(('text', line))
    if in_table and table_buffer:
        merged_lines.append(('__TABLE__', '\n'.join(table_buffer)))

    display_name = get_display_name(filename)

    parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(display_name)} - 需求文档</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:'default',securityLevel:'loose'}});</script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.8; color: #333; background: #f0f2f5; }}
.container {{ max-width: 960px; margin: 0 auto; padding: 0 16px; }}
.document {{ background: #fff; padding: 40px 48px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin: 20px auto 40px; border-radius: 12px; }}
h1 {{ font-size: 26px; margin-bottom: 16px; color: #1a1a1a; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
h2 {{ font-size: 20px; margin-top: 32px; margin-bottom: 12px; color: #1a1a1a; border-left: 4px solid #1a73e8; padding-left: 12px; }}
h3 {{ font-size: 17px; margin-top: 24px; margin-bottom: 10px; color: #2c3e50; }}
h4 {{ font-size: 15px; margin-top: 20px; margin-bottom: 8px; color: #34495e; }}
p {{ margin-bottom: 14px; text-align: justify; line-height: 1.8; }}
ul, ol {{ margin-bottom: 14px; padding-left: 24px; }}
li {{ margin-bottom: 4px; line-height: 1.7; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }}
th, td {{ border: 1px solid #d0d7de; padding: 8px 12px; text-align: left; }}
th {{ background: #f6f8fa; font-weight: 600; white-space: nowrap; }}
tr:nth-child(even) {{ background: #fafbfc; }}
code {{ background: #eef0f2; padding: 2px 6px; border-radius: 4px; font-size: 13px; color: #d63384; }}
pre {{ background: #f6f8fa; padding: 14px 18px; border-radius: 8px; overflow-x: auto; margin-bottom: 18px; border: 1px solid #e1e4e8; }}
pre code {{ background: none; padding: 0; color: #333; }}
blockquote {{ border-left: 4px solid #1a73e8; padding: 10px 18px; margin-bottom: 16px; background: #f0f4ff; color: #555; border-radius: 0 6px 6px 0; }}
strong {{ font-weight: 600; color: #1a1a1a; }}
hr {{ border: none; border-top: 1px solid #e1e4e8; margin: 24px 0; }}
.mermaid-container {{ text-align: center; margin: 20px 0; padding: 16px; background: #fafbfc; border-radius: 8px; border: 1px solid #e1e4e8; }}
.mermaid-container .mermaid {{ display: inline-block; }}
.nav-bar {{ background: linear-gradient(135deg, #1a73e8, #1557b0); color: #fff; padding: 12px 24px; position: sticky; top: 0; z-index: 100; display: flex; align-items: center; gap: 16px; }}
.nav-bar a {{ color: rgba(255,255,255,.9); text-decoration: none; font-size: 14px; }}
.nav-bar a:hover {{ color: #fff; text-decoration: underline; }}
.nav-bar .title {{ font-weight: 600; font-size: 15px; flex-shrink: 0; }}
.nav-bar .back-link {{ margin-left: auto; }}
@media (max-width: 768px) {{ .document {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="nav-bar">
    <span class="title">{html_escape(display_name)}</span>
    <a href="/" class="back-link">← 返回文档列表</a>
</div>
<div class="container">
<div class="document">
""")

    for typ, content in merged_lines:
        stripped = content.strip()

        # 表格
        if typ == '__TABLE__':
            parts.append(get_table_html(content))
            continue

        # 代码块
        if stripped.startswith('```'):
            if in_code:
                if code_lang == 'mermaid':
                    parts.append(f'<div class="mermaid-container"><div class="mermaid">{html_escape(code_content.strip())}</div></div>')
                else:
                    parts.append(f'<pre><code>{html_escape(code_content.rstrip())}</code></pre>')
                in_code = False
                code_lang = ""
                code_content = ""
            else:
                in_code = True
                code_lang = stripped[3:].strip()
                code_content = ""
            continue

        if in_code:
            code_content += content + '\n'
            continue

        # 标题
        if stripped.startswith('# ') and not stripped.startswith('## '):
            parts.append(f'<h1>{html_escape(stripped[2:])}</h1>')
        elif stripped.startswith('## ') and not stripped.startswith('### '):
            parts.append(f'<h2>{html_escape(stripped[3:])}</h2>')
        elif stripped.startswith('### ') and not stripped.startswith('#### '):
            parts.append(f'<h3>{html_escape(stripped[4:])}</h3>')
        elif stripped.startswith('#### '):
            parts.append(f'<h4>{html_escape(stripped[5:])}</h4>')
        elif not stripped:
            parts.append('\n')
        elif stripped.startswith('- ') or stripped.startswith('* '):
            parts.append(f'<li>{html_escape(stripped[2:])}</li>')
        elif stripped.startswith('> '):
            parts.append(f'<blockquote>{html_escape(stripped[2:])}</blockquote>')
        elif stripped.startswith('---'):
            parts.append('<hr>')
        else:
            parts.append(f'<p>{html_escape(stripped)}</p>')

    parts.append(f"""
</div>
<div class="footer" style="text-align:center;padding:16px;color:#999;font-size:13px;">
    生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} · RA-agent 需求文档服务 v2
</div>
</div>
</body>
</html>""")
    return '\n'.join(parts)


def html_escape(text):
    if not text:
        return ''
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class DocHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 首页
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith('.md') and f != 'README.md'])
            html = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>需求文档列表 - RA-agent</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333;padding:40px 20px;}
.container{max-width:720px;margin:0 auto;}
h1{font-size:24px;margin-bottom:6px;color:#1a1a1a;}
.subtitle{color:#666;margin-bottom:28px;font-size:14px;}
.file-list{list-style:none;}
.file-list li{background:#fff;border-radius:10px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.08);transition:box-shadow .2s;}
.file-list li:hover{box-shadow:0 3px 12px rgba(0,0,0,.12);}
.file-list a{display:block;padding:16px 20px;text-decoration:none;color:#333;font-size:15px;line-height:1.6;}
.file-list a:hover{color:#1a73e8;}
.file-list .file-name{font-weight:600;display:flex;align-items:center;gap:8px;}
.file-list .file-icon{font-size:20px;flex-shrink:0;}
.file-list .file-info{font-size:12px;color:#999;margin-top:2px;margin-left:28px;}
</style></head>
<body><div class="container">
<h1>📄 需求文档列表</h1>
<p class="subtitle">共 """ + str(len(files)) + """ 篇文档</p>
<ul class="file-list">
"""
            for f in files:
                filepath = os.path.join(REPORTS_DIR, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M')
                size = os.path.getsize(filepath)
                display_name = get_display_name(f)
                html += f'<li><a href="/view?file={f}"><span class="file-name"><span class="file-icon">📄</span>{html_escape(display_name)}</span><div class="file-info">{mtime} · {size} bytes</div></a></li>'
            html += '</ul></div></body></html>'
            self.wfile.write(html.encode('utf-8'))
            return

        if path == '/view':
            query = urllib.parse.parse_qs(parsed.query)
            file_name = query.get('file', [None])[0]
            if file_name and file_name.endswith('.md'):
                filepath = os.path.join(REPORTS_DIR, file_name)
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    html = md_to_html(md_content, file_name)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                    return
            self.send_error(404)
            return

        super().do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    os.chdir(REPORTS_DIR)
    server = http.server.HTTPServer(('0.0.0.0', PORT), DocHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║   📄 RA-agent 需求文档服务 v2 已启动        ║
║                                              ║
║   在浏览器打开:                              ║
║   http://localhost:{PORT}                    ║
║                                              ║
║   (局域网其他设备用服务器IP替换localhost)    ║
║                                              ║
║   按 Ctrl+C 停止服务                         ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()
