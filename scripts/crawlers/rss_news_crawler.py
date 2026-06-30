"""RSS 新闻爬虫（DB3.5 增量版）

特性：
- 优先按 source_url 去重
- source_url 不存在时按 title 去重
- 支持 dry-run / max-items / source / cleanup-days
- 每个 RSS 源写入 crawl_log
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import feedparser
import pymysql
from bs4 import BeautifulSoup, UnicodeDammit
from dateutil import parser as date_parser
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = PROJECT_ROOT / "backend" / ".env"

RSS_SOURCES: dict[str, list[dict[str, str]]] = {
    "china_news": [
        {
            "name": "中国新闻网-国内",
            "url": "https://www.chinanews.com.cn/rss/china.xml",
            "category_code": "politics",
            "source_name": "中国新闻网",
        },
        {
            "name": "中国新闻网-国际",
            "url": "https://www.chinanews.com.cn/rss/world.xml",
            "category_code": "world",
            "source_name": "中国新闻网",
        },
        {
            "name": "中国新闻网-社会",
            "url": "https://www.chinanews.com.cn/rss/society.xml",
            "category_code": "society",
            "source_name": "中国新闻网",
        },
        {
            "name": "中国新闻网-财经",
            "url": "https://www.chinanews.com.cn/rss/finance.xml",
            "category_code": "finance",
            "source_name": "中国新闻网",
        },
        {
            "name": "中国新闻网-体育",
            "url": "https://www.chinanews.com.cn/rss/sports.xml",
            "category_code": "sports",
            "source_name": "中国新闻网",
        },
        {
            "name": "中国新闻网-科技",
            "url": "https://www.chinanews.com.cn/rss/it.xml",
            "category_code": "technology",
            "source_name": "中国新闻网",
        },
        {
            "name": "中国新闻网-娱乐",
            "url": "https://www.chinanews.com.cn/rss/ent.xml",
            "category_code": "entertainment",
            "source_name": "中国新闻网",
        },
    ],
    "people": [
        {
            "name": "人民网-时政",
            "url": "http://www.people.com.cn/rss/politics.xml",
            "category_code": "politics",
            "source_name": "人民网",
        },
        {
            "name": "人民网-社会",
            "url": "http://www.people.com.cn/rss/society.xml",
            "category_code": "society",
            "source_name": "人民网",
        },
        {
            "name": "人民网-国际",
            "url": "http://www.people.com.cn/rss/world.xml",
            "category_code": "world",
            "source_name": "人民网",
        },
        {
            "name": "人民网-科技",
            "url": "http://www.people.com.cn/rss/it.xml",
            "category_code": "technology",
            "source_name": "人民网",
        },
        {
            "name": "人民网-娱乐",
            "url": "http://www.people.com.cn/rss/ent.xml",
            "category_code": "entertainment",
            "source_name": "人民网",
        },
    ],
}

ENABLE_PEOPLE_RSS = True  # 启用人民网 RSS 源以获得更多数据
DEFAULT_MAX_ITEMS = 10
DEFAULT_SOURCE_MODE = "all"  # 使用所有 RSS 源

logger = logging.getLogger("rss_news_crawler")


@dataclass
class ParsedNewsItem:
    title: str
    summary: str
    content: str
    cover_image: str
    category_id: int
    topic_id: int | None
    source: str
    editor: str
    publish_time: str
    view_count: int
    like_count: int
    comment_count: int
    favorite_count: int
    status: int
    tags: list[str]
    source_url: str | None = None


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_env() -> None:
    if BACKEND_ENV_PATH.exists():
        load_dotenv(BACKEND_ENV_PATH)
    else:
        load_dotenv()


def get_db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "llm_news_system"),
        "user": os.getenv("DB_USER", "llm_news_user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }


def get_source_list(mode: str) -> list[dict[str, str]]:
    sources = list(RSS_SOURCES["china_news"])
    if mode == "all" and ENABLE_PEOPLE_RSS:
        sources.extend(RSS_SOURCES["people"])
    return sources


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


BAD_URL_PREFIX_PATTERNS = [
    r"^\?+",
    r"^？+",
    r"^原文链接[:：]\s*",
    r"^链接[:：]\s*",
    r"^url[:：]\s*",
    r"^URL[:：]\s*",
]

NOISE_KEYWORDS = [
    "责任编辑",
    "责编",
    "版权声明",
    "免责声明",
    "更多精彩",
    "扫一扫",
    "客户端下载",
    "点击进入",
    "上一篇",
    "下一篇",
    "相关阅读",
    "相关推荐",
    "推荐阅读",
    "热门推荐",
    "广告",
    "声明：",
    "本文来源",
    "原文链接",
    "违法和不良信息举报",
]

BOILERPLATE_TERMINATORS = [
    "责任编辑",
    "责编",
    "版权声明",
    "免责声明",
    "相关阅读",
    "相关推荐",
    "推荐阅读",
    "热门推荐",
    "更多精彩",
    "客户端",
    "扫一扫",
    "分享到",
    "参与互动",
    "我要评论",
    "原文链接",
    "本文来源",
    "违法和不良信息举报",
]

MOJIBAKE_MARKERS = [
    "锟",
    "�",
    "Ã",
    "Â",
    "涓",
    "鍥",
    "鏂",
    "绔",
    "缃",
    "璐",
    "鐨",
    "鈥",
]

NOISE_ATTR_KEYWORDS = [
    "side",
    "sidebar",
    "recommend",
    "related",
    "hot",
    "rank",
    "ranking",
    "ad",
    "ads",
    "advert",
    "footer",
    "header",
    "nav",
    "menu",
    "share",
    "comment",
    "comments",
    "qrcode",
    "qr",
    "copyright",
    "breadcrumb",
]

ARTICLE_SELECTORS = [
    "article",
    ".article",
    ".article-content",
    ".article_content",
    ".news-content",
    ".news_content",
    ".content",
    ".main-content",
    "#article",
    "#content",
    "#main-content",
    ".left_zw",
    ".text",
    ".text-content",
    ".detail-content",
    ".post-content",
    "#artibody",
    ".articleBody",
    "#articleContent",
    ".article-con",
    ".article_main",
    ".articleMain",
    ".article-body",
    ".detail_article",
]

BAD_IMAGE_KEYWORDS = [
    "logo",
    "icon",
    "avatar",
    "qrcode",
    "qr",
    "loading",
    "blank",
    "spacer",
    "sprite",
    "default",
    "placeholder",
    "video_default",
    "play",
    "app",
]

# 通用图片特征（RSS 默认图、栏目图、视频默认图）
GENERIC_IMAGE_PATTERNS = [
    r"U\d+P\d+T\d+D\d+F\d+DT\d+\.jpg",  # 中国新闻网通用图格式
    r"/fileftp/",  # 备份/通用图
    r"default",
    r"placeholder",
    r"video",
    r"channel",
    r"category",
]


def normalize_url(raw_url: str | None, base_url: str = "") -> str:
    if not raw_url:
        return ""
    url = html.unescape(str(raw_url)).strip()
    for pattern in BAD_URL_PREFIX_PATTERNS:
        url = re.sub(pattern, "", url, flags=re.IGNORECASE).strip()
    match = re.search(r"https?://[^\s\"'<>]+", url)
    if match:
        url = match.group(0)
    elif base_url:
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


def normalize_image_url(raw_url: str | None, base_url: str = "") -> str:
    url = normalize_url(raw_url, base_url)
    if not url:
        return ""
    lowered = url.lower()
    if lowered.startswith("data:") or any(keyword in lowered for keyword in BAD_IMAGE_KEYWORDS):
        return ""
    if len(url) < 20:
        return ""
    return url


def is_generic_image(image_url: str) -> bool:
    """检查是否是通用/默认图片（RSS 默认图、栏目图、视频默认图等）"""
    if not image_url:
        return True

    url_lower = image_url.lower()

    # 检查关键词
    generic_keywords = [
        "default",
        "placeholder",
        "video_default",
        "logo",
        "icon",
        "avatar",
        "qr",
        "channel",
        "category",
    ]
    for keyword in generic_keywords:
        if keyword in url_lower:
            return True

    # 检查正则模式
    for pattern in GENERIC_IMAGE_PATTERNS:
        if re.search(pattern, url_lower, re.IGNORECASE):
            return True

    return False


def is_video_news(entry: Any, title: str, html_text: str) -> bool:
    """识别是否是视频新闻"""
    video_keywords_in_title = ["视频", "video", "播放", "点播"]

    # 检查标题中是否有明确的视频关键词
    for keyword in video_keywords_in_title:
        if keyword.lower() in title.lower():
            return True

    # 检查 HTML 中是否有视频播放器（更严格的判断）
    if html_text:
        html_lower = html_text.lower()
        
        # 需要同时满足多个条件才认为是视频新闻
        video_indicators = 0
        
        # 有 video 标签或 video 播放器
        if "<video" in html_lower or "video.js" in html_lower or "videojs" in html_lower:
            video_indicators += 1
        
        # 有明确的视频播放器容器
        if "player" in html_lower and ("video" in html_lower or "vjs" in html_lower):
            video_indicators += 1
        
        # 有视频时长或播放按钮
        if "duration" in html_lower and ("video" in html_lower or "player" in html_lower):
            video_indicators += 1
        
        # 需要至少两个指标才判断为视频新闻
        if video_indicators >= 2:
            return True

    return False


def is_noise_text(text: str) -> bool:
    normalized = normalize_whitespace(text)
    if len(normalized) < 15:
        return True
    return any(keyword in normalized for keyword in NOISE_KEYWORDS)


def is_noisy_content(content: str) -> bool:
    if not content:
        return True
    normalized = content.strip()
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    noise_hits = sum(1 for keyword in NOISE_KEYWORDS if keyword in normalized)
    url_count = normalized.count("http://") + normalized.count("https://")
    short_line_count = sum(1 for line in lines if len(line) < 20)
    return (
        len(normalized) < 200
        or noise_hits >= 3
        or url_count >= 3
        or (len(lines) >= 8 and short_line_count / max(len(lines), 1) > 0.55)
    )


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text).split()).strip()


def looks_mojibake(text: str) -> bool:
    if not text:
        return False
    marker_count = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    odd_script_count = len(re.findall(r"[\u0370-\u03ff\u0400-\u052f\u0590-\u05ff\u02c0-\u02ff]", text))
    if "�" in text:
        return True
    if odd_script_count >= 12 and odd_script_count >= max(chinese_count // 5, 8):
        return True
    return marker_count >= 3 and marker_count >= max(chinese_count // 8, 3)


def repair_mojibake(text: str) -> str:
    if not text or not looks_mojibake(text):
        return text
    for source_encoding in ("latin1", "gbk", "cp1252"):
        for target_encoding in ("utf-8", "gb18030"):
            try:
                repaired = text.encode(source_encoding, errors="ignore").decode(target_encoding, errors="ignore")
            except Exception:
                continue
            if repaired and not looks_mojibake(repaired):
                return repaired
    return text


def is_unreadable_article_text(text: str) -> bool:
    normalized = normalize_whitespace(text)
    if not normalized:
        return True
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", normalized))
    visible_count = len(re.findall(r"\S", normalized))
    if looks_mojibake(normalized):
        return True
    if visible_count >= 10 and chinese_count == 0:
        return True
    if visible_count >= 40 and chinese_count < max(visible_count // 12, 12):
        return True
    return False


def cut_boilerplate_tail(text: str) -> str:
    if not text:
        return ""
    earliest = -1
    for keyword in BOILERPLATE_TERMINATORS:
        index = text.find(keyword)
        if index >= 0 and (earliest < 0 or index < earliest):
            earliest = index
    if earliest >= 0:
        text = text[:earliest]
    return text.strip()


def truncate_text(text: str, max_length: int) -> str:
    return text if len(text) <= max_length else text[:max_length].rstrip() + "..."


def parse_datetime(value: Any) -> datetime:
    if not value:
        return datetime.now()
    if hasattr(value, "tm_year"):
        try:
            return datetime(*value[:6])  # type: ignore[index]
        except Exception:
            return datetime.now()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    try:
        return date_parser.parse(str(value))
    except Exception:
        return datetime.now()


def format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def get_column_names(connection: pymysql.connections.Connection, table_name: str) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name AS column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
            """,
            (table_name,),
        )
        rows = cursor.fetchall()
    return {row["column_name"] for row in rows}


def has_column(connection: pymysql.connections.Connection, table_name: str, column_name: str) -> bool:
    return column_name in get_column_names(connection, table_name)


def get_category_map(connection: pymysql.connections.Connection) -> dict[str, int]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, code FROM news_category WHERE status = 1")
        rows = cursor.fetchall()
    category_map = {row["code"]: int(row["id"]) for row in rows}
    required_codes = {"politics", "world", "society", "finance", "sports"}
    missing = required_codes - set(category_map.keys())
    if missing:
        raise RuntimeError(f"新闻分类缺失，请先导入 seed.sql，缺少：{', '.join(sorted(missing))}")
    return category_map


def get_topics(connection: pymysql.connections.Connection) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, topic_name, keyword_list, heat_score FROM news_topic WHERE status = 1 ORDER BY heat_score DESC, id ASC"
        )
        rows = cursor.fetchall()

    topics: list[dict[str, Any]] = []
    for row in rows:
        keywords = row["keyword_list"]
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except json.JSONDecodeError:
                keywords = []
        if not isinstance(keywords, list):
            keywords = []
        topics.append(
            {
                "id": int(row["id"]),
                "topic_name": row["topic_name"],
                "keyword_list": [str(item) for item in keywords],
                "heat_score": int(row["heat_score"] or 0),
            }
        )
    return topics


def match_topic_id(topics: list[dict[str, Any]], title: str, summary: str) -> int | None:
    text = f"{title} {summary}".lower()
    for topic in topics:
        for keyword in topic["keyword_list"]:
            if keyword and keyword.lower() in text:
                return int(topic["id"])
    return None


def build_tags(category_code: str, topic_name: str | None, source_name: str) -> list[str]:
    tags = [category_code, source_name]
    if topic_name:
        tags.insert(1, topic_name)
    result: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if tag and tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def extract_text_block(node: Any) -> str:
    paragraphs: list[str] = []
    for paragraph in node.find_all("p"):
        text = normalize_whitespace(paragraph.get_text(" ", strip=True))
        if text and not is_noise_text(text):
            paragraphs.append(text)

    if not paragraphs:
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if text and not is_noise_text(text):
            paragraphs.append(text)

    unique_paragraphs: list[str] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        if paragraph not in seen:
            seen.add(paragraph)
            unique_paragraphs.append(paragraph)
    return "\n\n".join(unique_paragraphs)


def strip_boilerplate_lines(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_whitespace(raw_line)
        if not line:
            continue
        if any(keyword in line for keyword in BOILERPLATE_TERMINATORS):
            break
        if is_noise_text(line):
            continue
        lines.append(line)
    return cut_boilerplate_tail("\n\n".join(lines))


def remove_noise_nodes(soup: BeautifulSoup) -> None:
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript", "button", "input", "select", "textarea"]):
        element.decompose()
    for element in list(soup.find_all(True)):
        if element.attrs is None:
            continue
        attr_text = " ".join(
            str(value)
            for value in [
                element.get("id", ""),
                " ".join(element.get("class", [])) if isinstance(element.get("class"), list) else element.get("class", ""),
            ]
        ).lower()
        if any(keyword in attr_text for keyword in NOISE_ATTR_KEYWORDS):
            element.decompose()


def score_article_node(node: Any, text: str) -> int:
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    punctuation_count = len(re.findall(r"[，。！？；：、,.!?;:]", text))
    paragraph_count = len(node.find_all("p"))
    link_count = len(node.find_all("a"))
    return chinese_chars + punctuation_count * 2 + paragraph_count * 20 - link_count * 30


def extract_article_content(html_text: str, url: str = "") -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    remove_noise_nodes(soup)

    candidates: list[tuple[int, str]] = []
    for selector in ARTICLE_SELECTORS:
        for node in soup.select(selector):
            text = strip_boilerplate_lines(extract_text_block(node))
            if len(text) >= 200:
                candidates.append((score_article_node(node, text), text))

    if not candidates:
        return ""

    candidates.sort(key=lambda item: item[0], reverse=True)
    content = candidates[0][1].strip()
    content = cut_boilerplate_tail(content)
    content = repair_mojibake(content)
    if len(content) > 12000:
        content = content[:12000].rstrip()
    return "" if is_noisy_content(content) else content


def decode_html_bytes(data: bytes, declared_charset: str | None = None) -> str:
    candidates = [
        declared_charset,
        "utf-8",
        "gb18030",
        "gbk",
        "gb2312",
    ]
    for charset in candidates:
        if not charset:
            continue
        try:
            text = data.decode(charset, errors="replace")
        except LookupError:
            continue
        if text and not looks_mojibake(text):
            return text

    dammit = UnicodeDammit(data, is_html=True)
    if dammit.unicode_markup:
        return dammit.unicode_markup
    return data.decode("utf-8", errors="ignore")


def fetch_html(url: str, source_name: str) -> str:
    if not url:
        return ""

    try:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; llm-news-system-crawler/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=20) as response:  # noqa: S310
            charset = response.headers.get_content_charset() or "utf-8"
            return decode_html_bytes(response.read(), charset)
    except Exception as exc:  # noqa: BLE001
        logger.warning("抓取原文失败：%s | %s | %s", source_name, url, exc)
        return ""


def fetch_article_content(url: str, source_name: str) -> str:
    return extract_article_content(fetch_html(url, source_name), url)


def extract_editor(html_text: str) -> str:
    """从网页 HTML 中提取编辑信息。支持格式：【编辑:名字】或 编辑: 名字 等。"""
    if not html_text:
        logger.debug("editor: HTML为空，跳过编辑提取")
        return ""

    try:
        soup = BeautifulSoup(html_text, "html.parser")

        # 方法1: 查找 adEditor 类的div（中国新闻网结构）
        editor_div = soup.find("div", class_="adEditor")
        if editor_div:
            span = editor_div.find("span")
            if span:
                text = span.get_text(strip=True)
                # 提取 【编辑:名字】 中的名字
                if "【编辑:" in text and "】" in text:
                    editor_name = text.split("【编辑:")[1].split("】")[0].strip()
                    logger.info(f"editor: 从adEditor找到编辑={editor_name}")
                    return editor_name

        # 方法2: 搜索包含"编辑"关键词的文本
        for elem in soup.find_all(["span", "div", "p"]):
            text = elem.get_text(strip=True)
            if "编辑" in text and ("【" in text or ":" in text or "：" in text):
                # 尝试提取编辑名字
                if "【编辑:" in text:
                    try:
                        editor_name = text.split("【编辑:")[1].split("】")[0].strip()
                        return editor_name
                    except IndexError:
                        pass
                elif "编辑:" in text or "编辑：" in text:
                    try:
                        sep = "编辑:" if "编辑:" in text else "编辑："
                        editor_name = text.split(sep)[1].split("|")[0].split("】")[0].strip()
                        if editor_name and len(editor_name) <= 20:  # 合理的名字长度
                            return editor_name
                    except IndexError:
                        pass
    except Exception:  # noqa: BLE001
        pass

    return ""


def extract_cover_image(entry: Any, html_text: str, source_url: str) -> str:
    """
    只从正文区域提取封面图。
    如果正文中没有有效图片，直接返回空字符串。
    """

    # 仅在正文区域内查找图片
    if html_text:
        soup = BeautifulSoup(html_text, "html.parser")

        # 找到文章内容区域
        article_area = None
        for selector in ARTICLE_SELECTORS:
            article_area = soup.select_one(selector)
            if article_area:
                break

        if article_area:
            # 只在正文区域查找图片
            article_copy = BeautifulSoup(str(article_area), "html.parser")
            remove_noise_nodes(article_copy)

            for img in article_copy.find_all("img"):
                raw_src = img.get("data-src") or img.get("data-original") or img.get("src")
                image = normalize_image_url(raw_src, source_url)

                # 过滤掉通用图
                if image and not is_generic_image(image):
                    logger.info(f"从正文提取真实配图：{image[:80]}")
                    return image

    # 都没找到有效图片，不放图片
    logger.debug("未找到有效配图，cover_image 设置为空")
    return ""


def build_content(entry: Any, summary: str, link: str, source_name: str, html_text: str = "", fetch_content: bool = True) -> str:
    content = ""
    if getattr(entry, "content", None):
        try:
            content = clean_html(entry.content[0].value)
        except Exception:
            content = ""
    if fetch_content and html_text:
        article_content = extract_article_content(html_text, link)
        if article_content:
            content = article_content
    if not content:
        content = summary
    cleaned_content = repair_mojibake(cut_boilerplate_tail(content.strip()))
    if is_unreadable_article_text(cleaned_content) and summary:
        return repair_mojibake(cut_boilerplate_tail(summary.strip()))
    return cleaned_content




def parse_item(
    entry: Any,
    feed_source: dict[str, str],
    category_map: dict[str, int],
    topics: list[dict[str, Any]],
    fetch_content: bool,
) -> ParsedNewsItem:
    title = clean_html(getattr(entry, "title", "")).strip()
    raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
    summary_clean = clean_html(raw_summary)
    summary = truncate_text(summary_clean or title, 200)
    link = normalize_url(getattr(entry, "link", "") or "", feed_source.get("url", ""))
    html_text = fetch_html(link, feed_source["source_name"]) if link and fetch_content else ""
    editor = extract_editor(html_text) or clean_html(getattr(entry, "author", "")).strip() or ""

    publish_time_value = (
        getattr(entry, "published", None)
        or getattr(entry, "updated", None)
        or getattr(entry, "published_parsed", None)
        or getattr(entry, "updated_parsed", None)
    )
    publish_time = format_datetime(parse_datetime(publish_time_value))

    category_code = feed_source["category_code"]
    category_id = category_map[category_code]
    topic_id = match_topic_id(topics, title, summary)
    topic_name = next((topic["topic_name"] for topic in topics if int(topic["id"]) == topic_id), None)

    # 识别视频新闻
    is_video = is_video_news(entry, title, html_text)
    if is_video:
        logger.info(f"检测到视频新闻：{title[:60]}")

    # 提取封面图（过滤通用图）
    cover_image = extract_cover_image(entry, html_text, link)

    # 视频新闻不强行分配图片
    if is_video and not cover_image:
        logger.info(f"视频新闻无有效配图，允许 cover_image 为空：{title[:60]}")

    return ParsedNewsItem(
        title=title,
        summary=summary,
        content=build_content(entry, summary, link, feed_source["source_name"], html_text=html_text, fetch_content=fetch_content),
        cover_image=cover_image,
        category_id=category_id,
        topic_id=topic_id,
        source=feed_source["source_name"],
        editor=editor,
        publish_time=publish_time,
        view_count=0,
        like_count=0,
        comment_count=0,
        favorite_count=0,
        status=1,
        tags=build_tags(category_code, topic_name, feed_source["source_name"]),
        source_url=link or None,
    )

def fetch_feed(url: str) -> feedparser.FeedParserDict:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; llm-news-system-crawler/1.0)",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310
        data = response.read()
    return feedparser.parse(data)


def get_existing_news_by_source_url(connection: pymysql.connections.Connection, source_url: str) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, source_url, title, content, cover_image FROM news WHERE source_url = %s LIMIT 1", (source_url,))
        return cursor.fetchone()


def get_existing_news_by_title(connection: pymysql.connections.Connection, title: str) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, source_url, title, content, cover_image FROM news WHERE title = %s LIMIT 1", (title,))
        return cursor.fetchone()


def should_update_existing(existing_row: dict[str, Any], item: ParsedNewsItem, update_existing_content: bool) -> bool:
    if not update_existing_content:
        return False
    existing_content = str(existing_row.get("content") or "")
    existing_title = str(existing_row.get("title") or "")
    existing_image = str(existing_row.get("cover_image") or "")
    existing_url = str(existing_row.get("source_url") or "")
    return (
        is_noisy_content(existing_content)
        or looks_mojibake(existing_title)
        or looks_mojibake(existing_content)
        or cut_boilerplate_tail(existing_content) != existing_content.strip()
        or existing_image != item.cover_image
        or (bool(item.source_url) and existing_url != item.source_url)
    )


def insert_news(connection: pymysql.connections.Connection, item: ParsedNewsItem, has_source_url: bool) -> None:
    columns = [
        "title",
        "summary",
        "content",
        "cover_image",
        "category_id",
        "topic_id",
        "source",
        "editor",
        "publish_time",
        "view_count",
        "like_count",
        "comment_count",
        "favorite_count",
        "status",
        "tags",
        "created_at",
        "updated_at",
    ]
    values: list[Any] = [
        item.title,
        item.summary,
        item.content,
        item.cover_image,
        item.category_id,
        item.topic_id,
        item.source,
        item.editor,
        item.publish_time,
        item.view_count,
        item.like_count,
        item.comment_count,
        item.favorite_count,
        item.status,
        json.dumps(item.tags, ensure_ascii=False),
        item.publish_time,
        item.publish_time,
    ]
    if has_source_url:
        columns.insert(4, "source_url")
        values.insert(4, item.source_url)

    sql = f"INSERT INTO news ({', '.join(f'`{c}`' for c in columns)}) VALUES ({', '.join(['%s'] * len(values))})"
    with connection.cursor() as cursor:
        cursor.execute(sql, values)


def update_news(
    connection: pymysql.connections.Connection,
    news_id: int,
    item: ParsedNewsItem,
    has_source_url: bool,
) -> None:
    set_clauses = [
        "`title` = %s",
        "`summary` = %s",
        "`content` = %s",
        "`cover_image` = %s",
        "`category_id` = %s",
        "`topic_id` = %s",
        "`source` = %s",
        "`editor` = %s",
        "`publish_time` = %s",
        "`status` = %s",
        "`tags` = %s",
        "`updated_at` = %s",
    ]
    values: list[Any] = [
        item.title,
        item.summary,
        item.content,
        item.cover_image,
        item.category_id,
        item.topic_id,
        item.source,
        item.editor,
        item.publish_time,
        item.status,
        json.dumps(item.tags, ensure_ascii=False),
        item.publish_time,
    ]
    if has_source_url and item.source_url:
        set_clauses.insert(4, "`source_url` = COALESCE(%s, `source_url`)")
        values.insert(4, item.source_url)
    values.append(news_id)
    sql = f"UPDATE news SET {', '.join(set_clauses)} WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, values)


def archive_old_news(connection: pymysql.connections.Connection, cleanup_days: int) -> int:
    if cleanup_days <= 0:
        return 0
    cutoff = datetime.now() - timedelta(days=cleanup_days)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE news SET status = 0, updated_at = NOW() WHERE status = 1 AND publish_time < %s",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        return cursor.rowcount


def write_crawl_log(
    connection: pymysql.connections.Connection,
    *,
    source_name: str,
    rss_url: str,
    start_time: datetime,
    end_time: datetime,
    parsed_count: int,
    inserted_count: int,
    skipped_count: int,
    updated_count: int,
    failed_count: int,
    status: str,
    error_message: str | None,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO crawl_log
            (source_name, rss_url, start_time, end_time, parsed_count, inserted_count,
             skipped_count, updated_count, failed_count, status, error_message)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                source_name,
                rss_url,
                start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                parsed_count,
                inserted_count,
                skipped_count,
                updated_count,
                failed_count,
                status,
                error_message,
            ),
        )


def crawl_source(
    connection: pymysql.connections.Connection,
    feed_source: dict[str, str],
    max_items: int,
    dry_run: bool,
    fetch_content: bool,
    update_existing_content: bool,
) -> dict[str, Any]:
    start_time = datetime.now()
    logger.info("开始抓取 RSS 源：%s", feed_source["name"])

    stats = {
        "parsed": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
        "start_time": start_time,
        "end_time": start_time,
        "status": "success",
    }

    try:
        feed = fetch_feed(feed_source["url"])
        if getattr(feed, "bozo", False):
            error = getattr(feed, "bozo_exception", None)
            raise RuntimeError(error or "RSS 解析失败")

        category_map = get_category_map(connection)
        topics = get_topics(connection)
        has_source_url = has_column(connection, "news", "source_url")
        entries = list(feed.entries[:max_items])

        for entry in entries:
            stats["parsed"] += 1
            try:
                item = parse_item(entry, feed_source, category_map, topics, fetch_content=fetch_content)
                if not item.title:
                    raise ValueError("标题为空")

                existing_row = None
                match_key = ""
                if item.source_url and has_source_url:
                    existing_row = get_existing_news_by_source_url(connection, item.source_url)
                    match_key = "source_url"
                if existing_row is None:
                    existing_row = get_existing_news_by_title(connection, item.title)
                    if not match_key:
                        match_key = "title"

                if existing_row is not None:
                    if should_update_existing(existing_row, item, update_existing_content):
                        if dry_run:
                            stats["updated"] += 1
                            logger.info("[dry-run][update] %s | source_url=%s", item.title, item.source_url or "")
                        else:
                            update_news(connection, int(existing_row["id"]), item, has_source_url)
                            stats["updated"] += 1
                            logger.info("更新新闻：%s", item.title)
                    else:
                        stats["skipped"] += 1
                        logger.info("跳过重复新闻：%s", item.title)
                    continue

                if dry_run:
                    stats["inserted"] += 1
                    logger.info(
                        "[dry-run][insert] %s | category_id=%s | topic_id=%s | publish_time=%s",
                        item.title,
                        item.category_id,
                        item.topic_id,
                        item.publish_time,
                    )
                else:
                    insert_news(connection, item, has_source_url)
                    stats["inserted"] += 1
                    logger.info("成功入库：%s", item.title)
            except Exception as exc:  # noqa: BLE001
                stats["failed"] += 1
                error_message = f"{getattr(entry, 'title', '未知标题')}: {exc}"
                stats["errors"].append(error_message)
                logger.exception("处理新闻失败：%s", error_message)
    except Exception as exc:  # noqa: BLE001
        stats["failed"] += 1
        stats["errors"].append(f"{feed_source['name']}: {exc}")
        stats["status"] = "failed"
        logger.exception("抓取 RSS 源失败：%s", feed_source["name"])
    finally:
        stats["end_time"] = datetime.now()

    if stats["status"] != "failed":
        stats["status"] = "partial_failed" if stats["failed"] > 0 else "success"
    return stats


def print_summary(source_name: str, stats: dict[str, Any]) -> None:
    logger.info(
        "RSS 源完成：%s | 解析=%s | 新增=%s | 更新=%s | 跳过=%s | 失败=%s",
        source_name,
        stats["parsed"],
        stats["inserted"],
        stats["updated"],
        stats["skipped"],
        stats["failed"],
    )
    for error in stats["errors"]:
        logger.warning("失败原因：%s", error)


def filter_duplicate_images(connection: pymysql.connections.Connection) -> dict[str, Any]:
    """过滤重复使用的图片（通用图检测）

    如果同一张图片被超过3条新闻使用，认为它是通用图，过滤掉
    """
    filter_stats = {
        "duplicate_images_filtered": 0,
        "news_updated": 0,
        "top_images": [],
    }

    try:
        with connection.cursor() as cursor:
            # 1. 统计每张图片的使用次数
            cursor.execute("""
                SELECT cover_image, COUNT(*) as count
                FROM news
                WHERE cover_image != '' AND cover_image IS NOT NULL
                GROUP BY cover_image
                ORDER BY count DESC
            """)

            duplicate_images = {}
            top_images = []

            for row in cursor.fetchall():
                image_url = row["cover_image"]
                count = row["count"]

                if count > 10:  # 超过10次的认为是通用图
                    duplicate_images[image_url] = count
                    logger.warning(
                        "检测到重复图片（%d 次使用）：%s",
                        count,
                        image_url[:80],
                    )

                # 记录前10个最常用的图片
                if len(top_images) < 10:
                    top_images.append({"image": image_url[:80], "count": count})

            filter_stats["top_images"] = top_images

            # 2. 过滤掉重复图片（设为空）
            for image_url, count in duplicate_images.items():
                cursor.execute(
                    "UPDATE news SET cover_image = '' WHERE cover_image = %s",
                    (image_url,),
                )
                filtered_count = cursor.rowcount
                filter_stats["duplicate_images_filtered"] += 1
                filter_stats["news_updated"] += filtered_count
                logger.info(
                    "已过滤 %d 条新闻的重复图片（%s）",
                    filtered_count,
                    image_url[:80],
                )

            connection.commit()

    except Exception as exc:  # noqa: BLE001
        logger.exception("过滤重复图片失败：%s", exc)

    return filter_stats


def print_image_statistics(connection: pymysql.connections.Connection) -> None:
    """输出图片统计信息"""
    try:
        with connection.cursor() as cursor:
            # 总新闻数
            cursor.execute("SELECT COUNT(*) as count FROM news")
            total_news = cursor.fetchone()["count"]

            # 有图新闻数
            cursor.execute(
                "SELECT COUNT(*) as count FROM news WHERE cover_image != '' AND cover_image IS NOT NULL"
            )
            news_with_image = cursor.fetchone()["count"]

            # 无图新闻数
            cursor.execute(
                "SELECT COUNT(*) as count FROM news WHERE cover_image = '' OR cover_image IS NULL"
            )
            news_without_image = cursor.fetchone()["count"]

            # 唯一图片数
            cursor.execute(
                "SELECT COUNT(DISTINCT cover_image) as count FROM news WHERE cover_image != '' AND cover_image IS NOT NULL"
            )
            unique_images = cursor.fetchone()["count"]

            logger.info("=" * 80)
            logger.info("📊 爬虫图片统计")
            logger.info("=" * 80)
            logger.info("总新闻数：%d", total_news)
            logger.info("有图新闻数：%d", news_with_image)
            logger.info("无图新闻数：%d", news_without_image)
            logger.info("唯一图片数：%d", unique_images)

            if news_with_image > 0:
                ratio = (unique_images / news_with_image) * 100
                logger.info("图片多样性：%.1f%% (%d 个不重复图片 / %d 条有图新闻)", ratio, unique_images, news_with_image)

            # 输出最常用的前10张图片
            cursor.execute("""
                SELECT cover_image, COUNT(*) as count
                FROM news
                WHERE cover_image != '' AND cover_image IS NOT NULL
                GROUP BY cover_image
                ORDER BY count DESC
                LIMIT 10
            """)

            logger.info("最常用的前 10 张图片：")
            for idx, row in enumerate(cursor.fetchall(), 1):
                logger.info("  %d. %s（使用 %d 次）", idx, row["cover_image"][:70], row["count"])

            logger.info("=" * 80)

    except Exception as exc:  # noqa: BLE001
        logger.exception("输出统计信息失败：%s", exc)


def clean_existing_news_text(connection: pymysql.connections.Connection) -> int:
    """清理已入库新闻中的乱码和正文尾部附录，不改动互动统计字段。"""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, summary, content, source, editor
            FROM news
            WHERE status = 1
            """
        )
        rows = cursor.fetchall()

    updated_count = 0
    for row in rows:
        summary_text = repair_mojibake(cut_boilerplate_tail(normalize_whitespace(str(row.get("summary") or ""))))
        content_text = repair_mojibake(cut_boilerplate_tail(str(row.get("content") or "").strip()))
        if is_unreadable_article_text(content_text) and summary_text:
            content_text = summary_text
        cleaned = {
            "title": repair_mojibake(normalize_whitespace(str(row.get("title") or ""))),
            "summary": summary_text,
            "content": content_text,
            "source": repair_mojibake(normalize_whitespace(str(row.get("source") or ""))),
            "editor": repair_mojibake(normalize_whitespace(str(row.get("editor") or ""))),
        }
        changed = any(cleaned[field] != str(row.get(field) or "") for field in cleaned)
        if not changed:
            continue

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE news
                   SET title = %s,
                       summary = %s,
                       content = %s,
                       source = %s,
                       editor = %s,
                       updated_at = NOW()
                 WHERE id = %s
                """,
                (
                    cleaned["title"],
                    cleaned["summary"],
                    cleaned["content"],
                    cleaned["source"],
                    cleaned["editor"],
                    row["id"],
                ),
            )
        updated_count += 1

    connection.commit()
    return updated_count


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RSS news crawler")
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS, help="Max items per RSS source")
    parser.add_argument("--dry-run", action="store_true", help="Preview parsed items without writing database")
    parser.add_argument("--source", choices=["china_news", "all"], default=DEFAULT_SOURCE_MODE, help="RSS source group")
    parser.add_argument("--cleanup-days", type=int, default=0, help="Archive old news by days; 0 means disabled")
    parser.add_argument("--fetch-content", action="store_true", help="Fetch article page content and cover image")
    parser.add_argument("--update-existing-content", action="store_true", help="Update noisy existing content, empty cover image and bad source_url")
    parser.add_argument("--clean-existing-text", action="store_true", help="Clean mojibake and appendix text in existing news rows")
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    setup_logging()
    load_env()
    args = parse_args(argv or sys.argv[1:])

    db_config = get_db_config()
    logger.info("数据库：%s@%s:%s/%s", db_config["user"], db_config["host"], db_config["port"], db_config["database"])
    logger.info("运行模式：%s", "dry-run" if args.dry_run else "write")
    logger.info("每源最多抓取：%s", args.max_items)
    if args.cleanup_days > 0:
        logger.info("归档旧新闻：%s 天前", args.cleanup_days)

    connection = pymysql.connect(**db_config)
    total_stats = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []}

    try:
        if not args.dry_run and args.cleanup_days > 0:
            archived_count = archive_old_news(connection, args.cleanup_days)
            logger.info("已归档旧新闻数量：%s", archived_count)

        if not args.dry_run and args.clean_existing_text:
            cleaned_count = clean_existing_news_text(connection)
            logger.info("已清理旧新闻文本：%s", cleaned_count)

        if args.max_items > 0:
            for feed_source in get_source_list(args.source):
                stats = crawl_source(
                    connection,
                    feed_source,
                    args.max_items,
                    args.dry_run,
                    fetch_content=args.fetch_content,
                    update_existing_content=args.update_existing_content,
                )
                print_summary(feed_source["name"], stats)

                total_stats["parsed"] += stats["parsed"]
                total_stats["inserted"] += stats["inserted"]
                total_stats["updated"] += stats["updated"]
                total_stats["skipped"] += stats["skipped"]
                total_stats["failed"] += stats["failed"]
                total_stats["errors"].extend(stats["errors"])

                if not args.dry_run:
                    write_crawl_log(
                        connection,
                        source_name=feed_source["name"],
                        rss_url=feed_source["url"],
                        start_time=stats["start_time"],
                        end_time=stats["end_time"],
                        parsed_count=stats["parsed"],
                        inserted_count=stats["inserted"],
                        skipped_count=stats["skipped"],
                        updated_count=stats["updated"],
                        failed_count=stats["failed"],
                        status=stats["status"],
                        error_message="；".join(stats["errors"]) if stats["errors"] else None,
                    )
        else:
            logger.info("max-items=0，跳过 RSS 抓取")

        # 爬虫完成后，过滤重复图片和输出统计
        if not args.dry_run:
            logger.info("")
            logger.info("开始过滤重复图片...")
            filter_stats = filter_duplicate_images(connection)
            logger.info(
                "过滤完成：处理了 %d 张重复图片，更新了 %d 条新闻",
                filter_stats["duplicate_images_filtered"],
                filter_stats["news_updated"],
            )

    finally:
        # 输出最终统计
        print_image_statistics(connection)
        connection.close()

    logger.info(
        "全部完成 | 解析=%s | 新增=%s | 更新=%s | 跳过=%s | 失败=%s",
        total_stats["parsed"],
        total_stats["inserted"],
        total_stats["updated"],
        total_stats["skipped"],
        total_stats["failed"],
    )
    if total_stats["errors"]:
        logger.info("失败明细：%s", len(total_stats["errors"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


