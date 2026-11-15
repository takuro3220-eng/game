#!/usr/bin/env python3
"""Apply repeatable iPhone presentation patches to the unpacked Godot v10 build."""
from pathlib import Path
import sys

ROOT = Path("game")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one occurrence, found {count}: {old}")
    return text.replace(old, new, 1)

def prepare() -> None:
    source = ROOT / "scripts" / "world_builder.gd"
    data = source.read_text(encoding="utf-8")
    settings = [
        ('Color("568dbf")', 'Color("385f82")'),
        ('Color("c2e1e6")', 'Color("89adb5")'),
        ('Color("abc59a")', 'Color("738576")'),
        ('Color("b0c7bd")', 'Color("819891")'),
        ('e.fog_density = 0.006', 'e.fog_density = 0.0045'),
        ('sun.light_energy = 1.25', 'sun.light_energy = 0.82'),
        ('sun.light_energy = 1.15 + sin(elapsed * 0.002) * 0.12',
         'sun.light_energy = 0.83 + sin(elapsed * 0.002) * 0.09'),
    ]
    for old, new in settings:
        data = replace_once(data, old, new, "lighting")
    data = replace_once(
        data,
        "    e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY\n",
        "    e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY\n"
        '    e.ambient_light_sky_contribution = 0.55\n'
        '    e.ambient_light_color = Color("778b8c")\n'
        "    e.ambient_light_energy = 0.38\n",
        "ambient lighting",
    )
    source.write_text(data, encoding="utf-8")
    project = ROOT / "project.godot"
    conf = project.read_text(encoding="utf-8")
    conf = replace_once(
        conf,
        'window/stretch/mode="canvas_items"\n',
        'window/stretch/mode="canvas_items"\nwindow/stretch/aspect="expand"\n',
        "responsive viewport",
    )
    project.write_text(conf, encoding="utf-8")
    print("Applied softer lighting and responsive landscape viewport settings.")

def finalize() -> None:
    exported = ROOT / "build" / "web" / "index.html"
    html = exported.read_text(encoding="utf-8")
    assert "</head>" in html and "</body>" in html, "Godot HTML shell changed"
    if 'id="astra-rotate"' in html:
        print("Portrait guidance already installed.")
        return
    meta = """<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ASTRA LEGENDS">
<meta name="theme-color" content="#111c2a">
"""
    overlay = """
<style id="astra-mobile-css">
  html, body { overscroll-behavior: none; }
  #astra-rotate {
    display: none; position: fixed; inset: 0; z-index: 2147483647;
    box-sizing: border-box; padding: 32px 30px;
    background: radial-gradient(circle at 50% 30%, #34546b, #0a1421 65%);
    color: #f5ecd9; text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    align-items: center; justify-content: center; flex-direction: column; gap: 13px;
  }
  #astra-rotate .rotate-icon { font-size: 54px; line-height: 1.3; }
  #astra-rotate h2 { font-size: clamp(22px, 6vw, 30px); margin: 0; font-weight: 750; }
  #astra-rotate p { font-size: 15px; line-height: 1.7; margin: 0; max-width: 390px; color: #d8e2e6; }
  #astra-rotate .small { font-size: 12px; color: #a6b8c0; margin-top: 6px; }
  @media (orientation: portrait) and (max-width: 900px) {
    #astra-rotate { display: flex; }
  }
</style>
<div id="astra-rotate" role="note" aria-label="横画面でプレイしてください">
  <div class="rotate-icon" aria-hidden="true">↻ ▱</div>
  <h2>iPhoneを横向きにしてください</h2>
  <p>ASTRA LEGENDSは横画面専用です。画面の向きを固定している場合は、コントロールセンターで縦向きロックを解除してください。</p>
  <p class="small">URLバーを隠すには、Safariで開き「共有」→「ホーム画面に追加」→「Webアプリとして開く」を選択します。</p>
</div>
"""
    html = html.replace("</head>", meta + "</head>", 1)
    html = html.replace("</body>", overlay + "</body>", 1)
    exported.write_text(html, encoding="utf-8")
    assert 'id="astra-rotate"' in exported.read_text(encoding="utf-8")
    print("Applied iPhone portrait guidance, PWA display metadata.")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("prepare", "finalize"):
        raise SystemExit("Usage: mobile_finish.py prepare|finalize")
    globals()[sys.argv[1]]()
