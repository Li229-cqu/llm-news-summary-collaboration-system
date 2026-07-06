"""新华网（news.cn）新闻爬虫。

从新华网各频道首页抓取新闻链接，解析文章页提取标题、正文、图片、时间、来源。
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

import pymysql
from bs4 import BeautifulSoup
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = PROJECT_ROOT / "backend" / ".env"

# 各频道首页可静态提取文章链接的源。
# 注意：财经(fortune)、军事(mil)、教育(edu) 频道首页为 JS 动态渲染，
# 静态 HTML 中无文章链接，暂不支持。财经使用 /money/ 子频道。
NEWS_CN_SOURCES = [
    {"name": "新华网-时政", "url": "https://www.news.cn/politics/", "channel": "politics", "category_code": "politics"},
    {"name": "新华网-国际", "url": "https://www.news.cn/world/", "channel": "world", "category_code": "world"},
    {"name": "新华网-财经", "url": "https://www.news.cn/money/", "channel": "money", "category_code": "finance"},
    {"name": "新华网-科技", "url": "https://www.news.cn/tech/", "channel": "tech", "category_code": "technology"},
    {"name": "新华网-健康", "url": "https://www.news.cn/health/", "channel": "health", "category_code": "society"},
    {"name": "新华网-娱乐", "url": "https://www.news.cn/ent/", "channel": "ent", "category_code": "entertainment"},
    {"name": "新华网-地方", "url": "https://www.news.cn/local/", "channel": "local", "category_code": "society"},
    {"name": "新华网-法治", "url": "https://www.news.cn/legal/", "channel": "legal", "category_code": "society"},
    {"name": "新华网-评论", "url": "https://www.news.cn/comments/", "channel": "comments", "category_code": "society"},
]

DEFAULT_MAX_ITEMS = 10
MIN_CONTENT_LENGTH = 200

BAD_IMAGE_KEYWORDS = [
    "logo", "icon", "avatar", "qrcode", "qr", "loading", "blank",
    "spacer", "sprite", "default", "placeholder", "video_default",
    "ewm", "qrcode-app", "zxcode",
]
DUPLICATE_IMAGE_MIN_COUNT = 2

logger = logging.getLogger("news_cn_crawler")


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
    if any(kw in lowered for kw in BAD_IMAGE_KEYWORDS):
        return True
    if lowered.endswith(".gif") and "photo" not in lowered:
        return True
    return False


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text).split()).strip()


def fetch_html(url: str) -> str:
    """抓取页面 HTML，优先用 requests，fallback 到 urllib。"""
    if not url:
        return ""
    try:
        import requests as req
        resp = req.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; news-cn-crawler/1.0)"}, timeout=20)
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except Exception:
        try:
            r = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; news-cn-crawler/1.0)"})
            with urlopen(r, timeout=20) as resp:
                data = resp.read()
                for enc in ["utf-8", "gb18030", "gbk"]:
                    try:
                        return data.decode(enc, errors="replace")
                    except LookupError:
                        continue
                return data.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning("fetch_html failed: %s | %s", url, e)
            return ""


def extract_channel_links(html_text: str, channel: str) -> list[str]:
    """从频道首页提取该频道的文章链接列表，仅保留 news.cn 域。"""
    if not html_text:
        return []
    soup = BeautifulSoup(html_text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = str(a.get("href", ""))
        if f"/{channel}/" not in href or "/c.html" not in href:
            continue
        # 过滤分享链接和其他非 news.cn 域
        lower = href.lower()
        if any(domain in lower for domain in ["service.weibo.com", "t.qq.com", "t.sina.com", "bshare.cn", "share."]):
            continue
        full = normalize_url(href, f"https://www.news.cn/{channel}/")
        if full and ("news.cn" in full or "xinhuanet.com" in full):
            links.append(full)
    # 去重保序
    seen = set()
    result = []
    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def extract_news_cn_article(html_text: str, article_url: str = "") -> tuple[str, str, list[str], str, str]:
    """解析新华网文章详情页，提取标题、正文、图片、发布时间、来源。

    返回: (title, content, images, pub_time, source_text)
    """
    if not html_text:
        return "", "", [], "", ""

    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
        tag.decompose()

    # 标题
    title_el = (soup.select_one("h1 span.title")
                or soup.select_one("span.title")
                or soup.select_one("h1")
                or soup.select_one(".title"))
    title = normalize_whitespace(title_el.get_text()) if title_el else ""

    # 正文
    content_el = soup.select_one("#detailContent") or soup.select_one("span#detailContent")
    main_area = soup.select_one(".main-left") or soup.select_one(".main")
    paragraphs = []
    if content_el:
        for p in content_el.find_all("p"):
            text = normalize_whitespace(p.get_text())
            if len(text) > 15:
                paragraphs.append(text)
    content = "\n\n".join(paragraphs)

    # 正文图片（在 .main-left 或 #detailContent 范围内搜索，包含相对路径解析）
    images = []
    search_area = main_area or content_el or soup
    for img in search_area.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
        # 解析相对路径
        if src and article_url:
            src = normalize_url(src, article_url)
        else:
            src = normalize_url(src)
        u = normalize_image_url(src)
        if u and not is_generic_image(u):
            images.append(u)

    # 发布时间
    pub_meta = soup.select_one('meta[name="publishdate"]')
    pub_date = pub_meta.get("content", "").strip() if pub_meta else ""
    time_el = soup.select_one(".header-time .time") or soup.select_one(".time")
    time_str = time_el.get_text(strip=True) if time_el else ""
    pub_time = f"{pub_date} {time_str}".strip() if pub_date else time_str

    # 来源
    source_meta = soup.select_one('meta[name="source"]')
    source_text = source_meta.get("content", "").strip() if source_meta else ""
    source_el = soup.select_one(".source")
    if source_el:
        raw = source_el.get_text(strip=True)
        raw = raw.replace("来源：", "").replace("来源:", "").strip()
        if raw and raw != "来源" and len(raw) < 50:
            source_text = raw

    return title, content, images, pub_time, source_text


def parse_publish_time(page_time: str = "") -> str:
    """将页面时间字符串统一为 '%Y-%m-%d %H:%M:%S' 格式。"""
    if not page_time:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


def crawl_source(conn, source, max_items, dry_run, update_existing, since_days):
    """抓取单个频道：频道首页提取链接 → 逐篇解析 → 入库。"""
    start = datetime.now()
    logger.info("抓取: %s", source["name"])
    stats = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

    try:
        cat_map = get_category_map(conn)
        has_src_url = has_column(conn, "news", "source_url")

        # 1. 获取频道首页并提取文章链接
        channel_html = fetch_html(source["url"])
        if not channel_html:
            logger.error("频道页抓取失败: %s", source["name"])
            stats["failed"] += 1
            return stats

        article_links = extract_channel_links(channel_html, source["channel"])
        if not article_links:
            logger.warning("未找到文章链接: %s (可能是JS动态渲染)", source["name"])

        # 2. 限制数量
        article_links = article_links[:max_items]
        logger.info("发现 %d 篇候选文章", len(article_links))

        # 3. 逐篇处理
        for link in article_links:
            stats["parsed"] += 1
            try:
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
                        html_text = fetch_html(link)
                        title, content, images, pub_time, source_text = extract_news_cn_article(html_text, link)
                        if not content or len(content) < MIN_CONTENT_LENGTH:
                            stats["skipped"] += 1
                            continue
                        cover = images[0] if images else ""
                        if is_image_used_by_other(conn, cover, source_url=link, title=title, exclude_id=int(existing["id"])):
                            logger.info("过滤重复图: %s", cover[:60])
                            cover = ""
                        summary = content[:500]
                        if dry_run:
                            stats["updated"] += 1
                        else:
                            with conn.cursor() as cur:
                                sets = ["content=%s", "summary=%s", "updated_at=NOW()"]
                                vals = [content, summary]
                                if cover:
                                    sets.append("cover_image=%s")
                                    vals.append(cover)
                                vals.append(int(existing["id"]))
                                cur.execute(f"UPDATE news SET {', '.join(sets)} WHERE id=%s", vals)
                                stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                    continue

                # 新文章：抓取详情页
                html_text = fetch_html(link)
                if not html_text:
                    stats["failed"] += 1
                    continue

                title, content, images, pub_time, source_text = extract_news_cn_article(html_text, link)

                if not title:
                    stats["failed"] += 1
                    continue
                if not content or len(content) < MIN_CONTENT_LENGTH:
                    stats["skipped"] += 1
                    continue

                pub_time_fmt = parse_publish_time(pub_time)

                # 时间过滤
                if since_days > 0:
                    pub_dt = parse_datetime_safe(pub_time_fmt)
                    if pub_dt is None or pub_dt < datetime.now() - timedelta(days=since_days):
                        stats["skipped"] += 1
                        continue

                # 分类
                cat_id = cat_map.get(source["category_code"])
                if not cat_id:
                    logger.warning("未找到分类: %s，跳过标题: %s", source["category_code"], title[:40])
                    stats["failed"] += 1
                    continue

                cover = images[0] if images else ""
                summary = content[:500]

                # 封面图去重
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
                        title, summary, content, cover, cat_id,
                        "新华网", source_text or "新华网",
                        pub_time_fmt, 0, 0, 0, 0, 1,
                        json.dumps([], ensure_ascii=False),
                        pub_time_fmt, pub_time_fmt,
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

            except Exception as e:
                stats["failed"] += 1
                logger.warning("失败: %s | %s", link[:60], e)

    except Exception as e:
        stats["failed"] += 1
        logger.error("频道抓取失败: %s | %s", source["name"], e)

    logger.info(
        "完成: %s | 解析=%d 新增=%d 更新=%d 跳过=%d 失败=%d",
        source["name"],
        stats["parsed"], stats["inserted"], stats["updated"], stats["skipped"], stats["failed"],
    )
    return stats


def filter_duplicate_images(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cover_image, COUNT(*) as c FROM news WHERE cover_image!='' AND cover_image IS NOT NULL GROUP BY cover_image HAVING c>=%s ORDER BY c DESC",
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
    p = argparse.ArgumentParser(description="新华网 news.cn 新闻爬虫")
    p.add_argument("--limit-per-source", type=int, default=DEFAULT_MAX_ITEMS, help="每个频道最多抓取篇数")
    p.add_argument("--since-days", type=int, default=0, help="仅保留最近 N 天内的新闻，0 表示不过滤")
    p.add_argument("--dry-run", action="store_true", help="预览不写库")
    p.add_argument("--fetch-content", action="store_true", help="抓取文章详情页（默认启用）")
    p.add_argument("--update-existing", action="store_true", help="更新已有新闻的正文和图片")
    return p.parse_args(argv)


def main(argv=None):
    setup_logging()
    load_env()
    args = parse_args(argv or sys.argv[1:])
    conn = pymysql.connect(**get_db_config())
    logger.info(
        "DB: %s  dry_run=%s limit=%d since_days=%d",
        os.getenv("DB_NAME", "?"),
        args.dry_run,
        args.limit_per_source,
        args.since_days,
    )
    total = {"parsed": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
    try:
        for src in NEWS_CN_SOURCES:
            st = crawl_source(
                conn,
                src,
                args.limit_per_source,
                args.dry_run,
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
