import ast
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRODUCE_DIR = ROOT / "reproduce"
CONVERSATION_DIR = ROOT / "conversation"


def extract_messages(py_path: Path):
    source = py_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    found = []

    class Visitor(ast.NodeVisitor):
        def visit_keyword(self, node):
            if node.arg == "messages":
                try:
                    value = ast.literal_eval(node.value)
                    if isinstance(value, list):
                        found.append(value)
                except Exception:
                    pass
            self.generic_visit(node)

    Visitor().visit(tree)

    return max(found, key=len) if found else []


def text_from_content(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    # 通常表示では邪魔なので省略
                    continue
                else:
                    parts.append(str(block))
            else:
                parts.append(str(block))
        return "\n\n".join(parts)

    return str(content)


def message_html(message, index):
    role = message.get("role", "unknown")
    text = text_from_content(message.get("content", ""))

    role_label = {
        "user": "User",
        "assistant": "Assistant",
        "system": "System",
    }.get(role, role)

    return f"""
<article class="message {html.escape(role)}">
  <div class="meta">
    <span class="role">{html.escape(role_label)}</span>
    <span class="num">#{index}</span>
  </div>
  <div class="body">{html.escape(text)}</div>
</article>
"""


def build_conversation_page(title, messages):
    body = "\n".join(
        message_html(message, i + 1)
        for i, message in enumerate(messages)
    )

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.7;
      margin: 0;
      background: #f6f7f9;
      color: #222;
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 32px 20px 80px;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    .back {{
      margin-bottom: 24px;
    }}
    .message {{
      white-space: pre-wrap;
      margin: 20px 0;
      padding: 18px 20px;
      border-radius: 16px;
      border: 1px solid #ddd;
      background: white;
      box-shadow: 0 6px 18px rgba(0,0,0,.05);
    }}
    .message.user {{
      border-left: 8px solid #2563eb;
      background: #eff6ff;
    }}
    .message.assistant {{
      border-left: 8px solid #16a34a;
      background: #f0fdf4;
    }}
    .meta {{
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
      font-weight: 700;
    }}
    .num {{
      color: #777;
      font-weight: 400;
    }}
    .body {{
      font-size: 16px;
    }}
  </style>
</head>
<body>
  <main>
    <div class="back"><a href="./">← Conversation index</a></div>
    <h1>{html.escape(title)}</h1>
    <p>{len(messages)} messages</p>
    {body}
  </main>
</body>
</html>
"""


def build_index(pages):
    items = "\n".join(
        f'<li><a href="{html.escape(filename)}">{html.escape(title)}</a> '
        f'<span>({count} messages)</span></li>'
        for title, filename, count in pages
    )

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>Conversation Viewer</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.7;
      margin: 0;
      background: #f6f7f9;
      color: #222;
    }}
    main {{
      max-width: 900px;
      margin: 0 auto;
      padding: 32px 20px 80px;
    }}
    li {{
      margin: 12px 0;
      padding: 14px 16px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 14px rgba(0,0,0,.05);
    }}
    span {{
      color: #666;
    }}
  </style>
</head>
<body>
  <main>
    <p><a href="../">← Back to top</a></p>
    <h1>Conversation Viewer</h1>
    <p>Readable user / assistant conversations extracted from reproduce scripts.</p>
    <ul>
      {items}
    </ul>
  </main>
</body>
</html>
"""


def main():
    CONVERSATION_DIR.mkdir(exist_ok=True)

    pages = []

    for py_path in sorted(REPRODUCE_DIR.glob("*.py")):
        messages = extract_messages(py_path)

        if not messages:
            continue

        html_name = py_path.stem.replace(" ", "_") + ".html"
        out_path = CONVERSATION_DIR / html_name

        out_path.write_text(
            build_conversation_page(py_path.name, messages),
            encoding="utf-8"
        )

        pages.append((py_path.name, html_name, len(messages)))

    (CONVERSATION_DIR / "index.html").write_text(
        build_index(pages),
        encoding="utf-8"
    )

    print(f"Generated {len(pages)} conversation page(s).")


if __name__ == "__main__":
    main()