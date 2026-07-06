"""News Editor Agent — Lightweight NLP Fallback Functions.

Pure Python standard-library implementations for Steps 2-8
when the real LLM (DeepSeek / Zhipu) is unavailable, unconfigured,
timed out, or returns an error.

No external dependencies — only re, collections.Counter, datetime, math.
"""

from __future__ import annotations

import re
import math
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

# ═════════════════════════════════════════════════════════════
# Common helpers
# ═════════════════════════════════════════════════════════════

# Chinese stop words — frequent function words that carry little meaning
_STOP_WORDS: set = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "所", "为", "所以", "因为", "但是", "然而", "而且", "虽然", "如果",
    "可以", "这个", "那个", "什么", "怎么", "如何", "哪里", "吗", "呢",
    "吧", "啊", "哦", "嗯", "被", "把", "从", "让", "对", "向", "与",
    "及", "或", "其", "之", "已", "将", "能", "可", "以", "于", "则",
    "又", "并", "但", "而", "且", "因", "尽管", "通过", "经过", "按照",
    "根据", "目前", "已经", "正在", "还", "更", "最", "非常", "十分",
    "进行", "使用", "利用", "包括", "成为", "作为", "称为", "认为",
    "表示", "指出", "强调", "透露", "介绍", "显示", "表明", "反映",
    "该", "此", "本", "记者", "报道", "新闻", "来源", "编辑", "发布",
    "近日", "日", "月", "年", "时", "分", "前", "后", "中", "里",
    "来", "去", "做", "使", "请", "各", "等", "多", "少", "大", "小",
}

# Event verbs — sentence scoring boost
_EVENT_VERBS: set = {
    "发布", "宣布", "完成", "启动", "增长", "下降", "获奖", "晋级",
    "通报", "回应", "实施", "推进", "举行", "发生", "造成", "获得",
    "突破", "推出", "上市", "签署", "达成", "批准", "取消", "暂停",
    "恢复", "升级", "改造", "建设", "投入", "投资", "融资", "收购",
    "合并", "裁员", "解散", "倒闭", "爆炸", "袭击", "坠毁", "失联",
    "确诊", "出院", "康复", "死亡", "救援", "撤离", "预警", "登陆",
    "夺冠", "击败", "战胜", "淘汰", "晋级", "得分", "进球", "破门",
    "命中", "犯规", "判罚", "转会", "续约", "退役", "复出", "开幕",
    "闭幕", "上映", "播出", "开播", "杀青", "定档", "斩获", "入围",
    "提名", "揭晓", "曝光", "泄露", "召回", "反弹", "暴跌", "暴涨",
    "飙升", "回落", "企稳", "震荡", "开盘", "收盘", "分红", "派息",
    "增持", "减持", "回购", "注资", "补贴", "减免", "征收", "调整",
    "修订", "废止", "施行", "延期", "提前", "毕业", "录取", "招生",
    "开学", "放假", "考试", "答辩", "答辩", "评审", "通过", "驳回",
    "上诉", "裁决", "判决", "逮捕", "拘留", "起诉", "宣判", "释放",
}

# Institution name patterns
_INSTITUTION_PATTERNS = [
    r"(?:中国|国家|全国|中央|国务院|外交部|国防部|科技部|工信部|教育部|公安部|民政部|司法部|财政部|人社部|自然资源部|生态环境部|住建部|交通运输部|水利部|农业农村部|商务部|文旅部|卫健委|退役军人事务部|应急管理部|人民银行|审计署|国家税务总局|市场监管总局|广电总局|体育总局|统计局|医保局|气象局|能源局|国防科工局|航天局|民航局|铁路局|邮政局|文物局|中医药局|外汇局|银保监会|证监会)",
    r"(?:北京|上海|广州|深圳|天津|重庆|成都|武汉|杭州|南京|苏州|西安|长沙|青岛|大连|宁波|厦门|郑州|沈阳|济南|合肥|福州|东莞|佛山|无锡|长春|哈尔滨|石家庄|昆明|贵阳|南宁|海口|拉萨|银川|西宁|兰州|呼和浩特|乌鲁木齐)(?:市|省|自治区|地区|县|区)?(?:政府|公安局|教育局|卫健委|市场监管局|财政局|发改委|住建局|交通局|人社局|民政局|城管局|环保局|文旅局|体育局|气象局|应急管理局)?",
    r"(?:联合国|世卫组织|世界银行|国际货币基金组织|欧盟|北约|东盟|非盟|OPEC|G7|G20|APEC|IMF|WTO|UNICEF|UNESCO)",
    r"(?:中国科学院|中国工程院|中国社科院|清华大学|北京大学|浙江大学|复旦大学|上海交通大学|南京大学|中国科大|哈工大|西安交大|武汉大学|华中科大|中山大学|四川大学)(?:大学|学院|研究院|研究所|实验室|课题组)?",
    r"(?:华为|阿里|腾讯|百度|字节跳动|美团|京东|拼多多|网易|小米|OPPO|vivo|比亚迪|宁德时代|隆基|阳光电源|中芯国际|长江存储|寒武纪|商汤|旷视|科大讯飞|海康威视)(?:公司|集团|科技|股份|有限)?",
    r"(?:中国石油|中国石化|中海油|国家电网|南方电网|中国移动|中国联通|中国电信|中国铁路|中国建筑|中国中铁|中国铁建|中国交建|中航工业|中国船舶|兵器工业|中国电子)(?:集团|总公司|公司)?",
]

# Topic keyword lexicon for Step 5
_TOPIC_LEXICON: Dict[str, List[str]] = {
    "体育": ["比赛", "球队", "球员", "进球", "晋级", "冠军", "主教练", "赛事",
             "联赛", "杯赛", "决赛", "半决赛", "小组赛", "淘汰赛", "客场", "主场",
             "球迷", "裁判", "点球", "射门", "篮球", "足球", "排球", "乒乓球",
             "羽毛球", "网球", "游泳", "田径", "冬奥", "奥运", "金牌", "银牌",
             "铜牌", "纪录", "打破", "世界纪录", "亚洲纪录", "体育", "运动"],
    "财经": ["股价", "市场", "营收", "投资", "企业", "增长", "下降", "融资",
             "A股", "港股", "美股", "基金", "股票", "债券", "期货", "外汇",
             "GDP", "CPI", "PMI", "通胀", "利率", "加息", "降息", "央行",
             "上市", "IPO", "财报", "净利润", "毛利率", "市值", "股东"],
    "科技": ["人工智能", "芯片", "算法", "模型", "数据", "算力", "机器人",
             "5G", "6G", "量子", "区块链", "云计算", "大数据", "物联网",
             "AI", "GPT", "大模型", "自动驾驶", "半导体", "操作系统", "软件",
             "硬件", "服务器", "数据库", "网络安全", "密码", "开源"],
    "社会": ["通报", "警方", "居民", "事故", "救援", "社区", "调查", "案件",
             "嫌疑人", "受害者", "目击", "报警", "消防", "急救", "伤亡",
             "纠纷", "维权", "投诉", "曝光", "举报", "处罚", "罚款"],
    "国际": ["美国", "韩国", "日本", "联合国", "外交", "总统", "政府",
             "俄罗斯", "乌克兰", "欧盟", "北约", "中东", "朝鲜", "印度",
             "南海", "台海", "制裁", "谈判", "峰会", "访问", "声明", "条约",
             "协议", "冲突", "战争", "撤军", "维和", "难民"],
    "娱乐": ["电影", "导演", "演员", "票房", "奖项", "音乐", "综艺",
             "电视剧", "网剧", "综艺节目", "真人秀", "歌手", "乐队", "演唱会",
             "粉丝", "偶像", "出道", "回归", "专辑", "单曲", "MV", "预告片"],
    "教育": ["学校", "学生", "考试", "高校", "课程", "招生", "高考", "中考",
             "考研", "留学", "专业", "学位", "毕业", "就业", "教师", "教授",
             "教育部", "学区", "学费", "培训", "在线教育", "双减"],
    "健康": ["医院", "医生", "患者", "疾病", "治疗", "药物", "疫苗", "药品",
             "医保", "医疗", "手术", "诊断", "症状", "预防", "康复", "疫情",
             "病毒", "感染", "防控", "口罩", "核酸检测", "新冠"],
    "天气灾害": ["暴雨", "台风", "预警", "降雨", "内涝", "应急", "气象",
               "洪水", "地震", "干旱", "暴雪", "泥石流", "山体滑坡", "龙卷风",
               "冰雹", "寒潮", "高温", "降温", "大风", "降水量", "防汛",
               "抗旱", "受灾", "转移", "安置", "救灾", "灾后重建"],
    "汽车": ["汽车", "新能源", "车企", "销量", "车型", "智能驾驶", "电动车",
             "混动", "纯电", "SUV", "轿车", "MPV", "充电桩", "电池", "续航",
             "百公里", "油耗", "排放", "国六", "特斯拉", "比亚迪"],
    "房地产": ["楼市", "房价", "住房", "楼盘", "土地", "开发商", "二手房",
             "新房", "商品房", "限购", "房贷", "首付", "公积金", "物业",
             "售楼", "开盘", "竣工", "去库存", "棚改", "旧改", "保障房"],
}


def split_sentences(text: str) -> list[str]:
    """Split text into sentences and filter noise lines.

    Cleans source/editor/ads/disclaimer lines, removes URLs,
    filters very short fragments, keeps original order.
    """
    if not text or not text.strip():
        return []

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Split into raw segments
    raw = re.split(r"[。！？；\n]+", text)

    # Filter noise lines
    noise_patterns = [
        r"^(?:责任编辑|责编|编辑|记者|通讯员|作者|来源|出处|转载自|文章来源)[：:].*$",
        r"^（(?:责任编辑|责编|编辑|记者)[^）]*）$",
        r"^【(?:责任编辑|责编|来源|转载)[^】]*】$",
        r"^(?:本文|此文|文章|稿件)(?:来源|来自|转自|转载).*$",
        r"^广告[：:].*$",
        r"^免责声明[：:].*$",
        r"^扫码.*$",
        r"^关注.*(?:公众号|微信|微博).*$",
        r"^\s*$",
    ]

    sentences: list[str] = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        # Check noise
        noisy = False
        for pat in noise_patterns:
            if re.match(pat, s, re.IGNORECASE):
                noisy = True
                break
        if noisy:
            continue
        # Filter very short fragments (likely noise)
        if len(s) < 3:
            continue
        sentences.append(s)

    return sentences


def extract_keywords_fallback(text: str, top_k: int = 8) -> list[dict]:
    """Extract keywords from text using frequency + heuristic scoring.

    Returns list of dicts compatible with Step 2 output:
        [{"word": ..., "weight": ..., "type": "keyword"}, ...]
    """
    if not text or not text.strip():
        return [{"word": "暂无关键词", "weight": 1.0, "type": "keyword"}]

    sentences = split_sentences(text)
    if not sentences:
        return [{"word": "暂无关键词", "weight": 1.0, "type": "keyword"}]

    # Collect candidate phrases (2-6 chars, Chinese)
    candidates: Counter = Counter()
    total_chars = 0

    for sent in sentences:
        # Extract Chinese words (2-6 character sequences)
        chars = re.findall(r"[一-鿿]", sent)
        total_chars += len(chars)
        for span in range(2, 7):
            for i in range(len(chars) - span + 1):
                phrase = "".join(chars[i:i + span])
                if phrase not in _STOP_WORDS and len(phrase) >= 2:
                    candidates[phrase] += 1

    # Also extract number+unit phrases
    number_phrases = re.findall(
        r"(?:[\d]+(?:\.\d+)?(?:%|万|亿|千|百|元|美元|亿元|万元|吨|公里|米|小时|分钟|天|周|月|年|岁|人次|辆|台|架|次|个百分点)?)",
        text,
    )
    for np_ in number_phrases:
        candidates[np_] += 2  # Boost number phrases

    # Institution names via regex
    for pattern in _INSTITUTION_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            if len(m) >= 2:
                candidates[m] += 3  # Boost institution names

    # Score by frequency + position boost (first 3 sentences)
    first_three_text = "".join(sentences[:3])
    scored: list[dict] = []
    max_freq = max(candidates.values()) if candidates else 1

    for phrase, freq in candidates.most_common(top_k * 3):
        # Weight: normalized frequency
        weight = min(1.0, freq / max(max_freq, 1))
        # Position bonus
        if phrase in first_three_text:
            weight = min(1.0, weight + 0.1)
        # Penalize too short
        if len(phrase) < 3:
            weight *= 0.85

        scored.append({
            "word": phrase,
            "weight": round(weight, 2),
            "type": "keyword",
        })

    # Sort by weight descending, take top_k
    scored.sort(key=lambda x: (-x["weight"], -len(x["word"])))
    return scored[:top_k]


def _score_sentence(sentence: str, keywords: Optional[list] = None, position: int = 0) -> float:
    """Score a sentence for relevance to the core news content.

    Scoring factors:
    - Position bonus: first 3 sentences get higher weight
    - Event verb boost
    - Number/date/location/institution presence
    - Keyword hit count
    - Length penalty for too-short or too-long
    """
    score = 0.0
    s = sentence.strip()
    if not s:
        return 0.0

    length = len(s)

    # 1. Position boost
    if position == 0:
        score += 3.0
    elif position <= 2:
        score += 2.0
    elif position <= 5:
        score += 1.0
    elif position <= 10:
        score += 0.5

    # 2. Length scoring (optimal: 25-100 chars)
    if 25 <= length <= 100:
        score += 1.5
    elif 15 <= length < 25:
        score += 0.8
    elif 100 < length <= 180:
        score += 0.5
    elif length < 10:
        score -= 1.0
    elif length > 250:
        score -= 0.5

    # 3. Event verb boost
    for verb in _EVENT_VERBS:
        if verb in s:
            score += 0.6
            break  # one boost for having event verbs

    # 4. Numeric content boost
    if re.search(r"\d+(?:\.\d+)?%?", s):
        score += 0.5
    if re.search(r"(?:\d+万|\d+亿|\d+千|\d+百|\d+元|\d+吨|\d+公里|\d+米|\d+人)", s):
        score += 0.4

    # 5. Date/time mention
    if re.search(r"(?:今日|昨日|近日|本周|今年|\d+年\d+月|\d+月\d+日)", s):
        score += 0.4

    # 6. Location mention
    if re.search(r"(?:在[^\s]{2,10}(?:市|省|区|县|地区|国家|国)|于[^\s]{2,10})", s):
        score += 0.3

    # 7. Institution/person presence
    if re.search(r"(?:[^\s]{2,6}(?:公司|集团|大学|学院|医院|政府|部门|中心|银行|基金|球队|俱乐部|协会|联盟))", s):
        score += 0.4

    # 8. Keyword hits
    if keywords:
        kw_hits = sum(1 for kw in keywords if isinstance(kw, dict) and kw.get("word", "") in s)
        score += kw_hits * 0.5

    # 9. Penalize if looks like boilerplate
    if re.match(r"^(?:据悉|据了解|据报道|据透露|据相关)", s):
        score -= 0.5

    return score


def _compress_to_title(sentence: str, style: str = "客观新闻型") -> str:
    """Compress a sentence into a title by removing modifiers and truncating."""
    s = sentence.strip()

    # Remove common prefixes
    prefixes = [
        r"^(?:据悉|据了解|据报道|据透露|据相关人士|有消息称|记者从[^，。]*获悉|记者[^，。]*报道)",
        r"^(?:近日|日前|昨天|今天|今日|昨日|本周|本月|今年)",
    ]
    for pat in prefixes:
        s = re.sub(pat, "", s).strip()

    # Remove common suffixes
    s = re.sub(r"(?:。|！|？|；)$", "", s).strip()
    s = re.sub(r"（[^）]*）$", "", s).strip()
    s = re.sub(r"\([^)]*\)$", "", s).strip()

    if style == "简洁概括型":
        max_len = 15
    elif style == "客观新闻型":
        max_len = 28
    else:  # 吸引点击型
        max_len = 30

    # Truncate if too long
    if len(s) > max_len:
        # Try to cut at a natural boundary
        s = s[:max_len]
        # Try to end at Chinese char boundary
        while len(s) > 10 and s[-1] in "，、的了对在和是不有或与":
            s = s[:-1]
        s = s.rstrip("，、的了对在和是不有或与")

    # Ensure minimum length
    if len(s) < 5:
        return sentence[:max_len].rstrip("，。！？；")

    # 吸引点击型: add interest markers
    if style == "吸引点击型":
        # Add number emphasis if present
        num_match = re.search(r"(\d+(?:\.\d+)?(?:%|万|亿)?(?:元|美元|亿元|万元)?)", s)
        if num_match and "：" not in s and ":" not in s:
            pass  # keep as-is, numbers are already attention-grabbing

    return s


def extract_elements_fallback(text: str) -> dict:
    """Rule-based 5W1H extraction from news text.

    Returns dict compatible with Step 3 output:
        {"news_elements": {"who": ..., "what": ..., "when": ..., "where": ..., "why": ..., "how": ...}}
    """
    result = {
        "who": "原文未明确说明",
        "what": "原文未明确说明",
        "when": "原文未明确说明",
        "where": "原文未明确说明",
        "why": "原文未明确说明",
        "how": "原文未明确说明",
    }

    if not text or not text.strip():
        return {"news_elements": result}

    sentences = split_sentences(text)
    if not sentences:
        return {"news_elements": result}

    first_three = sentences[:3]

    # ── WHO: institutions, persons, teams ──────────────────
    who_candidates: list[str] = []

    # Institution patterns
    for pattern in _INSTITUTION_PATTERNS:
        for sent in first_three + sentences:
            matches = re.findall(pattern, sent)
            for m in matches:
                if m not in who_candidates:
                    who_candidates.append(m)

    # Person patterns: XX表示, XX称, XX介绍
    person_matches = re.findall(
        r"([^\s，。！？；]{2,6}(?:主席|总统|总理|部长|局长|院长|校长|教授|主任|经理|CEO|创始人|队长|教练|运动员|球员|选手|导演|演员|歌手|发言人|负责人|代表))(?:表示|称|介绍|指出|强调|透露|宣布|回应)",
        text,
    )
    for pm in person_matches:
        if pm not in who_candidates:
            who_candidates.append(pm)

    if who_candidates:
        result["who"] = "、".join(who_candidates[:3])
    elif len(first_three) > 0:
        # Fallback: first 20 chars of first sentence
        result["who"] = first_three[0][:25].rstrip("，。！？；")

    # ── WHAT: core event ─────────────────────────────────
    # Use the highest-scoring sentence as "what"
    best_sent = ""
    best_score = -1
    for i, s in enumerate(sentences):
        sc = _score_sentence(s, position=i)
        if sc > best_score:
            best_score = sc
            best_sent = s
    if best_sent:
        result["what"] = best_sent[:150].rstrip("，。！？；")

    # ── WHEN: date / time ─────────────────────────────────
    time_patterns = [
        r"(\d{4}年\d{1,2}月\d{1,2}日?)",
        r"(\d{4}年\d{1,2}月)",
        r"(\d{4}年)",
        r"(\d{1,2}月\d{1,2}日)",
        r"(今日|昨日|近日|日前|本周|本月|今年|当天|当晚|昨晨|今晨|上午|下午|晚间|夜间)",
        r"(上周|下周|上月|下月|去年|明年|前年)",
        r"(春节|端午|中秋|国庆|元旦|五一|十一|清明|重阳|元宵|圣诞|新年)",
    ]
    when_matches: list[str] = []
    for pat in time_patterns:
        found = re.findall(pat, text)
        when_matches.extend(found)
    if when_matches:
        # Take the most specific match
        when_matches.sort(key=len, reverse=True)
        result["when"] = when_matches[0]
    else:
        result["when"] = "时间未明确"

    # ── WHERE: locations ──────────────────────────────────
    loc_patterns = [
        r"在([^\s，。！？；]{2,15}(?:市|省|区|县|镇|村|地区|国家|国|体育馆|体育场|中心|广场|机场|车站|港口|码头|医院|学校|酒店|大厦|小区|公园|剧场|影院))",
        r"于([^\s，。！？；]{2,15}(?:市|省|区|县|镇|村|地区|国家|国|体育馆|体育场|中心|广场|机场|车站))",
        r"([^\s，。！？；]{2,8}(?:市|省|区|县))(?:政府|公安局|法院|检察院|消防|气象局|教育局|卫健委|市场监管局)",
    ]
    where_found = []
    for pat in loc_patterns:
        for match in re.findall(pat, text):
            if match not in where_found:
                where_found.append(match)
    if where_found:
        result["where"] = "、".join(where_found[:2])
    else:
        result["where"] = "地点未明确"

    # ── WHY: reason ──────────────────────────────────────
    why_patterns = [
        r"(?:因|因为|由于|原因|起因是)[：,]?\s*([^。！？；\n]{10,80})",
        r"(?:为了|旨在|为|目的是|目标是)[：,]?\s*([^。！？；\n]{10,80})",
        r"(?:受[^，。]{2,20}影响)[，,]?\s*([^。！？；\n]{5,60})",
    ]
    for pat in why_patterns:
        match = re.search(pat, text)
        if match:
            result["why"] = match.group(0)[:80].rstrip("，。！？；")
            break
    if result["why"] == "原文未明确说明":
        # Check for causal keywords
        for sent in sentences:
            if any(w in sent for w in ["因为", "由于", "为了", "旨在", "原因是", "起因"]):
                result["why"] = sent[:80].rstrip("，。！？；")
                break

    # ── HOW: method / means ──────────────────────────────
    how_patterns = [
        r"(?:通过|采取|采用|利用|使用|运用|以[^，。]{2,10}方式|以[^，。]{2,10}手段)[，,]?\s*([^。！？；\n]{10,80})",
        r"(?:加强|推进|推动|加快|深化|完善|优化|提升|提高|扩大|减少|降低|促进|支持|保障)[^。！？；]{5,60}",
    ]
    for pat in how_patterns:
        match = re.search(pat, text)
        if match:
            result["how"] = match.group(0)[:80].rstrip("，。！？；")
            break
    if result["how"] == "原文未明确说明":
        for sent in sentences:
            if any(w in sent for w in ["通过", "采取", "利用", "使用", "运用", "加强", "推进", "推动"]):
                result["how"] = sent[:80].rstrip("，。！？；")
                break

    return {"news_elements": result}


def generate_title_summary_fallback(
    text: str,
    params: Optional[dict] = None,
    keywords: Optional[list] = None,
    elements: Optional[dict] = None,
) -> dict:
    """Extractive title and summary generation from input text.

    Uses sentence scoring + extraction — no LLM.
    Returns dict compatible with Step 4 output.
    """
    params = params or {}
    title_count = max(1, min(5, int(params.get("title_count", 3))))
    summary_type = str(params.get("summary_type", "generate"))
    title_style = str(params.get("title_style", "客观新闻型"))
    summary_style = str(params.get("summary_style", "简明扼要"))
    summary_length = str(params.get("summary_length", "both"))

    sentences = split_sentences(text)
    if not sentences:
        return {
            "candidate_titles": ["新闻标题"],
            "summary_short": text[:100] if text else "",
            "summary_long": text[:300] if text else "",
            "summary_points": [],
        }

    # ── Score all sentences ──────────────────────────────
    scored = []
    for i, s in enumerate(sentences):
        score = _score_sentence(s, keywords=keywords, position=i)
        scored.append((i, s, score))

    # Sort by score descending for title selection
    scored_by_score = sorted(scored, key=lambda x: -x[2])

    # ── Generate Titles ──────────────────────────────────
    # Use top-N highest-scoring sentences
    candidate_titles = []
    seen_titles: set = set()
    for idx, sent, score in scored_by_score:
        if len(candidate_titles) >= title_count:
            break
        title = _compress_to_title(sent, style=title_style)
        if title and title not in seen_titles:
            candidate_titles.append(title)
            seen_titles.add(title)

    # Fill remaining slots with next sentences if needed
    if len(candidate_titles) < title_count:
        for i, s in enumerate(sentences):
            if len(candidate_titles) >= title_count:
                break
            title = _compress_to_title(s, style=title_style)
            if title and title not in seen_titles:
                candidate_titles.append(title)
                seen_titles.add(title)

    # ── Generate Summary ─────────────────────────────────
    # Short: top 1-2 highest-scoring sentences, max 100 chars
    # Long: top 3-5 sentences in original order (includes short content but expanded)
    SHORT_MAX = 100
    LONG_MAX = 350

    top_scored = sorted(scored_by_score, key=lambda x: -x[2])

    # ── Short summary ─────────────────────────────────
    # Cap at 2 sentences, but if the text is very short (<= 3 sentences),
    # use only 1 sentence so long summary can be longer
    max_short_sents = 1 if len(sentences) <= 3 else 2
    short_sents: list[str] = []
    short_len = 0
    for idx, s, sc in top_scored:
        if len(short_sents) >= max_short_sents:
            break
        if short_len >= SHORT_MAX:
            break
        s_clean = s.strip()
        if s_clean and s_clean not in short_sents:
            if short_len + len(s_clean) > SHORT_MAX:
                remaining = SHORT_MAX - short_len
                if remaining > 15:
                    s_clean = s_clean[:remaining].rstrip("，；、。！？") + "。"
                else:
                    break
            short_sents.append(s_clean)
            short_len += len(s_clean)

    summary_short = "。".join(short_sents) + "。" if short_sents else (
        sentences[0][:SHORT_MAX].rstrip("，；、。！？") + "。" if sentences else ""
    )

    if summary_style == "客观正式":
        summary_short = f"据报道，{summary_short}" if summary_short else summary_short
    elif summary_style == "通俗易懂":
        summary_short = f"简单来说，{summary_short}" if summary_short else summary_short

    # ── Long summary (includes and expands beyond short) ──
    # Use top 5 sentences in original position order
    top5_idx = {idx for idx, _, sc in top_scored[:5]}
    top5_idx.add(0)
    ordered_idx = sorted(top5_idx)
    ordered_all = [sentences[i].strip() for i in ordered_idx if i < len(sentences) and sentences[i].strip()]

    # Deduplicate while preserving order
    seen: set = set()
    ordered_dedup: list[str] = []
    for s in ordered_all:
        if s not in seen:
            seen.add(s)
            ordered_dedup.append(s)

    long_sents: list[str] = []
    long_len = 0
    for s in ordered_dedup:
        if long_len >= LONG_MAX:
            break
        if long_len + len(s) > LONG_MAX:
            remaining = LONG_MAX - long_len
            if remaining > 15:
                long_sents.append(s[:remaining].rstrip("，；、。！？") + "。")
            break
        long_sents.append(s)
        long_len += len(s)

    summary_long = "。".join(long_sents) + "。" if long_sents else (
        sentences[0][:LONG_MAX].rstrip("，；、。！？") + "。" if sentences else ""
    )

    if summary_style == "客观正式":
        summary_long = f"综合来看，{summary_long}" if summary_long else summary_long
    elif summary_style == "通俗易懂":
        summary_long = f"换句话说，{summary_long}" if summary_long else summary_long

    # ── Ensure long > short ──────────────────────────────
    if len(summary_long) <= len(summary_short) and len(sentences) > 2:
        # Use all sentences as long summary
        all_s = [s.strip() for s in sentences if s.strip()]
        deduped = []
        seen2 = set()
        for s in all_s:
            if s not in seen2:
                seen2.add(s)
                deduped.append(s)
        long_sents2 = []
        llen = 0
        for s in deduped:
            if llen >= LONG_MAX:
                break
            long_sents2.append(s)
            llen += len(s)
        if long_sents2:
            summary_long = "。".join(long_sents2) + "。"
            if summary_style == "客观正式":
                summary_long = f"综合来看，{summary_long}"
            elif summary_style == "通俗易懂":
                summary_long = f"换句话说，{summary_long}"

    # ── Summary Points (not displayed in UI, kept for API compatibility) ──
    summary_points: list = []

    # ── Length control ───────────────────────────────────
    if summary_length == "short":
        summary_long = ""
    elif summary_length == "long":
        summary_short = ""

    return {
        "candidate_titles": candidate_titles,
        "summary_short": summary_short,
        "summary_long": summary_long,
        "summary_points": summary_points,
    }


def match_topic_fallback(text: str, keywords: Optional[list] = None) -> dict:
    """Match news to topic categories based on keyword lexicon.

    Returns dict compatible with Step 5 output.
    """
    if not text or not text.strip():
        return {
            "primary_topic": "综合",
            "secondary_topics": [],
            "confidence": 0.3,
            "topic_category": "综合",
            "matched_from": "关键词词库",
        }

    kw_words: set = set()
    if keywords:
        for k in keywords:
            if isinstance(k, dict):
                kw_words.add(k.get("word", ""))
            elif isinstance(k, str):
                kw_words.add(k)

    # Score each topic category
    topic_scores: Dict[str, float] = {}
    for topic, lexicon in _TOPIC_LEXICON.items():
        score = 0
        hits = 0
        for word in lexicon:
            if word in text:
                score += 1.0
                hits += 1
            if word in kw_words:
                score += 1.5
                hits += 1
        # Normalize by lexicon size
        if hits > 0:
            topic_scores[topic] = min(1.0, score / max(len(lexicon) * 0.1, 1))

    # Sort by score
    sorted_topics = sorted(topic_scores.items(), key=lambda x: -x[1])

    if not sorted_topics or sorted_topics[0][1] < 0.1:
        return {
            "primary_topic": "综合",
            "secondary_topics": [],
            "confidence": 0.3,
            "topic_category": "综合",
            "matched_from": "关键词词库",
        }

    primary = sorted_topics[0][0]
    confidence = round(sorted_topics[0][1], 2)
    secondary = [t for t, s in sorted_topics[1:4] if s > 0.15]

    return {
        "primary_topic": primary,
        "secondary_topics": secondary,
        "confidence": confidence,
        "topic_category": primary,
        "matched_from": "关键词词库",
    }


def judge_timeline_fallback(text: str) -> dict:
    """Judge news timeliness based on time words and progress indicators.

    Returns dict compatible with Step 6 output.
    """
    if not text or not text.strip():
        return {
            "is_timely": True,
            "recommended_position": "一般新闻",
            "time_sensitivity": "中",
            "related_events": [],
            "reason": "无法判断时效性，默认按一般新闻处理",
            "expiration_hours": 48,
        }

    # Check for time words
    urgent_time_words = ["今日", "今天", "刚刚", "最新", "突发", "紧急", "现场", "直播"]
    recent_time_words = ["昨日", "昨天", "近日", "日前", "本周", "本月", "最新", "昨晚", "今晨"]
    older_time_words = ["上周", "上月", "去年", "前年", "往年", "历史"]

    has_urgent = any(w in text for w in urgent_time_words)
    has_recent = any(w in text for w in recent_time_words)

    # Progress indicators
    progress_words = ["首次", "再次", "最新", "公布", "宣布", "启动", "推进", "完成",
                      "回应", "通报", "后续", "进展", "更新", "发布", "披露", "揭晓"]
    has_progress = any(w in text for w in progress_words)

    # Decide timeliness
    if has_urgent:
        is_timely = True
        time_sensitivity = "高"
        recommended_position = "要闻区/头条"
        expiration_hours = 12
        reason = "包含紧急/即时性时间标记"
    elif has_recent and has_progress:
        is_timely = True
        time_sensitivity = "高"
        recommended_position = "要闻区"
        expiration_hours = 24
        reason = "包含近期时间标记且有进展信息"
    elif has_recent:
        is_timely = True
        time_sensitivity = "中"
        recommended_position = "一般新闻"
        expiration_hours = 48
        reason = "包含近期时间标记"
    elif has_progress:
        is_timely = True
        time_sensitivity = "中"
        recommended_position = "一般新闻"
        expiration_hours = 72
        reason = "有进展信息但时间不明确"
    else:
        is_timely = True
        time_sensitivity = "低"
        recommended_position = "一般新闻"
        expiration_hours = 168  # 7 days
        reason = "无明确时间标记，可能为持续性话题"

    # Extract date references as related events
    date_pattern = r"(\d{4}年\d{1,2}月\d{1,2}日?|\d{4}年\d{1,2}月|\d{1,2}月\d{1,2}日)"
    related_dates = re.findall(date_pattern, text)
    related_events = [f"{d}相关报道" for d in related_dates[:3]]

    return {
        "is_timely": is_timely,
        "recommended_position": recommended_position,
        "time_sensitivity": time_sensitivity,
        "related_events": related_events,
        "reason": reason,
        "expiration_hours": expiration_hours,
    }


def check_consistency_fallback(original_text: str, summary: str) -> dict:
    """Lightweight consistency check between summary and original text.

    Uses Jaccard similarity at character/word level.
    Since fallback summaries are extractive (from original text),
    risk is generally low.

    Returns dict compatible with Step 7 output.
    """
    if not original_text or not summary:
        return {
            "risk_level": "low",
            "risk_label": "低风险",
            "check_items": [
                {"name": "标题-正文一致性", "status": "pass", "message": "标题基于原文生成"},
                {"name": "摘要-正文一致性", "status": "pass", "message": "摘要从原文抽取"},
                {"name": "数据准确性", "status": "pass", "message": "数据来源为原文"},
            ],
            "suggestions": [],
            "similarity_map": [],
            "highlight_segments": [],
        }

    # Split summary into sentences
    sum_sents = split_sentences(summary)
    orig_sents = split_sentences(original_text)

    if not sum_sents or not orig_sents:
        return {
            "risk_level": "low",
            "risk_label": "低风险",
            "check_items": [
                {"name": "标题-正文一致性", "status": "warn", "message": "无法进行分析"},
            ],
            "suggestions": [],
            "similarity_map": [],
            "highlight_segments": [],
        }

    # Build character trigram sets for each sentence
    def char_trigrams(s: str) -> set:
        chars = re.sub(r"\s+", "", s)
        return {chars[i:i + 3] for i in range(len(chars) - 2)} if len(chars) >= 3 else {chars}

    orig_trigram_sets = [char_trigrams(s) for s in orig_sents]

    # Calculate Jaccard similarity for each summary sentence
    total_similarity = 0.0
    similarity_map = []
    matched_count = 0

    for ss in sum_sents:
        ss_trigrams = char_trigrams(ss)
        if not ss_trigrams:
            continue

        best_score = 0.0
        best_orig = ""
        for j, os_ in enumerate(orig_sents):
            os_trigrams = orig_trigram_sets[j]
            if not os_trigrams:
                continue
            intersection = len(ss_trigrams & os_trigrams)
            union = len(ss_trigrams | os_trigrams)
            if union == 0:
                continue
            jaccard = intersection / union
            if jaccard > best_score:
                best_score = jaccard
                best_orig = os_[:60]

        total_similarity += best_score

        if best_score >= 0.3:
            sim_type = "match"
            matched_count += 1
        elif best_score >= 0.15:
            sim_type = "drift"
        else:
            sim_type = "hallucination"

        similarity_map.append({
            "summary_sentence": ss[:80],
            "source_sentence": best_orig if best_orig else "无对应",
            "score": round(best_score, 2),
            "type": sim_type,
            "reason": f"字符Jaccard相似度 {best_score:.2f}",
        })

    # Evidence coverage
    coverage = matched_count / max(len(sum_sents), 1)
    coverage = round(coverage, 2)

    # Risk level
    if coverage >= 0.7:
        risk_level = "low"
        risk_label = "低风险"
    elif coverage >= 0.4:
        risk_level = "medium"
        risk_label = "中等风险"
    else:
        risk_level = "high"
        risk_label = "高风险"

    # Check items
    check_items = [
        {
            "name": "标题-正文一致性",
            "status": "pass" if coverage >= 0.7 else "warn",
            "message": f"标题基于原文抽取生成（证据覆盖率 {int(coverage * 100)}%）",
        },
        {
            "name": "摘要-正文一致性",
            "status": "pass" if coverage >= 0.6 else "warn",
            "message": f"摘要与原文证据匹配度 {int(coverage * 100)}%",
        },
        {
            "name": "数据准确性",
            "status": "pass",
            "message": "数据来源为原文" if coverage >= 0.6 else "建议核实关键数据",
        },
    ]

    # Suggestions
    suggestions = []
    if coverage < 0.7:
        suggestions.append("建议人工复核摘要与原文的一致性")
    if len(sum_sents) > len(orig_sents) * 0.8:
        suggestions.append("摘要长度较长，可考虑精简")
    if not suggestions:
        suggestions.append("摘要质量较好，可考虑微调措辞")

    # Highlight segments from original
    highlight_segments = []
    for i, s in enumerate(orig_sents[:8]):
        # Check if this segment is covered by any summary sentence
        s_trigrams = char_trigrams(s)
        max_overlap = 0.0
        for ss in sum_sents:
            ss_trigrams = char_trigrams(ss)
            if not ss_trigrams or not s_trigrams:
                continue
            intersection = len(s_trigrams & ss_trigrams)
            union = len(s_trigrams | ss_trigrams)
            if union > 0:
                overlap = intersection / union
                max_overlap = max(max_overlap, overlap)

        highlight_segments.append({
            "text_range": s[:60],
            "score": round(0.3 + max_overlap * 0.7, 2),
            "covered": max_overlap >= 0.2,
        })

    return {
        "risk_level": risk_level,
        "risk_label": risk_label,
        "check_items": check_items,
        "suggestions": suggestions,
        "similarity_map": similarity_map,
        "highlight_segments": highlight_segments,
    }


def edit_suggestions_fallback(context: dict) -> dict:
    """Generate editing suggestions based on input characteristics.

    Args:
        context: dict with keys like title, summary, summary_long,
                 keywords, topic, consistency, news_elements, text

    Returns dict compatible with Step 8 output.
    """
    title = context.get("title", "") or ""
    summary = context.get("summary", "") or ""
    summary_long = context.get("summary_long", "") or ""
    keywords = context.get("keywords", []) or []
    topic = context.get("topic", {}) or {}
    consistency = context.get("consistency", {}) or {}
    elements = context.get("elements", context.get("news_elements", {})) or {}
    text = context.get("text", "") or ""

    suggestions = []
    overall_score = 75  # Start from a baseline

    # 1. Title check
    if not title:
        suggestions.append({
            "type": "标题缺失",
            "priority": "high",
            "detail": "未生成标题，建议补充",
            "reason": "标题是新闻的第一要素",
        })
        overall_score -= 20
    elif len(title) > 30:
        suggestions.append({
            "type": "标题优化",
            "priority": "medium",
            "detail": f"标题长度 {len(title)} 字，偏长，建议精简至 25 字以内",
            "reason": "过长标题影响阅读体验和SEO",
        })
        overall_score -= 5
    elif len(title) < 8:
        suggestions.append({
            "type": "标题优化",
            "priority": "medium",
            "detail": "标题过短，建议增加关键信息（主体+事件）",
            "reason": "过短标题信息量不足",
        })
        overall_score -= 5
    else:
        overall_score += 5

    # 2. Summary check
    if not summary and not summary_long:
        suggestions.append({
            "type": "摘要缺失",
            "priority": "high",
            "detail": "未生成摘要，建议补充",
            "reason": "摘要是读者快速了解新闻的关键",
        })
        overall_score -= 20
    else:
        main_summary = summary or summary_long
        if len(main_summary) < 30:
            suggestions.append({
                "type": "摘要优化",
                "priority": "medium",
                "detail": "摘要偏短，建议补充更多关键信息",
                "reason": "摘要过于简短可能遗漏重要内容",
            })
            overall_score -= 5
        elif len(main_summary) > 500:
            suggestions.append({
                "type": "摘要优化",
                "priority": "low",
                "detail": "摘要偏长，可考虑删减非核心信息",
                "reason": "过长摘要降低阅读效率",
            })
            overall_score -= 3
        else:
            overall_score += 5

    # 3. Keywords check
    if not keywords:
        suggestions.append({
            "type": "关键词缺失",
            "priority": "medium",
            "detail": "缺少关键词标签，建议添加3-8个关键词",
            "reason": "关键词有助于搜索和分类",
        })
        overall_score -= 5
    else:
        overall_score += 3

    # 4. Elements check (5W1H)
    missing_elements = []
    for key, label in [("who", "主体"), ("what", "事件"), ("when", "时间"),
                        ("where", "地点"), ("why", "原因"), ("how", "方式")]:
        val = elements.get(key, "")
        if not val or val in ("原文未明确说明", "时间未明确", "地点未明确", ""):
            missing_elements.append(label)
    if missing_elements:
        suggestions.append({
            "type": "要素补充",
            "priority": "medium",
            "detail": f"缺少{len(missing_elements)}个新闻要素：{'、'.join(missing_elements)}",
            "reason": "六要素完整性影响新闻质量",
        })
        overall_score -= len(missing_elements) * 3
    else:
        overall_score += 5

    # 5. Consistency result check
    risk_level = consistency.get("risk_level", "low")
    if risk_level == "high":
        suggestions.append({
            "type": "质量警告",
            "priority": "high",
            "detail": "一致性检查风险为高，建议人工全文复核",
            "reason": "高风险报告需要特别关注",
        })
        overall_score -= 15
    elif risk_level == "medium":
        suggestions.append({
            "type": "质量提醒",
            "priority": "medium",
            "detail": "一致性检查存在中等风险项，建议核实关键信息",
            "reason": "中风险项目值得人工审查",
        })
        overall_score -= 5

    # 6. Structure/format suggestions
    if text and len(text) > 2000:
        suggestions.append({
            "type": "结构建议",
            "priority": "low",
            "detail": "原文较长，建议添加小标题分段",
            "reason": "长文分段有助于提高可读性",
        })

    # Clamp score
    overall_score = max(30, min(99, overall_score))

    # Ready to publish?
    ready_to_publish = (
        overall_score >= 65
        and risk_level != "high"
        and len(suggestions) <= 3
    )

    return {
        "suggestions": suggestions,
        "overall_score": overall_score,
        "ready_to_publish": ready_to_publish,
    }
