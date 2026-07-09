"""人民网新闻爬虫。

从人民网频道首页抓取最新文章链接，解析文章页提取标题、正文、图片、时间、来源。
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import feedparser
import pymysql
from bs4 import BeautifulSoup
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = PROJECT_ROOT / "backend" / ".env"

# 频道配置。
# type="homepage": 从首页 HTML 提取文章链接
# type="rss": 从 RSS 源提取（兜底，内容可能较旧）
# 时政频道有反爬，从主站首页抓取 politics 域名的链接
# 科技/体育频道主页无自属文章，降级为 RSS
PEOPLE_SOURCES = [
    {"type": "homepage", "name": "人民网-时政", "url": "http://www.people.com.cn/",
     "link_domain": "politics.people.com.cn",
     "category_code": "politics", "source_name": "人民网"},
    {"type": "homepage", "name": "人民网-社会", "url": "http://society.people.com.cn/",
     "link_domain": "society.people.com.cn",
     "category_code": "society", "source_name": "人民网"},
    {"type": "homepage", "name": "人民网-财经", "url": "http://finance.people.com.cn/",
     "link_domain": "finance.people.com.cn",
     "category_code": "finance", "source_name": "人民网"},
    {"type": "rss", "name": "人民网-科技", "url": "http://www.people.com.cn/rss/scitech.xml",
     "category_code": "technology", "source_name": "人民网"},
    {"type": "rss", "name": "人民网-体育", "url": "http://www.people.com.cn/rss/sports.xml",
     "category_code": "sports", "source_name": "人民网"},
    {"type": "homepage", "name": "人民网-文娱", "url": "http://ent.people.com.cn/",
     "link_domain": "ent.people.com.cn",
     "category_code": "entertainment", "source_name": "人民网"},
    {"type": "homepage", "name": "人民网-国际", "url": "http://world.people.com.cn/",
     "link_domain": "world.people.com.cn",
     "category_code": "world", "source_name": "人民网"},
]

DEFAULT_MAX_ITEMS = 10
MIN_CONTENT_LENGTH = 200

BAD_IMAGE_KEYWORDS = [
    "logo", "icon", "avatar", "qrcode", "qr", "loading", "blank",
    "spacer", "sprite", "default", "placeholder", "video_default",
    "ewm", "qrcode-app", "zxcode", "share.png", "share.jpg",
]
PEOPLE_BAD_IMG_PATTERNS = ["share.png", "2020wbc", "weixin", "weibo", "qrcode"]
DUPLICATE_IMAGE_MIN_COUNT = 2

PEOPLE_BASE_URL = "http://www.people.com.cn"

# 浏览器 UA 用于绕过部分反爬
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

logger = logging.getLogger("people_cn_crawler")


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_env():
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


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(BeautifulSoup(text, "html.parser").get_text(" ", strip=True).split())


def normalize_url(raw_url: str | None, base_url: str = "") -> str:
    if not raw_url:
        return ""
    url = html.unescape(str(raw_url)).strip()
    m = re.search(r"https?://[^\s\"'<>]+", url)
    if m:
        url = m.group(0)
    elif base_url:
        url = urljoin(base_url, url)
    p = urlparse(url)
    return url if p.scheme in {"http", "https"} and p.netloc else ""


def normalize_image_url(raw_url: str | None, base_url: str = "") -> str:
    url = normalize_url(raw_url, base_url)
    if not url or url.lower().startswith("data:") or len(url) < 20:
        return ""
    if any(kw in url.lower() for kw in BAD_IMAGE_KEYWORDS):
        return ""
    if url.startswith("//"):
        url = "https:" + url
    return url


def is_generic_image(image_url: str) -> bool:
    if not image_url:
        return True
    lowered = image_url.lower()
    if any(kw in lowered for kw in BAD_IMAGE_KEYWORDS + PEOPLE_BAD_IMG_PATTERNS):
        return True
    if lowered.endswith(".gif") and "photo" not in lowered:
        return True
    return False


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text).split()).strip()


def _detect_charset(data: bytes) -> str:
    """从 HTML meta 标签检测 charset，默认返回 utf-8。"""
    m = re.search(rb'charset["\'=\s]+([a-zA-Z0-9_-]+)', data[:3000], re.I)
    if m:
        enc = m.group(1).decode("ascii", errors="ignore").lower()
        if enc in ("gbk", "gb2312", "gb18030", "utf-8"):
            return enc
    return "utf-8"


def fetch_html_people(url: str) -> str:
    """抓取人民网页面 HTML，自动检测编码。"""
    if not url:
        return ""
    try:
        import requests as req
        resp = req.get(url, headers={"User-Agent": BROWSER_UA}, timeout=20)
        data = resp.content
        charset = _detect_charset(data)
        return data.decode(charset, errors="replace")
    except Exception:
        try:
            r = Request(url, headers={
                "User-Agent": BROWSER_UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            with urlopen(r, timeout=20) as resp:
                data = resp.read()
            charset = _detect_charset(data)
            return data.decode(charset, errors="replace")
        except Exception as e:
            logger.warning("fetch_html_people failed: %s | %s", url, e)
            return ""


def extract_people_article(html_text: str, article_url: str = "") -> tuple[str, list[str], str, str]:
    """解析人民网文章详情页。

    返回: (content, images, pub_time, source_text)
    """
    if not html_text:
        return "", [], "", ""

    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
        tag.decompose()

    # 正文容器
    content_el = soup.select_one(".rm_txt_con") or soup.select_one(".text_con") or soup.select_one("#articleContent") or soup
    paragraphs = []
    for p in content_el.find_all("p"):
        text = normalize_whitespace(p.get_text())
        if len(text) > 15:
            paragraphs.append(text)
    content = "\n\n".join(paragraphs)

    # 正文图片
    images = []
    for img in content_el.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
        if src:
            if src.startswith("/") and not src.startswith("//"):
                src = PEOPLE_BASE_URL + src
            elif article_url:
                src = urljoin(article_url, src)
            else:
                src = normalize_url(src)
        u = normalize_image_url(src)
        if u and not is_generic_image(u):
            images.append(u)

    # 发布时间
    pub_date = ""
    pub_meta = soup.select_one('meta[name="publishdate"]')
    if pub_meta:
        pub_date = pub_meta.get("content", "").strip()

    time_str = ""
    for sel in [".text_time", ".time", ".article_time", ".info"]:
        time_el = soup.select_one(sel)
        if time_el:
            t = time_el.get_text(strip=True)
            if 5 < len(t) < 80:
                m = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{1,2}:\d{2}(:\d{2})?)', t)
                if m:
                    time_str = m.group(1)
                    break

    pub_time = pub_date
    if time_str:
        pub_time = f"{pub_date} {time_str.split()[-1]}" if pub_date else time_str

    # 来源
    source_text = ""
    source_meta = soup.select_one('meta[name="source"]')
    if source_meta:
        raw = source_meta.get("content", "").strip()
        raw = raw.replace("来源：", "").replace("来源:", "").replace("来源", "").strip()
        if raw and len(raw) < 80:
            source_text = raw

    return content, images, pub_time, source_text


def _extract_date_from_url(url: str) -> str | None:
    """从人民网文章 URL 中提取日期。URL 格式: /n1/YYYY/MMDD/cXXXX-XXXX.html"""
    m = re.search(r'/n1/(\d{4})/(\d{2})(\d{2})/', url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def parse_publish_time_from_page(page_time: str = "", article_url: str = "") -> str:
    """将页面时间字符串统一为 '%Y-%m-%d %H:%M:%S' 格式。"""
    if page_time:
        time_str = page_time.strip().replace("\n", " ").replace("\r", " ")
        for fmt in [
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
            "%Y年%m月%d日 %H:%M:%S", "%Y年%m月%d日 %H:%M",
            "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
        ]:
            try:
                return datetime.strptime(time_str, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
    # 从 URL 提取日期作为兜底
    url_date = _extract_date_from_url(article_url)
    if url_date:
        return f"{url_date} 00:00:00"
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime_safe(time_str: str) -> datetime | None:
    if not time_str:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except ValueError:
            continue
    try:
        from dateutil import parser as date_parser
        return date_parser.parse(time_str)
    except Exception:
        return None


def get_category_map(conn: pymysql.connections.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, code FROM news_category WHERE status=1")
        return {row["code"]: int(row["id"]) for row in cur.fetchall()}


def has_column(conn: pymysql.connections.Connection, table: str, col: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COLUMN_NAME AS cn FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=%s",
            [table],
        )
        return col in {str(r.get("cn", r.get("COLUMN_NAME", ""))) for r in cur.fetchall()}


def is_image_used_by_other(
    conn: pymysql.connections.Connection,
    img_url: str,
    source_url: str = "",
    title: str = "",
    exclude_id: int = None,
) -> bool:
    if not img_url:
        return False
    where = ["cover_image = %s"]
    params = [img_url]
    if exclude_id:
        where.append("id <> %s")
        params.append(exclude_id)
    with conn.cursor() as cur:
        cur.execute(f"SELECT id, title, source_url FROM news WHERE {' AND '.join(where)} LIMIT 5", params)
        for row in cur.fetchall():
            if source_url and normalize_url(row.get("source_url") or "") == normalize_url(source_url):
                continue
            if title and normalize_whitespace(str(row.get("title") or "")) == normalize_whitespace(title):
                continue
            return True
    return False


def fetch_section_links(page_url: str, domain_filter: str) -> list[str]:
    """从频道首页抓取符合域名过滤条件的文章链接列表。"""
    html_text = fetch_html_people(page_url)
    if not html_text:
        logger.error("首页抓取失败: %s", page_url)
        return []

    soup = BeautifulSoup(html_text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = str(a.get("href", ""))
        if not re.search(r'/n1/\d{4}/\d{4}/c\d+-\d+\.html', href):
            continue
        full = normalize_url(href, page_url)
        if not full:
            continue
        if domain_filter not in full:
            continue
        links.append(full)

    seen = set()
    result = []
    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def fetch_feed(url: str) -> list[dict]:
    """从 RSS 源获取条目列表，返回统一格式的 dict 列表。"""
    r = Request(url, headers={"User-Agent": BROWSER_UA})
    with urlopen(r, timeout=15) as resp:
        feed = feedparser.parse(resp.read())
    entries = []
    for entry in feed.entries:
        entries.append({
            "title": clean_html(getattr(entry, "title", "")).strip(),
            "link": normalize_url(getattr(entry, "link", ""), url),
            "summary": clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))[:500],
            "published_parsed": getattr(entry, "published_parsed", None),
            "updated_parsed": getattr(entry, "updated_parsed", None),
        })
    return entries


def parse_publish_time_rss(entry: dict, page_time: str = "") -> str:
    """从 RSS 条目的时间字段解析发布时间。"""
    pp = entry.get("published_parsed") or entry.get("updated_parsed")
    if pp:
        try:
            return datetime(*pp[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    if page_time:
        for fmt in [
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
            "%Y年%m月%d日 %H:%M:%S", "%Y年%m月%d日 %H:%M",
        ]:
            try:
                return datetime.strptime(page_time.strip(), fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_title_from_page(html_text: str) -> str:
    """从文章详情页提取标题。"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    h1s = soup.find_all("h1")
    for h1 in h1s:
        t = normalize_whitespace(h1.get_text())
        if len(t) > 5:
            return t
    # 兜底：从 <title> 标签提取
    title_tag = soup.find("title")
    if title_tag:
        t = title_tag.get_text(strip=True)
        # 去掉末尾的 "--频道名--人民网" 等后缀
        t = re.sub(r'\s*[-–—]\s*.*$', '', t).strip()
        return t
    return ""


def _process_article(conn, source, link, title, summary, cat_id, cat_map,
                     has_src_url, dry_run, update_existing, since_days,
                     stats, entry=None):
    """处理单篇文章：抓取详情页 → 解析 → 入库。entry 仅 RSS 模式传入。"""
    # 去重检查
    existing = None
    if link and has_src_url:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, source_url, title, content, cover_image FROM news WHERE source_url=%s LIMIT 1",
                [link],
            )
            existing = cur.fetchone()

    if existing:
        if update_existing and (
            len(str(existing.get("content") or "")) < MIN_CONTENT_LENGTH
            or not existing.get("cover_image")
        ):
            html_text = fetch_html_people(link)
            title2 = extract_title_from_page(html_text) or str(existing.get("title", ""))
            content, images, page_time, page_source = extract_people_article(html_text, link)
            if not content or len(content) < MIN_CONTENT_LENGTH:
                stats["skipped"] += 1
                return
            cover = images[0] if images else ""
            if is_image_used_by_other(conn, cover, source_url=link, title=title2, exclude_id=int(existing["id"])):
                logger.info("过滤重复图: %s", cover[:60])
                cover = ""
            if dry_run:
                stats["updated"] += 1
            else:
                with conn.cursor() as cur:
                    sets = ["content=%s", "summary=%s", "updated_at=NOW()"]
                    vals = [content, content[:500]]
                    if cover:
                        sets.append("cover_image=%s")
                        vals.append(cover)
                    vals.append(int(existing["id"]))
                    cur.execute(f"UPDATE news SET {', '.join(sets)} WHERE id=%s", vals)
                    stats["updated"] += 1
        else:
            stats["skipped"] += 1
        return

    # 新文章：抓取详情页
    html_text = fetch_html_people(link)
    if not html_text:
        stats["failed"] += 1
        return

    # 从页面提取标题（首页模式没有标题，RSS 模式下用页面标题覆盖）
    page_title = extract_title_from_page(html_text)
    if page_title:
        title = page_title

    if not title:
        stats["failed"] += 1
        return

    content, images, page_time, page_source = extract_people_article(html_text, link)

    if not content or len(content) < MIN_CONTENT_LENGTH:
        stats["skipped"] += 1
        return

    # 发布时间
    if entry:
        pub_time = parse_publish_time_rss(entry, page_time)
    else:
        pub_time = parse_publish_time_from_page(page_time, link)

    if since_days > 0:
        pub_dt = parse_datetime_safe(pub_time)
        if pub_dt is None or pub_dt < datetime.now() - timedelta(days=since_days):
            stats["skipped"] += 1
            return

    cat_id_val = cat_map.get(source["category_code"])
    if not cat_id_val:
        logger.warning("未找到分类: %s", source["category_code"])
        stats["failed"] += 1
        return

    cover = images[0] if images else ""
    if is_image_used_by_other(conn, cover, source_url=link, title=title):
        logger.info("过滤重复图: %s", cover[:60])
        cover = ""

    if dry_run:
        stats["inserted"] += 1
        logger.info("预览: %s", title[:50])
    else:
        cols = [
            "title", "summary", "content", "cover_image", "category_id",
            "source", "editor", "publish_time", "view_count", "like_count",
            "comment_count", "favorite_count", "status", "tags",
            "created_at", "updated_at",
        ]
        vals = [
            title, content[:500], content, cover, cat_id_val,
            source["source_name"], page_source or "",
            pub_time, 0, 0, 0, 0, 1,
            json.dumps([], ensure_ascii=False),
            pub_time, pub_time,
        ]
        if has_src_url:
            cols.insert(4, "source_url")
            vals.insert(4, link)

        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO news ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(vals))})",
                vals,
            )
        stats["inserted"] += 1
        logger.info("入库: %s", title[:50])


def crawl_source(conn, source, max_items, dry_run, fetch_content, update_existing, since_days=0):
    """抓取单个频道。支持 homepage 和 rss 两种模式。"""
    logger.info("抓取: %s (type=%s)", source["name"], source["type"])
    stats = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

    try:
        cat_map = get_category_map(conn)
        has_src_url = has_column(conn, "news", "source_url")

        if source["type"] == "homepage":
            # 首页抓取模式
            article_links = fetch_section_links(source["url"], source["link_domain"])
            if not article_links:
                logger.warning("未提取到文章链接: %s", source["name"])
            article_links = article_links[:max_items]
            logger.info("候选文章: %d 篇", len(article_links))

            for link in article_links:
                stats["parsed"] += 1
                try:
                    _process_article(conn, source, link, title="", summary="",
                                     cat_id=None, cat_map=cat_map,
                                     has_src_url=has_src_url, dry_run=dry_run,
                                     update_existing=update_existing,
                                     since_days=since_days, stats=stats)
                except Exception as e:
                    stats["failed"] += 1
                    logger.warning("失败: %s | %s", link[:60], e)

        else:
            # RSS 模式
            entries = fetch_feed(source["url"])
            entries = entries[:max_items]
            logger.info("RSS 条目: %d 条", len(entries))

            for entry in entries:
                stats["parsed"] += 1
                try:
                    title = entry["title"]
                    if not title:
                        stats["failed"] += 1
                        continue
                    link = entry["link"]
                    _process_article(conn, source, link, title=title,
                                     summary=entry["summary"],
                                     cat_id=None, cat_map=cat_map,
                                     has_src_url=has_src_url, dry_run=dry_run,
                                     update_existing=update_existing,
                                     since_days=since_days, stats=stats, entry=entry)
                except Exception as e:
                    stats["failed"] += 1
                    logger.warning("失败: %s | %s", entry.get("title", "?"), e)

    except Exception as e:
        stats["failed"] += 1
        logger.error("频道抓取失败: %s | %s", source["name"], e)

    logger.info(
        "完成: %s | 解析=%d 新增=%d 更新=%d 跳过=%d 失败=%d",
        source["name"], stats["parsed"], stats["inserted"], stats["updated"], stats["skipped"], stats["failed"],
    )
    return stats


def filter_duplicate_images(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cover_image, COUNT(*) as c FROM news WHERE cover_image!='' AND cover_image IS NOT NULL "
            "GROUP BY cover_image HAVING c>=%s ORDER BY c DESC",
            [DUPLICATE_IMAGE_MIN_COUNT],
        )
        dupes = [(r["cover_image"], r["c"]) for r in cur.fetchall()]
        for img, cnt in dupes:
            cur.execute("UPDATE news SET cover_image='' WHERE cover_image=%s", [img])
            logger.info("过滤%d条重复图: %s", cur.rowcount, img[:60])
    return len(dupes)


def print_stats(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM news WHERE status=1")
        total = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM news WHERE status=1 AND cover_image!='' AND cover_image IS NOT NULL")
        imgs = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(DISTINCT cover_image) as c FROM news WHERE cover_image!='' AND cover_image IS NOT NULL")
        uniq = cur.fetchone()["c"]
        logger.info(
            "统计: 总%d 有图%d 唯一图%d 多样性%.1f%%",
            total, imgs, uniq, (uniq / imgs * 100) if imgs else 0,
        )


def parse_args(argv):
    p = argparse.ArgumentParser(description="人民网新闻爬虫（首页链接抓取）")
    p.add_argument("--limit-per-source", type=int, default=DEFAULT_MAX_ITEMS, help="每个频道最多抓取篇数")
    p.add_argument("--since-days", type=int, default=0, help="仅保留最近 N 天内的新闻，0 表示不过滤")
    p.add_argument("--dry-run", action="store_true", help="预览不写库")
    p.add_argument("--fetch-content", action="store_true", help="抓取文章详情页正文（默认启用）")
    p.add_argument("--update-existing", action="store_true", help="更新已有新闻的正文和图片")
    return p.parse_args(argv)


def main(argv=None):
    setup_logging()
    load_env()
    args = parse_args(argv or sys.argv[1:])
    if not args.fetch_content and not args.dry_run:
        args.fetch_content = True
    conn = pymysql.connect(**get_db_config())
    logger.info(
        "DB: %s  dry_run=%s limit=%d since_days=%d fetch_content=%s",
        os.getenv("DB_NAME", "?"),
        args.dry_run,
        args.limit_per_source,
        args.since_days,
        args.fetch_content,
    )
    total = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
    try:
        for src in PEOPLE_SOURCES:
            st = crawl_source(
                conn,
                src,
                args.limit_per_source,
                args.dry_run,
                args.fetch_content,
                args.update_existing,
                args.since_days,
            )
            for k in total:
                total[k] += st[k]
        if not args.dry_run:
            filter_duplicate_images(conn)
        print_stats(conn)
    finally:
        conn.close()
    logger.info(
        "全部完成 | 解析=%d 新增=%d 更新=%d 跳过=%d 失败=%d",
        total["parsed"], total["inserted"], total["updated"], total["skipped"], total["failed"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
