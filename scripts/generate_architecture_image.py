from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "project_architecture.png"

FONT_REG = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
if not FONT_REG.exists():
    FONT_REG = Path(r"C:\Windows\Fonts\msyh.ttc")
if not FONT_BOLD.exists():
    FONT_BOLD = FONT_REG

W, H = 2400, 1450
img = Image.new("RGB", (W, H), "#f8fafc")
d = ImageDraw.Draw(img)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


F_TITLE = font(52, True)
F_SUB = font(24)
F_LAYER = font(28, True)
F_BOX_TITLE = font(28, True)
F_TEXT = font(22)
F_SMALL = font(19)
F_TAG = font(18, True)

C_TEXT = "#111827"
C_MUTED = "#4b5563"
C_LINE = "#64748b"
C_USER = ("#f4f4f5", "#71717a")
C_FRONT = ("#ecfeff", "#0891b2")
C_BACK = ("#eef2ff", "#4f46e5")
C_AI = ("#f0fdf4", "#16a34a")
C_DATA = ("#fff7ed", "#f97316")
C_EXT = ("#fdf2f8", "#db2777")


def rounded_box(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    fill: str,
    outline: str,
    width: int = 3,
    radius: int = 24,
) -> None:
    d.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def label(
    text: str,
    xy: tuple[float, float],
    fnt: ImageFont.FreeTypeFont,
    fill: str = C_TEXT,
    anchor: str = "mm",
) -> None:
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def wrap_text(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        current = ""
        for ch in para:
            trial = current + ch
            bbox = d.textbbox((0, 0), trial, font=fnt)
            if bbox[2] - bbox[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def draw_text_block(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    items: list[str],
    fill: str,
    outline: str,
) -> None:
    rounded_box(x, y, x + w, y + h, fill, outline, width=2, radius=18)
    label(title, (x + w / 2, y + 34), F_BOX_TITLE, C_TEXT)
    yy = y + 68
    for item in items:
        lines = wrap_text(item, F_SMALL, w - 46)
        for idx, line in enumerate(lines):
            d.text(
                (x + 24, yy),
                ("• " if idx == 0 else "  ") + line,
                font=F_SMALL,
                fill=C_MUTED,
            )
            yy += 27
        yy += 1


def arrow(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: str = C_LINE,
    width: int = 4,
    text: str | None = None,
    text_offset: int = 0,
) -> None:
    d.line([x1, y1, x2, y2], fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 16
    p1 = (
        x2 - size * math.cos(ang) + size * 0.55 * math.sin(ang),
        y2 - size * math.sin(ang) - size * 0.55 * math.cos(ang),
    )
    p2 = (
        x2 - size * math.cos(ang) - size * 0.55 * math.sin(ang),
        y2 - size * math.sin(ang) + size * 0.55 * math.cos(ang),
    )
    d.polygon([(x2, y2), p1, p2], fill=color)
    if text:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + text_offset
        bbox = d.textbbox((0, 0), text, font=F_TAG)
        pad_x, pad_y = 12, 7
        d.rounded_rectangle(
            [
                mx - (bbox[2] - bbox[0]) / 2 - pad_x,
                my - (bbox[3] - bbox[1]) / 2 - pad_y,
                mx + (bbox[2] - bbox[0]) / 2 + pad_x,
                my + (bbox[3] - bbox[1]) / 2 + pad_y,
            ],
            radius=12,
            fill="#ffffff",
            outline="#cbd5e1",
            width=1,
        )
        label(text, (mx, my - 1), F_TAG, C_MUTED)


def polyline_arrow(
    points: list[tuple[int, int]],
    color: str = C_LINE,
    width: int = 4,
    text: str | None = None,
    text_xy: tuple[int, int] | None = None,
) -> None:
    d.line(points, fill=color, width=width, joint="curve")
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 16
    p1 = (
        x2 - size * math.cos(ang) + size * 0.55 * math.sin(ang),
        y2 - size * math.sin(ang) - size * 0.55 * math.cos(ang),
    )
    p2 = (
        x2 - size * math.cos(ang) - size * 0.55 * math.sin(ang),
        y2 - size * math.sin(ang) + size * 0.55 * math.cos(ang),
    )
    d.polygon([(x2, y2), p1, p2], fill=color)
    if text and text_xy:
        tx, ty = text_xy
        bbox = d.textbbox((0, 0), text, font=F_TAG)
        pad_x, pad_y = 12, 7
        d.rounded_rectangle(
            [
                tx - (bbox[2] - bbox[0]) / 2 - pad_x,
                ty - (bbox[3] - bbox[1]) / 2 - pad_y,
                tx + (bbox[2] - bbox[0]) / 2 + pad_x,
                ty + (bbox[3] - bbox[1]) / 2 + pad_y,
            ],
            radius=12,
            fill="#ffffff",
            outline="#cbd5e1",
            width=1,
        )
        label(text, (tx, ty - 1), F_TAG, C_MUTED)


# Title
d.text((90, 58), "基于大语言模型的智能新闻摘要与协同互动系统", font=F_TITLE, fill=C_TEXT)
d.text(
    (92, 125),
    "项目架构图 | Vue 3 前端 + FastAPI 后端 + 独立 AI 服务 + MySQL + RSS 爬虫",
    font=F_SUB,
    fill=C_MUTED,
)
d.line([90, 170, W - 90, 170], fill="#cbd5e1", width=2)

lanes = [
    (90, 215, 330, 260, "用户层", C_USER),
    (400, 215, 820, 260, "前端表现层", C_FRONT),
    (890, 215, 1460, 260, "后端业务层", C_BACK),
    (1530, 215, 1930, 260, "AI 能力层", C_AI),
    (2000, 215, 2310, 260, "数据与外部资源", C_DATA),
]
for x1, y1, x2, y2, txt, col in lanes:
    rounded_box(x1, y1, x2, y2, col[0], col[1], width=2, radius=18)
    label(txt, ((x1 + x2) / 2, (y1 + y2) / 2 - 1), F_LAYER, C_TEXT)

rounded_box(105, 470, 315, 680, C_USER[0], C_USER[1], 3, 24)
label("用户", (210, 515), F_BOX_TITLE)
for i, t in enumerate(["普通用户", "审核编辑", "管理员"]):
    label(t, (210, 565 + i * 38), F_TEXT, C_MUTED)

rounded_box(400, 315, 820, 850, C_FRONT[0], C_FRONT[1], 4, 28)
label("frontend", (610, 360), F_BOX_TITLE)
label("Vue 3 + Vite + TypeScript + Element Plus", (610, 397), F_SMALL, C_MUTED)
frontend_modules = [
    ("页面视图", ["首页 / 新闻详情 / 时间线", "AI 生成 / 社区 / 个人中心 / 管理后台"]),
    ("状态与路由", ["Pinia Store / Vue Router", "主题与导航状态"]),
    ("API 请求层", ["Axios 封装 / Token 注入", "统一错误处理"]),
]
y = 435
for title, items in frontend_modules:
    draw_text_block(430, y, 360, 124, title, items, "#ffffff", "#67e8f9")
    y += 136

rounded_box(890, 305, 1460, 960, C_BACK[0], C_BACK[1], 4, 28)
label("backend", (1175, 350), F_BOX_TITLE)
label("FastAPI + PyMySQL | /api/*", (1175, 387), F_SMALL, C_MUTED)
backend_boxes = [
    (925, 430, "认证与用户", ["auth / user", "profile / 上传资源"]),
    (1195, 430, "新闻业务", ["news / interaction", "评论 / 收藏 / 浏览"]),
    (925, 620, "社区协同", ["community", "帖子 / 评论 / AI 会话"]),
    (1195, 620, "事件脉络", ["timeline", "热点主题 / 聚类"]),
    (925, 810, "管理后台", ["admin", "系统配置 / 日志 / 备份"]),
    (1195, 810, "AI 网关", ["ai / editor_agent", "agent_analysis / SSE"]),
]
for x, y, title, items in backend_boxes:
    draw_text_block(x, y, 230, 130, title, items, "#ffffff", "#a5b4fc")

rounded_box(1530, 355, 1930, 855, C_AI[0], C_AI[1], 4, 28)
label("ai-service", (1730, 400), F_BOX_TITLE)
label("FastAPI 独立 AI 服务 | /ai/*", (1730, 437), F_SMALL, C_MUTED)
ai_blocks = [
    ("AI 接口", ["generate / extract / check", "evidence / timeline / polish / chat"]),
    ("AI 编排", ["Prompt Builder", "LLM Client / Parser / Task Service"]),
    ("运行模式", ["Mock 输出", "真实大模型配置"]),
]
y = 475
for title, items in ai_blocks:
    draw_text_block(1560, y, 340, 112, title, items, "#ffffff", "#86efac")
    y += 126

rounded_box(2000, 330, 2310, 980, C_DATA[0], C_DATA[1], 4, 28)
label("MySQL 8.0", (2155, 375), F_BOX_TITLE)
label("llm_news_system", (2155, 412), F_SMALL, C_MUTED)
data_items = [
    ("核心数据", "user / news / category / topic"),
    ("互动数据", "comment / like / favorite / history"),
    ("社区数据", "post / post_comment / AI session"),
    ("AI 记录", "ai_generate_record / prompt / config"),
    ("运维扩展", "crawl_log / upload_file / timeline"),
    ("初始化脚本", "schema.sql / seed.sql / migrations"),
]
y = 460
for title, desc in data_items:
    rounded_box(2030, y, 2280, y + 70, "#ffffff", "#fdba74", 2, 16)
    d.text((2050, y + 12), title, font=F_TEXT, fill=C_TEXT)
    d.text((2050, y + 42), desc, font=F_SMALL, fill=C_MUTED)
    y += 82

rounded_box(1530, 1010, 1930, 1240, C_EXT[0], C_EXT[1], 3, 24)
label("外部数据与模型", (1730, 1053), F_BOX_TITLE)
d.text((1565, 1098), "• 光明网 RSS 新闻源", font=F_TEXT, fill=C_MUTED)
d.text((1565, 1134), "• DeepSeek / 智谱等真实大模型 API", font=F_TEXT, fill=C_MUTED)
d.text((1565, 1170), "• AI 配置可由后端管理后台维护", font=F_TEXT, fill=C_MUTED)

rounded_box(890, 1050, 1460, 1240, "#ffffff", "#db2777", 3, 24)
label("scripts/crawlers 新闻爬虫", (1175, 1095), F_BOX_TITLE)
d.text((930, 1140), "• RSS 增量抓取 / 正文解析", font=F_TEXT, fill=C_MUTED)
d.text((930, 1176), "• 写入 news、news_topic、crawl_log 等表", font=F_TEXT, fill=C_MUTED)

rounded_box(1030, 990, 1320, 1038, "#fafafa", "#94a3b8", 2, 18)
label("Mock fallback：数据库异常或本地演示", (1175, 1014), F_SMALL, C_MUTED)

arrow(315, 575, 400, 575, text="访问系统")
arrow(820, 575, 890, 575, text="HTTP /api/*")
arrow(1460, 610, 1530, 610, text="HTTP /ai/*")
polyline_arrow(
    [(1460, 895), (1500, 895), (1500, 945), (2000, 945)],
    text="读写业务数据",
    text_xy=(1715, 945),
)
arrow(1930, 620, 2000, 620, text="AI 记录/配置", text_offset=-36)
arrow(1730, 1010, 1730, 855, color="#16a34a", text="模型调用 / Mock")
arrow(1460, 1145, 2000, 860, color="#db2777", text="爬虫入库")
arrow(1530, 1120, 1460, 1120, color="#db2777", text="RSS 源")
arrow(1175, 960, 1175, 990, color="#94a3b8")

rounded_box(110, 990, 790, 1288, "#ffffff", "#cbd5e1", 2, 24)
label("核心链路", (450, 1034), F_BOX_TITLE)
callouts = [
    "前端只访问 backend，不直接访问数据库或 AI 服务。",
    "backend 统一处理认证、业务逻辑、数据访问和 AI 调用。",
    "ai-service 独立承载摘要、抽取、校验、润色、时间线等智能能力。",
    "RSS 爬虫离线或定时运行，抓取新闻后写入 MySQL。",
]
y = 1080
for c in callouts:
    lines = wrap_text(c, F_TEXT, 610)
    for idx, line in enumerate(lines):
        d.text((145, y), ("• " if idx == 0 else "  ") + line, font=F_TEXT, fill=C_MUTED)
        y += 34

rounded_box(2000, 1015, 2310, 1240, "#ffffff", "#cbd5e1", 2, 24)
label("图例", (2155, 1058), F_BOX_TITLE)
legend = [
    ("#64748b", "主业务请求"),
    ("#16a34a", "AI 能力调用"),
    ("#db2777", "外部数据输入"),
    ("#f97316", "数据存储"),
]
ly = 1100
for color, text in legend:
    d.line([2050, ly + 12, 2110, ly + 12], fill=color, width=5)
    d.polygon([(2110, ly + 12), (2095, ly + 3), (2095, ly + 21)], fill=color)
    d.text((2130, ly), text, font=F_TEXT, fill=C_MUTED)
    ly += 38

d.line([90, 1320, W - 90, 1320], fill="#cbd5e1", width=2)
d.text(
    (90, 1350),
    "部署端口：frontend http://localhost:5173 | backend http://127.0.0.1:8000 | ai-service http://127.0.0.1:8001 | MySQL 127.0.0.1:3306",
    font=F_SMALL,
    fill=C_MUTED,
)
d.text((90, 1384), "生成文件：docs/project_architecture.png", font=F_SMALL, fill="#64748b")

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, quality=95)
print(OUT)
