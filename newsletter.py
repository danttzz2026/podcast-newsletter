"""HTML email newsletter formatting."""

import re
from datetime import datetime


def markdown_to_html(md: str) -> str:
    """Simple markdown to HTML converter for newsletter content."""
    lines = md.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Headers
        if stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h3 style="color:#1a1a2e;margin:16px 0 8px 0;font-size:15px;">{stripped[3:]}</h3>')
        # Bullet points
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append('<ul style="margin:4px 0;padding-left:20px;">')
                in_list = True
            bullet_content = stripped[2:]
            # Bold text
            bullet_content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", bullet_content)
            html_lines.append(f'<li style="margin:4px 0;color:#333;font-size:14px;line-height:1.5;">{bullet_content}</li>')
        # Regular text
        elif stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            # Bold text
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            # Italic text
            text = re.sub(r'"(.+?)"', r'<em>"\1"</em>', text)
            html_lines.append(f'<p style="margin:4px 0;color:#333;font-size:14px;line-height:1.6;">{text}</p>')

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def format_newsletter(summaries: list[dict]) -> str:
    """
    Format all episode summaries into a complete HTML email newsletter.
    Groups episodes by category.
    """
    today = datetime.now().strftime("%B %d, %Y")
    episode_count = len(summaries)

    # Group by category
    categories = {}
    for s in summaries:
        cat = s["podcast_category"]
        categories.setdefault(cat, []).append(s)

    # Category display order
    cat_order = ["Core", "VC", "AI", "Tech/Business", "Markets", "Other"]
    cat_colors = {
        "Core": "#6C63FF",
        "VC": "#00B4D8",
        "AI": "#FF6B6B",
        "Tech/Business": "#4CAF50",
        "Markets": "#FF9800",
        "Other": "#9E9E9E",
    }

    # Build episode cards
    episodes_html = ""
    for cat in cat_order:
        if cat not in categories:
            continue
        color = cat_colors.get(cat, "#666")
        episodes_html += f'''
        <tr><td style="padding:24px 0 8px 0;">
            <span style="background:{color};color:white;padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;letter-spacing:0.5px;">{cat.upper()}</span>
        </td></tr>
        '''

        for s in categories[cat]:
            summary_html = markdown_to_html(s["summary"])
            link_html = f'<a href="{s["link"]}" style="color:#6C63FF;text-decoration:none;font-size:13px;">Listen to episode →</a>' if s["link"] else ""

            episodes_html += f'''
        <tr><td style="padding:12px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:white;border-radius:12px;border:1px solid #e8e8e8;">
                <tr><td style="padding:20px 24px;">
                    <p style="margin:0 0 4px 0;font-size:12px;color:#888;font-weight:500;">{s["podcast_name"]} · {s["published"]}</p>
                    <h2 style="margin:0 0 12px 0;font-size:18px;color:#1a1a2e;line-height:1.3;">{s["episode_title"]}</h2>
                    {summary_html}
                    <p style="margin:16px 0 0 0;">{link_html}</p>
                </td></tr>
            </table>
        </td></tr>
            '''

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f7;">
<tr><td align="center" style="padding:20px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

    <!-- Header -->
    <tr><td style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:32px 24px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="margin:0;color:white;font-size:24px;font-weight:700;">🎙️ Your Daily Pod Digest</h1>
        <p style="margin:8px 0 0 0;color:#a8a8b3;font-size:14px;">{today} · {episode_count} new episode{"s" if episode_count != 1 else ""}</p>
    </td></tr>

    <!-- Body -->
    <tr><td style="background:#f5f5f7;padding:8px 0;">
        <table width="100%" cellpadding="0" cellspacing="0">
            {episodes_html}
        </table>
    </td></tr>

    <!-- Footer -->
    <tr><td style="padding:24px;text-align:center;border-top:1px solid #e8e8e8;">
        <p style="margin:0;color:#999;font-size:12px;">Summaries generated by Claude · Built with ❤️</p>
    </td></tr>

</table>
</td></tr>
</table>
</body>
</html>'''

    return html
