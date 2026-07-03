"""光明网 RSS 新闻爬虫。

从光明网 7 个频道 RSS 抓取新闻，解析文章页提取正文、图片、时间、来源。
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
from dateutil import parser as date_parser
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = PROJECT_ROOT / "backend" / ".env"

GMW_RSS_SOURCES = [
    {"name": "光明网-时政要闻", "url": "https://news.gmw.cn/rss_news.xml", "category_code": "politics", "source_name": "光明网"},
    {"name": "光明网-国际新闻", "url": "https://world.gmw.cn/rss_world.xml", "category_code": "world", "source_name": "光明网"},
    {"name": "光明网-经济财经", "url": "https://economy.gmw.cn/rss_economy.xml", "category_code": "finance", "source_name": "光明网"},
    {"name": "光明网-社会民生", "url": "https://life.gmw.cn/rss_life.xml", "category_code": "society", "source_name": "光明网"},
    {"name": "光明网-文化", "url": "https://culture.gmw.cn/rss_culture.xml", "category_code": "entertainment", "source_name": "光明网"},
    {"name": "光明网-科技", "url": "https://tech.gmw.cn/rss_tech.xml", "category_code": "technology", "source_name": "光明网"},
    {"name": "光明网-体育", "url": "https://sports.gmw.cn/rss_sports.xml", "category_code": "sports", "source_name": "光明网"},
]

DEFAULT_MAX_ITEMS = 10
MIN_CONTENT_LENGTH = 200

BAD_IMAGE_KEYWORDS = ["logo", "icon", "avatar", "qrcode", "qr", "loading", "blank", "spacer", "sprite", "default", "placeholder", "video_default"]
GMW_BAD_IMG_PATTERNS = ["content_banner", "qrcodes", "pengyouquan"]
DUPLICATE_IMAGE_MIN_COUNT = 2

logger = logging.getLogger("gmw_rss_crawler")


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_env():
    if BACKEND_ENV_PATH.exists():
        load_dotenv(BACKEND_ENV_PATH)
    else:
        load_dotenv()


def get_db_config() -> dict[str, Any]:
    return {"host": os.getenv("DB_HOST", "127.0.0.1"), "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_NAME", "llm_news_system"), "user": os.getenv("DB_USER", "llm_news_user"),
            "password": os.getenv("DB_PASSWORD", ""), "charset": "utf8mb4", "cursorclass": pymysql.cursors.DictCursor, "autocommit": True}


def clean_html(text: str | None) -> str:
    if not text: return ""
    return " ".join(BeautifulSoup(text, "html.parser").get_text(" ", strip=True).split())


def normalize_url(raw_url: str | None, base_url: str = "") -> str:
    if not raw_url: return ""
    url = html.unescape(str(raw_url)).strip()
    m = re.search(r"https?://[^\s\"'<>]+", url)
    if m: url = m.group(0)
    elif base_url: url = urljoin(base_url, url)
    p = urlparse(url)
    return url if p.scheme in {"http", "https"} and p.netloc else ""


def normalize_image_url(raw_url: str | None, base_url: str = "") -> str:
    url = normalize_url(raw_url, base_url)
    if not url or url.lower().startswith("data:") or len(url) < 20: return ""
    return "" if any(kw in url.lower() for kw in BAD_IMAGE_KEYWORDS) else url


def is_generic_image(image_url: str) -> bool:
    if not image_url: return True
    lowered = image_url.lower()
    if any(kw in lowered for kw in BAD_IMAGE_KEYWORDS + GMW_BAD_IMG_PATTERNS): return True
    if lowered.endswith(".gif") and "photo" not in lowered: return True
    return False


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text).split()).strip()


def fetch_html_gmw(url: str) -> str:
    if not url: return ""
    try:
        import requests as req
        resp = req.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; gmw-crawler/1.0)"}, timeout=20)
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except Exception:
        try:
            r = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; gmw-crawler/1.0)"})
            with urlopen(r, timeout=20) as resp:
                data = resp.read()
                for enc in ["utf-8", "gb18030", "gbk"]:
                    try: return data.decode(enc, errors="replace")
                    except LookupError: continue
                return data.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning("fetch_html failed: %s | %s", url, e)
            return ""


def extract_gmw_article(html_text: str) -> tuple[str, list[str], str, str]:
    """提取正文、图片、发布时间、来源。返回 (content, images, pub_time, source_text)。"""
    if not html_text: return "", [], "", ""
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
        tag.decompose()
    article_node = soup.select_one("div.u-mainText") or soup
    images = []
    for img in article_node.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or img.get("original") or ""
        u = normalize_image_url(src, "")
        if u and not is_generic_image(u):
            if u.startswith("//"): u = "https:" + u
            images.append(u)
    paragraphs = [normalize_whitespace(p.get_text(" ", strip=True)) for p in article_node.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) > 15]
    content = "\n\n".join(paragraphs)
    time_tag = soup.select_one("#articlePubTime") or soup.select_one(".m-con-time") or soup.select_one(".u-time")
    pub_time = time_tag.get_text(strip=True) if time_tag else ""
    source_tag = soup.select_one(".m-con-source") or soup.select_one(".source")
    source_text = source_tag.get_text(strip=True) if source_tag else ""
    return content, images, pub_time, source_text


def parse_publish_time(rss_entry: Any, page_time: str = "") -> str:
    pp = getattr(rss_entry, "published_parsed", None) or getattr(rss_entry, "updated_parsed", None)
    if pp:
        try: return datetime(*pp[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except: pass
    if page_time:
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y年%m月%d日 %H:%M", "%Y-%m-%d"]:
            try: return datetime.strptime(page_time.strip(), fmt).strftime("%Y-%m-%d %H:%M:%S")
            except: continue
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    r = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; gmw-crawler/1.0)"})
    with urlopen(r, timeout=15) as resp: return feedparser.parse(resp.read())


def get_category_map(conn: pymysql.connections.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, code FROM news_category WHERE status=1")
        return {row["code"]: int(row["id"]) for row in cur.fetchall()}


def has_column(conn: pymysql.connections.Connection, table: str, col: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT COLUMN_NAME AS cn FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=%s", [table])
        return col in {str(r.get("cn", r.get("COLUMN_NAME", ""))) for r in cur.fetchall()}


def is_image_used_by_other(conn: pymysql.connections.Connection, img_url: str, source_url: str = "", title: str = "", exclude_id: int = None) -> bool:
    if not img_url: return False
    where = ["cover_image = %s"]; params = [img_url]
    if exclude_id: where.append("id <> %s"); params.append(exclude_id)
    with conn.cursor() as cur:
        cur.execute(f"SELECT id, title, source_url FROM news WHERE {' AND '.join(where)} LIMIT 5", params)
        for row in cur.fetchall():
            if source_url and normalize_url(row.get("source_url") or "") == normalize_url(source_url): continue
            if title and normalize_whitespace(str(row.get("title") or "")) == normalize_whitespace(title): continue
            return True
    return False


def crawl_source(conn, source, max_items, dry_run, fetch_content, update_existing):
    start = datetime.now()
    logger.info("抓取: %s", source["name"])
    stats = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
    try:
        feed = fetch_feed(source["url"])
        cat_map = get_category_map(conn)
        has_src_url = has_column(conn, "news", "source_url")
        for entry in list(feed.entries[:max_items]):
            stats["parsed"] += 1
            try:
                title = clean_html(getattr(entry, "title", "")).strip()
                if not title: stats["failed"] += 1; continue
                link = normalize_url(getattr(entry, "link", ""), source["url"])
                summary = clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))[:500]
                html_text = fetch_html_gmw(link) if link and fetch_content else ""
                content, images, page_time, page_source = extract_gmw_article(html_text)
                if not content or len(content) < MIN_CONTENT_LENGTH:
                    stats["skipped"] += 1; continue
                cover = images[0] if images else ""
                pub_time = parse_publish_time(entry, page_time)
                cat_id = cat_map.get(source["category_code"])
                if not cat_id: stats["failed"] += 1; continue

                existing = None
                if link and has_src_url:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, source_url, title, content, cover_image FROM news WHERE source_url=%s LIMIT 1", [link])
                        existing = cur.fetchone()
                if existing:
                    if is_image_used_by_other(conn, cover, source_url=link, title=title, exclude_id=int(existing["id"])):
                        logger.info("过滤重复图: %s", cover[:60]); cover = ""
                    if update_existing and (len(str(existing.get("content") or "")) < MIN_CONTENT_LENGTH or not existing.get("cover_image")):
                        if dry_run: stats["updated"] += 1
                        else:
                            with conn.cursor() as cur:
                                sets = ["content=%s", "summary=%s", "updated_at=NOW()"]; vals = [content, summary]
                                if cover: sets.append("cover_image=%s"); vals.append(cover)
                                vals.append(int(existing["id"]))
                                cur.execute(f"UPDATE news SET {', '.join(sets)} WHERE id=%s", vals)
                                stats["updated"] += 1
                    else: stats["skipped"] += 1
                    continue

                if is_image_used_by_other(conn, cover, source_url=link, title=title):
                    logger.info("过滤重复图: %s", cover[:60]); cover = ""
                if dry_run:
                    stats["inserted"] += 1
                else:
                    cols = ["title","summary","content","cover_image","category_id","source","editor","publish_time","view_count","like_count","comment_count","favorite_count","status","tags","created_at","updated_at"]
                    vals = [title, summary, content, cover, cat_id, source["source_name"], page_source or "", pub_time, 0, 0, 0, 0, 1, json.dumps([], ensure_ascii=False), pub_time, pub_time]
                    if has_src_url: cols.insert(4, "source_url"); vals.insert(4, link)
                    with conn.cursor() as cur:
                        cur.execute(f"INSERT INTO news ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(vals))})", vals)
                    stats["inserted"] += 1
                    logger.info("入库: %s", title[:50])
            except Exception as e:
                stats["failed"] += 1
                logger.warning("失败: %s | %s", getattr(entry, "title", "?"), e)
    except Exception as e:
        stats["failed"] += 1
        logger.error("RSS源失败: %s | %s", source["name"], e)
    logger.info("完成: %s | 解析=%d 新增=%d 更新=%d 跳过=%d 失败=%d", source["name"], stats["parsed"], stats["inserted"], stats["updated"], stats["skipped"], stats["failed"])
    return stats


def filter_duplicate_images(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT cover_image, COUNT(*) as c FROM news WHERE cover_image!='' AND cover_image IS NOT NULL GROUP BY cover_image HAVING c>=%s ORDER BY c DESC", [DUPLICATE_IMAGE_MIN_COUNT])
        dupes = [(r["cover_image"], r["c"]) for r in cur.fetchall()]
        for img, cnt in dupes:
            cur.execute("UPDATE news SET cover_image='' WHERE cover_image=%s", [img])
            logger.info("过滤%d条重复图: %s", cur.rowcount, img[:60])
    return len(dupes)


def print_stats(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM news WHERE status=1"); total = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM news WHERE status=1 AND cover_image!='' AND cover_image IS NOT NULL"); imgs = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(DISTINCT cover_image) as c FROM news WHERE cover_image!='' AND cover_image IS NOT NULL"); uniq = cur.fetchone()["c"]
        logger.info("统计: 总%d 有图%d 唯一图%d 多样性%.1f%%", total, imgs, uniq, (uniq/imgs*100) if imgs else 0)


def parse_args(argv):
    p = argparse.ArgumentParser(description="光明网 RSS 新闻爬虫")
    p.add_argument("--limit-per-source", type=int, default=DEFAULT_MAX_ITEMS)
    p.add_argument("--dry-run", action="store_true", help="预览不写库")
    p.add_argument("--fetch-content", action="store_true", help="抓取文章详情页")
    p.add_argument("--update-existing", action="store_true", help="更新已有新闻的正文和图片")
    return p.parse_args(argv)


def main(argv=None):
    setup_logging(); load_env()
    args = parse_args(argv or sys.argv[1:])
    conn = pymysql.connect(**get_db_config())
    logger.info("DB: %s  dry_run=%s limit=%d", os.getenv("DB_NAME","?"), args.dry_run, args.limit_per_source)
    total = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
    try:
        for src in GMW_RSS_SOURCES:
            st = crawl_source(conn, src, args.limit_per_source, args.dry_run, args.fetch_content, args.update_existing)
            for k in total: total[k] += st[k]
        if not args.dry_run:
            filter_duplicate_images(conn)
        print_stats(conn)
    finally:
        conn.close()
    logger.info("全部完成 | 解析=%d 新增=%d 更新=%d 跳过=%d 失败=%d", total["parsed"], total["inserted"], total["updated"], total["skipped"], total["failed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
