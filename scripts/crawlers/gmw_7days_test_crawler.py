"""光明网 7 天历史新闻抓取测试。

测试 RSS 能否覆盖过去 7 天。写入 crawler_test_gmw_7days_news 表。
"""

from __future__ import annotations

import argparse, html, json, logging, os, re, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import feedparser, pymysql
from bs4 import BeautifulSoup
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = PROJECT_ROOT / "backend" / ".env"
TABLE_NAME = "crawler_test_gmw_7days_news"

GMW_SOURCES = [
    ("news.gmw.cn", "rss_news.xml", "politics", "时政要闻"),
    ("world.gmw.cn", "rss_world.xml", "world", "国际新闻"),
    ("economy.gmw.cn", "rss_economy.xml", "finance", "经济财经"),
    ("life.gmw.cn", "rss_life.xml", "society", "社会民生"),
    ("culture.gmw.cn", "rss_culture.xml", "entertainment", "文化"),
    ("tech.gmw.cn", "rss_tech.xml", "technology", "科技"),
    ("sports.gmw.cn", "rss_sports.xml", "sports", "体育"),
]

BAD_IMG = ["logo", "icon", "avatar", "qrcode", "qr", "loading", "blank", "spacer", "default", "placeholder", "content_banner", "pengyouquan"]
logger = logging.getLogger("gmw_7days")


def setup(): logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_env():
    if BACKEND_ENV_PATH.exists(): load_dotenv(BACKEND_ENV_PATH)
    else: load_dotenv()


def db_cfg():
    return {"host": os.getenv("DB_HOST", "127.0.0.1"), "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_NAME", "llm_news_system"), "user": os.getenv("DB_USER", "llm_news_user"),
            "password": os.getenv("DB_PASSWORD", ""), "charset": "utf8mb4", "cursorclass": pymysql.cursors.DictCursor, "autocommit": True}


def fetch(url):
    if not url: return ""
    try:
        import requests as req
        r = req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        r.encoding = r.apparent_encoding or "utf-8"; return r.text
    except:
        try:
            rq = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(rq, timeout=20) as resp: return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning("fetch failed: %s | %s", url, e); return ""


def clean(s): return " ".join(BeautifulSoup(s, "html.parser").get_text(" ", strip=True).split()) if s else ""


def norm_url(u, base=""):
    if not u: return ""
    u = html.unescape(str(u)).strip(); m = re.search(r"https?://[^\s\"'<>]+", u)
    if m: u = m.group(0)
    elif base: u = urljoin(base, u)
    p = urlparse(u); return u if p.scheme in {"http", "https"} and p.netloc else ""


def img_url(u, base=""):
    u = norm_url(u, base)
    if not u or u.lower().startswith("data:") or len(u) < 20: return ""
    if any(k in u.lower() for k in BAD_IMG): return ""
    return "https:" + u if u.startswith("//") else u


def parse_article(html):
    if not html: return "", [], "", ""
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]): t.decompose()
    node = soup.select_one("div.u-mainText") or soup
    imgs = []
    for img in node.find_all("img"):
        u = img_url(img.get("src") or img.get("data-src") or img.get("data-original") or "", "")
        if u: imgs.append(u)
    ps = [p.get_text(" ", strip=True) for p in node.find_all("p") if len(p.get_text(" ", strip=True)) > 15]
    content = "\n\n".join(ps)
    tt = soup.select_one("#articlePubTime") or soup.select_one(".m-con-time") or soup.select_one(".u-time")
    pub = tt.get_text(strip=True) if tt else ""
    st = soup.select_one(".m-con-source") or soup.select_one(".source")
    src = st.get_text(strip=True) if st else ""
    return content, imgs, pub, src


def parse_time(entry, page_tm=""):
    pp = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if pp:
        try: return datetime(*pp[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except: pass
    if page_tm:
        for f in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y年%m月%d日 %H:%M", "%Y-%m-%d"]:
            try: return datetime.strptime(page_tm.strip(), f).strftime("%Y-%m-%d %H:%M:%S")
            except: continue
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    setup(); load_env()
    p = argparse.ArgumentParser(); p.add_argument("--apply", action="store_true"); p.add_argument("--reset", action="store_true")
    p.add_argument("--limit", type=int, default=100)
    args = p.parse_args()
    conn = pymysql.connect(**db_cfg())
    # 自动创建测试表（如果不存在）
    with conn.cursor() as c:
        c.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
            source_name VARCHAR(100) NOT NULL, source_channel VARCHAR(100) NULL, category_code VARCHAR(50) NULL,
            title VARCHAR(500) NOT NULL, summary TEXT NULL, content LONGTEXT NULL, content_length INT DEFAULT 0,
            image_url TEXT NULL, image_count INT DEFAULT 0, image_urls_json TEXT NULL,
            publish_time DATETIME NULL, source_url TEXT NOT NULL, crawl_status VARCHAR(50) DEFAULT 'success',
            error_message TEXT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_gmw7d_url (source_url(255)), KEY idx_gmw7d_cat (category_code),
            KEY idx_gmw7d_time (publish_time), KEY idx_gmw7d_status (crawl_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
    if args.reset and args.apply:
        with conn.cursor() as c: c.execute(f"TRUNCATE TABLE {TABLE_NAME}")
        logger.info("已清空测试表")
    mode = "APPLY" if args.apply else "DRY-RUN"
    logger.info("=== %s 模式, limit=%d ===", mode, args.limit)

    total = {"ok": 0, "dup": 0, "fail": 0}
    all_dates = set()
    for host, rss_path, cat, ch_name in GMW_SOURCES:
        url = f"https://{host}/{rss_path}"
        logger.info("抓取: %s", ch_name)
        try:
            feed_r = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(feed_r, timeout=15) as resp:
                feed = feedparser.parse(resp.read())
            entries = list(feed.entries[:args.limit])
            logger.info("  RSS条目: %d", len(entries))
            for entry in entries:
                try:
                    title = clean(getattr(entry, "title", "")).strip()
                    if not title: continue
                    link = norm_url(getattr(entry, "link", ""), url)
                    summary = clean(getattr(entry, "summary", "") or getattr(entry, "description", ""))[:500]
                    html = fetch(link) if link else ""
                    content, imgs, pg_time, pg_src = parse_article(html)
                    pub = parse_time(entry, pg_time)
                    all_dates.add(pub[:10])
                    if not content or len(content) < 200:
                        total["fail"] += 1; continue
                    cover = imgs[0] if imgs else ""
                    if args.apply:
                        with conn.cursor() as c:
                            c.execute(f"""INSERT INTO {TABLE_NAME} (source_name,source_channel,category_code,title,summary,content,content_length,
                                image_url,image_count,image_urls_json,publish_time,source_url,crawl_status)
                                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'success')
                                ON DUPLICATE KEY UPDATE content=VALUES(content),image_url=VALUES(image_url),image_count=VALUES(image_count)""",
                                ("光明网", ch_name, cat, title, summary, content, len(content), cover, len(imgs),
                                 json.dumps(imgs, ensure_ascii=False) if imgs else None, pub, link))
                    total["ok"] += 1
                except Exception as e:
                    total["fail"] += 1
        except Exception as e:
            logger.error("频道失败: %s | %s", ch_name, e)

    logger.info("=== 完成: 成功=%d 失败=%d ===", total["ok"], total["fail"])
    logger.info("覆盖日期: %d 天 (%s ~ %s)", len(all_dates), min(all_dates) if all_dates else "?", max(all_dates) if all_dates else "?")

    if args.apply:
        with conn.cursor() as c:
            c.execute(f"SELECT DATE(publish_time) as d, COUNT(*) as n FROM {TABLE_NAME} WHERE crawl_status='success' GROUP BY d ORDER BY d DESC")
            for r in c.fetchall(): logger.info("  %s: %d篇", r["d"], r["n"])
            c.execute(f"SELECT category_code, COUNT(*) as n FROM {TABLE_NAME} WHERE crawl_status='success' GROUP BY category_code ORDER BY n DESC")
            for r in c.fetchall(): logger.info("  %s: %d篇", r["category_code"], r["n"])
            c.execute(f"SELECT COUNT(*) as t, SUM(CASE WHEN image_url!='' AND image_url IS NOT NULL THEN 1 ELSE 0 END) as imgs, MIN(publish_time) as mn, MAX(publish_time) as mx FROM {TABLE_NAME} WHERE crawl_status='success'")
            r = c.fetchone(); logger.info("总计: %d篇 有图%d 时间%s~%s", r["t"], r["imgs"], str(r["mn"])[:16] if r["mn"] else "?", str(r["mx"])[:16] if r["mx"] else "?")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
