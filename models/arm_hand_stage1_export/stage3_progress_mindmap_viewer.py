#!/usr/bin/env python3
"""Live progress mind-map viewer.

This is a tiny dependency-free local web app. It serves
a mind-map JSON file and refreshes the browser view every few seconds, so
alignment meetings can use a single live map.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import socket
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "docs" / "stage3_progress_mindmap.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def load_mindmap(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_node(data.get("root"), path=())
    return data


def validate_node(node: Any, *, path: tuple[str, ...]) -> None:
    if not isinstance(node, dict):
        raise ValueError(f"node at {'/'.join(path) or '<root>'} must be an object")
    for key in ("id", "label", "status", "summary"):
        if not isinstance(node.get(key), str) or not node.get(key):
            raise ValueError(f"node at {'/'.join(path) or '<root>'} missing string key {key!r}")
    children = node.get("children", [])
    if children is None:
        children = []
    if not isinstance(children, list):
        raise ValueError(f"children at {'/'.join(path) or '<root>'} must be a list")
    for child in children:
        child_id = str(child.get("id", "unknown")) if isinstance(child, dict) else "unknown"
        validate_node(child, path=path + (child_id,))


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(int(status))
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler: BaseHTTPRequestHandler, body: str, *, content_type: str = "text/html; charset=utf-8") -> None:
    encoded = body.encode("utf-8")
    handler.send_response(int(HTTPStatus.OK))
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(encoded)


def make_handler(data_path: Path, open_root: Path = ROOT):
    open_root = open_root.resolve()

    class MindMapHandler(BaseHTTPRequestHandler):
        server_version = "ProgressMindMap/0.2"

        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"[{time.strftime('%H:%M:%S')}] {self.address_string()} {fmt % args}")

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                text_response(self, HTML)
                return
            if parsed.path == "/api/mindmap":
                try:
                    payload = load_mindmap(data_path)
                    payload["_source"] = str(data_path.resolve())
                    payload["_mtime"] = data_path.stat().st_mtime
                    json_response(self, payload)
                except Exception as exc:
                    json_response(self, {"error": str(exc), "source": str(data_path)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            if parsed.path.startswith("/open/"):
                rel = parsed.path.removeprefix("/open/")
                target = (open_root / rel).resolve()
                if not str(target).startswith(str(open_root)) or not target.exists():
                    json_response(self, {"error": "file not found", "path": rel}, HTTPStatus.NOT_FOUND)
                    return
                content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                body = target.read_bytes()
                self.send_response(int(HTTPStatus.OK))
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            json_response(self, {"error": "not found", "path": parsed.path}, HTTPStatus.NOT_FOUND)

    return MindMapHandler


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) != 0


def pick_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        if port_is_free(host, port):
            return port
    raise OSError(f"No free port in range {preferred}-{preferred + 19}")


def main(
    *,
    default_data: Path = DEFAULT_DATA,
    default_port: int = DEFAULT_PORT,
    default_open_root: Path = ROOT,
    description: str = "启动实时进展思维导图。",
    label: str = "进展思维导图",
) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--data", type=Path, default=default_data)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=default_port)
    parser.add_argument("--open-root", type=Path, default=default_open_root)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check", action="store_true", help="Validate the JSON and exit.")
    args = parser.parse_args()

    data_path = args.data.resolve()
    open_root = args.open_root.resolve()
    load_mindmap(data_path)
    if args.check:
        print(f"OK: {data_path}")
        return 0

    port = pick_port(args.host, int(args.port))
    handler = make_handler(data_path, open_root=open_root)
    server = ThreadingHTTPServer((args.host, port), handler)
    url = f"http://{args.host}:{port}/"
    print(f"{label}: {url}")
    print(f"数据来源: {data_path}")
    print(f"文件打开根目录: {open_root}")
    print("按 Ctrl+C 停止。")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mind-map server.")
    finally:
        server.server_close()
    return 0


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>进展思维导图</title>
  <link rel="icon" href="data:,">
  <style>
    :root {
      --bg: #f7f7f3;
      --panel: #ffffff;
      --ink: #242424;
      --muted: #686b70;
      --line: #c9cbd1;
      --done: #2f8f68;
      --current: #1f6fb2;
      --watch: #b46a18;
      --next: #7a5eb8;
      --rejected: #9b3e3e;
      --unknown: #6b7280;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
    }
    header {
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px;
      background: rgba(247, 247, 243, 0.94);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(8px);
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 650;
    }
    .subtitle {
      margin-top: 3px;
      color: var(--muted);
      font-size: 13px;
      max-width: 980px;
      line-height: 1.35;
    }
    .toolbar {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    button {
      border: 1px solid #bfc4cd;
      background: #fff;
      color: var(--ink);
      border-radius: 7px;
      padding: 7px 10px;
      cursor: pointer;
      font-size: 13px;
    }
    button:hover { border-color: #7a8495; }
    .main {
      min-width: 0;
      display: flex;
      flex-direction: column;
    }
    .canvas-wrap {
      overflow: auto;
      height: calc(100vh - 75px);
      padding: 18px;
    }
    svg {
      background: #fffefb;
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 100%;
    }
    .link {
      stroke: #b7bbc4;
      stroke-width: 1.5;
      fill: none;
    }
    .node rect {
      fill: #fff;
      stroke-width: 2;
      rx: 8;
      filter: drop-shadow(0 2px 5px rgba(0,0,0,0.08));
    }
    .node text {
      fill: var(--ink);
      font-size: 13px;
      pointer-events: none;
    }
    .node .status {
      fill: #fff;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .node.done rect { stroke: var(--done); }
    .node.current rect { stroke: var(--current); }
    .node.watch rect { stroke: var(--watch); }
    .node.next rect { stroke: var(--next); }
    .node.rejected rect { stroke: var(--rejected); }
    .node.unknown rect { stroke: var(--unknown); }
    .badge.done { fill: var(--done); }
    .badge.current { fill: var(--current); }
    .badge.watch { fill: var(--watch); }
    .badge.next { fill: var(--next); }
    .badge.rejected { fill: var(--rejected); }
    .badge.unknown { fill: var(--unknown); }
    .node.selected rect { stroke-width: 3.5; }
    .aside {
      min-width: 0;
      border-left: 1px solid var(--line);
      background: var(--panel);
      padding: 16px;
      height: 100vh;
      overflow: auto;
    }
    .status-pill {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      background: var(--unknown);
    }
    .status-pill.done { background: var(--done); }
    .status-pill.current { background: var(--current); }
    .status-pill.watch { background: var(--watch); }
    .status-pill.next { background: var(--next); }
    .status-pill.rejected { background: var(--rejected); }
    .aside h2 {
      margin: 12px 0 8px;
      font-size: 19px;
    }
    .aside p {
      color: #34373c;
      line-height: 1.45;
      font-size: 14px;
    }
    .aside ul {
      padding-left: 20px;
      margin: 8px 0 16px;
    }
    .aside li {
      margin: 7px 0;
      font-size: 13px;
      line-height: 1.38;
    }
    .aside a {
      color: #1f6fb2;
      text-decoration: none;
      word-break: break-word;
    }
    .aside a:hover { text-decoration: underline; }
    .meta {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }
    .legend {
      display: grid;
      gap: 7px;
      margin-top: 14px;
      font-size: 12px;
    }
    .legend-row {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
      background: var(--unknown);
    }
    .dot.done { background: var(--done); }
    .dot.current { background: var(--current); }
    .dot.watch { background: var(--watch); }
    .dot.next { background: var(--next); }
    .dot.rejected { background: var(--rejected); }
    .error {
      color: #9b3e3e;
      font-weight: 650;
    }
    @media (max-width: 980px) {
      .app { grid-template-columns: 1fr; }
      .aside { height: auto; border-left: 0; border-top: 1px solid var(--line); }
      .canvas-wrap { height: 62vh; }
      header { align-items: flex-start; flex-direction: column; }
      .toolbar { justify-content: flex-start; }
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="main">
      <header>
        <div>
          <h1 id="title">进展思维导图</h1>
          <div class="subtitle" id="subtitle">正在加载...</div>
        </div>
        <div class="toolbar">
          <button id="expand">全部展开</button>
          <button id="collapse">折叠低层级</button>
          <button id="refresh">刷新</button>
        </div>
      </header>
      <div class="canvas-wrap">
        <svg id="map" width="1200" height="720" role="img" aria-label="进展思维导图"></svg>
      </div>
    </div>
    <aside class="aside">
      <div class="meta" id="meta">正在等待数据。</div>
      <div id="details"></div>
      <div class="legend" id="legend"></div>
    </aside>
  </div>
  <script>
    const svg = document.getElementById('map');
    const details = document.getElementById('details');
    const meta = document.getElementById('meta');
    const legendEl = document.getElementById('legend');
    const collapsed = new Set();
    let data = null;
    let selectedId = null;
    let lastMtime = 0;

    const statusClass = status => ['done', 'current', 'watch', 'next', 'rejected'].includes(status) ? status : 'unknown';
    const statusLabel = status => ({
      done: '已完成',
      current: '当前',
      watch: '关注',
      next: '下一步',
      rejected: '否决',
      unknown: '未知'
    })[statusClass(status)] || '未知';

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function wrapText(text, maxChars) {
      const words = String(text || '').split(/\s+/);
      const lines = [];
      let line = '';
      for (const word of words) {
        const next = line ? line + ' ' + word : word;
        if (next.length > maxChars && line) {
          lines.push(line);
          line = word;
        } else {
          line = next;
        }
      }
      if (line) lines.push(line);
      return lines.slice(0, 3);
    }

    function visibleChildren(node) {
      return collapsed.has(node.id) ? [] : (node.children || []);
    }

    function layout(root) {
      let leaf = 0;
      const nodes = [];
      const links = [];
      function place(node, depth, parent) {
        const kids = visibleChildren(node);
        const startLeaf = leaf;
        let y;
        if (kids.length === 0) {
          y = leaf++;
        } else {
          for (const child of kids) {
            place(child, depth + 1, node);
          }
          y = (startLeaf + leaf - 1) / 2;
        }
        const item = {
          node,
          depth,
          x: 80 + depth * 285,
          y: 70 + y * 88,
          parent
        };
        nodes.push(item);
        if (parent) links.push({ source: parent, target: item });
        return item;
      }
      nodes.length = 0;
      links.length = 0;
      place(root, 0, null);
      const byId = new Map(nodes.map(n => [n.node.id, n]));
      links.length = 0;
      for (const item of nodes) {
        if (item.parent) links.push({ source: byId.get(item.parent.id), target: item });
      }
      return { nodes, links, width: 180 + Math.max(...nodes.map(n => n.x)) + 240, height: 130 + Math.max(...nodes.map(n => n.y)) };
    }

    function render() {
      if (!data || !data.root) return;
      const { nodes, links, width, height } = layout(data.root);
      svg.setAttribute('width', Math.max(1100, width));
      svg.setAttribute('height', Math.max(680, height));
      svg.innerHTML = '';

      for (const link of links) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const sx = link.source.x + 220;
        const sy = link.source.y + 28;
        const tx = link.target.x;
        const ty = link.target.y + 28;
        const mid = (sx + tx) / 2;
        path.setAttribute('d', `M ${sx} ${sy} C ${mid} ${sy}, ${mid} ${ty}, ${tx} ${ty}`);
        path.setAttribute('class', 'link');
        svg.appendChild(path);
      }

      for (const item of nodes) {
        const node = item.node;
        const status = statusClass(node.status);
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', `node ${status}${node.id === selectedId ? ' selected' : ''}`);
        g.setAttribute('transform', `translate(${item.x},${item.y})`);
        g.style.cursor = 'pointer';
        g.addEventListener('click', () => {
          selectedId = node.id;
          showDetails(node);
          render();
        });
        g.addEventListener('dblclick', () => {
          if ((node.children || []).length) {
            collapsed.has(node.id) ? collapsed.delete(node.id) : collapsed.add(node.id);
            render();
          }
        });

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('width', '230');
        rect.setAttribute('height', '64');
        g.appendChild(rect);

        const badge = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        badge.setAttribute('class', `badge ${status}`);
        badge.setAttribute('x', '10');
        badge.setAttribute('y', '8');
        badge.setAttribute('width', Math.max(50, String(node.status).length * 8 + 14));
        badge.setAttribute('height', '18');
        badge.setAttribute('rx', '9');
        g.appendChild(badge);

        const badgeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        badgeText.setAttribute('class', 'status');
        badgeText.setAttribute('x', '18');
        badgeText.setAttribute('y', '21');
        badgeText.textContent = statusLabel(node.status);
        g.appendChild(badgeText);

        const lines = wrapText(node.label, 24);
        lines.forEach((line, idx) => {
          const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          t.setAttribute('x', '12');
          t.setAttribute('y', String(43 + idx * 15));
          t.textContent = line;
          g.appendChild(t);
        });

        if ((node.children || []).length) {
          const mark = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          mark.setAttribute('x', '208');
          mark.setAttribute('y', '22');
          mark.textContent = collapsed.has(node.id) ? '+' : '-';
          mark.style.fontWeight = '700';
          g.appendChild(mark);
        }
        svg.appendChild(g);
      }

      if (!selectedId && data.root) selectedId = data.root.id;
      const selected = findNode(data.root, selectedId) || data.root;
      showDetails(selected);
    }

    function findNode(node, id) {
      if (!node) return null;
      if (node.id === id) return node;
      for (const child of node.children || []) {
        const found = findNode(child, id);
        if (found) return found;
      }
      return null;
    }

    function showDetails(node) {
      const status = statusClass(node.status);
      const metrics = (node.metrics || []).map(m => `<li>${escapeHtml(m)}</li>`).join('');
      const sections = (node.sections || []).map(section => {
        const title = escapeHtml(section.title || 'Notes');
        const items = (section.items || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
        return `<h3>${title}</h3>${items ? `<ul>${items}</ul>` : ''}`;
      }).join('');
      const links = (node.links || []).map(l => `<li><a href="/open/${encodeURI(l)}" target="_blank">${escapeHtml(l)}</a></li>`).join('');
      details.innerHTML = `
        <span class="status-pill ${status}">${escapeHtml(statusLabel(node.status))}</span>
        <h2>${escapeHtml(node.label)}</h2>
        <p>${escapeHtml(node.summary)}</p>
        ${metrics ? `<h3>关键记录</h3><ul>${metrics}</ul>` : ''}
        ${sections}
        ${links ? `<h3>相关文件</h3><ul>${links}</ul>` : ''}
        ${(node.children || []).length ? '<p class="meta">在地图里双击这个节点，可以折叠或展开它。</p>' : ''}
      `;
    }

    function renderLegend() {
      const legend = data?.legend || {};
      const rows = Object.entries(legend).map(([status, text]) => {
        const cls = statusClass(status);
        return `<div class="legend-row"><span class="dot ${cls}"></span><b>${escapeHtml(statusLabel(status))}</b><span>${escapeHtml(text)}</span></div>`;
      }).join('');
      legendEl.innerHTML = rows ? `<h3>图例</h3>${rows}` : '';
    }

    async function load() {
      try {
        const res = await fetch('/api/mindmap?ts=' + Date.now());
        const payload = await res.json();
        if (!res.ok || payload.error) throw new Error(payload.error || 'load failed');
        data = payload;
        const pageTitle = payload.title || '进展思维导图';
        document.title = pageTitle;
        document.getElementById('title').textContent = pageTitle;
        svg.setAttribute('aria-label', pageTitle);
        document.getElementById('subtitle').textContent = payload.subtitle || '';
        const changed = payload._mtime !== lastMtime;
        lastMtime = payload._mtime;
        const stamp = new Date((payload._mtime || 0) * 1000).toLocaleString();
        meta.innerHTML = `更新时间：${escapeHtml(payload.updated_at || 'unknown')}<br>数据文件修改时间：${escapeHtml(stamp)}<br>数据来源：${escapeHtml(payload._source || '')}`;
        renderLegend();
        if (changed || !svg.childNodes.length) render();
      } catch (err) {
        meta.innerHTML = `<span class="error">思维导图加载错误：${escapeHtml(err.message)}</span>`;
      }
    }

    document.getElementById('refresh').addEventListener('click', load);
    document.getElementById('expand').addEventListener('click', () => { collapsed.clear(); render(); });
    document.getElementById('collapse').addEventListener('click', () => {
      collapsed.clear();
      function visit(node, depth) {
        if (depth >= 2) collapsed.add(node.id);
        for (const child of node.children || []) visit(child, depth + 1);
      }
      if (data?.root) visit(data.root, 0);
      render();
    });

    load();
    setInterval(load, 2000);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
