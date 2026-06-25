# 鍩轰簬澶ц瑷€妯″瀷鐨勬櫤鑳芥柊闂绘憳瑕佷笌鍗忓悓浜掑姩绯荤粺

## 涓€銆侀」鐩畝浠?

鍩轰簬澶ц瑷€妯″瀷鐨勬櫤鑳芥柊闂绘憳瑕佷笌鍗忓悓浜掑姩绯荤粺鏄竴涓潰鍚戞柊闂绘祻瑙堛€丄I 鏍囬鎽樿鐢熸垚鍜岀ぞ鍖轰簰鍔ㄧ殑鍓嶅悗绔垎绂荤郴缁熴€?

绯荤粺瑙勫垝鍖呭惈棣栭〉鏂伴椈娴忚銆佹柊闂昏鎯呫€丄I 鏍囬鎽樿鐢熸垚銆佺ぞ鍖轰簰鍔ㄣ€佷釜浜轰腑蹇冨拰绠＄悊鍚庡彴绛夋ā鍧楋紝鐜板凡瀹屾垚 **AI 鏍囬鎽樿鐢熸垚妯″潡鍏ㄥ姛鑳藉疄鐜?*锛堝寘鎷姩鎬?Mock 鍜屾櫤璋?GLM-4-Flash 鐪熷疄 LLM 璋冪敤锛夛紝鍚庣画灏嗙户缁畬鍠勫叾浠栨ā鍧椼€?

## 浜屻€侀」鐩畾浣?

绯荤粺鍥寸粫鈥濇柊闂绘祻瑙堚€旀柊闂昏鎯呬簰鍔ㄢ€擜I 鐢熸垚鈥旂ぞ鍖轰氦娴佲€斾釜浜鸿褰曠鐞嗏€濈殑闂幆灞曞紑锛岀粨鍚堟柊闂诲唴瀹规秷璐广€佹櫤鑳界敓鎴愯兘鍔涘拰鐢ㄦ埛鍗忓悓浜掑姩锛屼负鐢ㄦ埛鎻愪緵杩炶疮鐨勬柊闂婚槄璇讳笌浜ゆ祦浣撻獙銆?

## 涓夈€佹妧鏈爤瑙勫垝

### 鍓嶇

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Element Plus
- Axios

### 鍚庣

- Python
- FastAPI
- Pydantic
- Uvicorn
- 鍚庣画鎺ュ叆 MySQL

### AI 鏈嶅姟

- FastAPI
- **褰撳墠鏀寔**锛氬姩鎬?Mock锛堝揩閫熸紨绀猴級+ 鏅鸿氨 GLM-4-Flash锛堢湡瀹?AI锛?
- 鍙厤缃垏鎹袱绉嶆ā寮忥紝LLM 璋冪敤澶辫触鏃惰嚜鍔?fallback 鍒?Mock

### 閮ㄧ讲

- 鍚庣画浣跨敤 Nginx
- 鍚庣画鍙娇鐢?Docker / Docker Compose

## 鍥涖€佺洰褰曠粨鏋?

```text
llm-news-summary-collaboration-system/
鈹溾攢鈹€ frontend/     # 鍓嶇椤圭洰
鈹溾攢鈹€ backend/      # 鍚庣涓氬姟鏈嶅姟
鈹溾攢鈹€ ai-service/   # AI 妯″瀷璋冪敤鏈嶅姟锛堟敮鎸?Mock + LLM锛?
鈹溾攢鈹€ docs/         # 椤圭洰鏂囨。锛堝寘鍚紑鍙戦樁娈佃鏄庯級
鈹溾攢鈹€ deploy/       # 閮ㄧ讲閰嶇疆
鈹溾攢鈹€ scripts/      # 寮€鍙戣剼鏈?
鈹斺攢鈹€ README.md     # 椤圭洰璇存槑
```

| 鐩綍 | 璇存槑 |
| --- | --- |
| `frontend` | 鍓嶇椤圭洰锛岃礋璐ｇ敤鎴风晫闈㈠拰鍓嶇浜や簰銆?|
| `backend` | 鍚庣涓氬姟鏈嶅姟锛屾彁渚?API 杞彂鍜屼笟鍔￠€昏緫銆?|
| `ai-service` | AI 妯″瀷璋冪敤鏈嶅姟锛屾敮鎸?Mock 鍜屾櫤璋?GLM-4-Flash 涓ょ妯″紡銆?|
| `docs` | 椤圭洰鏂囨。锛屽寘鍚渶姹傘€佽璁°€佹帴鍙ｅ拰鍚勯樁娈靛畬鎴愯鏄庛€?|
| `deploy` | 閮ㄧ讲閰嶇疆锛屽悗缁瓨鏀?Nginx銆丏ocker 绛夋枃浠躲€?|
| `scripts` | 寮€鍙戣剼鏈紝鍖呭惈娴嬭瘯鍜屽伐鍏疯剼鏈€?|

## 浜斻€佸紑鍙戦樁娈?

| 闃舵 | 璇存槑 | 鐘舵€?|
| --- | --- | --- |
| 绗?0 闃舵 | 椤圭洰鎬婚鏋舵惌寤?| 鉁?宸插畬鎴?|
| 绗?1 闃舵 | 鍓嶇鍩虹妗嗘灦鎼缓 | 鉁?宸插畬鎴?|
| 绗?2 闃舵 | 鍚庣 FastAPI 鍩虹妗嗘灦鎼缓 | 鉁?宸插畬鎴?|
| 绗?3 闃舵 | AI 鏈嶅姟妗嗘灦鎼缓 | 鉁?宸插畬鎴?|
| 绗?4 闃舵 | 鐢ㄦ埛涓庢潈闄?Mock 鎼缓 | 鉁?宸插畬鎴?|
| **绗?5 闃舵** | **AI 鏍囬鎽樿鐢熸垚妯″潡** | **鉁?宸插畬鎴?* |
| 绗?6 闃舵 | 鏁版嵁搴撴帴鍏ヤ笌鑱旇皟 | 寰呭紑濮?|

## 鍏€佸綋鍓嶉樁娈佃鏄?

### 鉁?绗?0-5 闃舵宸插畬鎴?

**鍩虹妗嗘灦**锛氶」鐩叿澶囧畬鏁寸殑鐩綍楠ㄦ灦銆乂ue 3 鍓嶇妗嗘灦銆丗astAPI 鍚庣妗嗘灦鍜岀嫭绔?AI 鏈嶅姟妗嗘灦銆?

**AI 鏍囬鎽樿鐢熸垚妯″潡**锛堢 5 闃舵锛屾渶鏂板畬鎴愶級锛?
- 鉁?**鍓嶇 UI**锛氬畬鏁寸殑杈撳叆銆佸弬鏁般€佺粨鏋溿€佸巻鍙茬鐞嗙晫闈?
- 鉁?**Mock 妯″紡**锛氬姩鎬佺敓鎴愭爣棰樸€佹憳瑕併€佸叧閿瘝銆佽绱犮€佷竴鑷存€ф鏌ワ紙蹇€熻繑鍥烇紝<100ms锛?
- 鉁?**LLM 妯″紡**锛氭帴鍏ユ櫤璋?GLM-4-Flash锛岀湡瀹?AI 鐢熸垚锛?-5s锛?
- 鉁?**Fallback 鏈哄埗**锛歀LM 澶辫触鑷姩闄嶇骇鍒?Mock锛岀敤鎴锋棤鎰熺煡
- 鉁?**瓒呮椂澶勭悊**锛氬垎灞傝秴鏃堕厤缃紙鍓嶇 60s銆佸悗绔?60s銆乤i-service LLM 45s锛?
- 鉁?**鏂伴椈璇︽儏椤甸泦鎴?*锛氫竴閿鍏ユ鏂囷紝鏃犵紳璺宠浆
- 鉁?**鐢熸垚鍘嗗彶绠＄悊**锛氭煡鐪嬨€佸鐢ㄣ€佸垹闄ゅ巻鍙茶褰?
- 鉁?**閿欒澶勭悊**锛氬弸濂界殑瓒呮椂鎻愮ず鍜岄敊璇檷绾?

**鐢ㄦ埛鏉冮檺绯荤粺**锛堢 4 闃舵锛夛細Mock 鐧诲綍銆佺敤鎴风姸鎬佺鐞嗐€佽矾鐢卞畧鍗€佽鑹叉潈闄愭帶鍒躲€?

### 馃攼 娴嬭瘯璐﹀彿

| 瑙掕壊 | 鐢ㄦ埛鍚?| 瀵嗙爜 |
| --- | --- | --- |
| 鏅€氱敤鎴?| `user` | `123456` |
| 瀹℃牳缂栬緫 | `editor` | `123456` |
| 绠＄悊鍛?| `admin` | `123456` |

## 涓冦€佸揩閫熷紑濮?

### 7.1 鍓嶇鍚姩

```bash
cd frontend
npm install
npm run dev
```

绗簩娆″惎鍔細
```bash
cd frontend
npm run dev
```

璁块棶 [http://localhost:5173](http://localhost:5173)

### 7.2 鍚庣鍚姩

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

绗簩娆¤繍琛岋細
```bash
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

鍚姩鍚庡彲璁块棶锛?
- 鍋ュ悍妫€鏌ワ細[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Swagger 鏂囨。锛歔http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7.3 AI 鏈嶅姟鍚姩锛堥噸瑕?猸愶級

```bash
cd ai-service

# 绗?1 姝ワ細瀹夎渚濊禆
pip install -r requirements.txt

# 绗?2 姝ワ細閰嶇疆 .env 鏂囦欢
cp .env.example .env

# 绗?3 姝ワ細缂栬緫 .env锛堝彲閫夛級
# 濡傛灉瑕佷娇鐢ㄧ湡瀹?LLM锛堟櫤璋?GLM-4-Flash锛夛細
#   1. 娉ㄥ唽 https://open.bigmodel.cn/
#   2. 鍒涘缓 API Key
#   3. 缂栬緫 ai-service/.env锛?
#      LLM_ENABLED=true
#      LLM_API_KEY=sk-浣犵殑瀹為檯APIKey
# 
# 濡傛灉鍙兂蹇€熸祴璇曪紝淇濇寔榛樿閰嶇疆锛?
#   LLM_ENABLED=false 锛堜娇鐢ㄥ姩鎬?Mock锛?

# 绗?4 姝ワ細鍚姩 AI 鏈嶅姟
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 7.4 璁块棶搴旂敤

鍚姩鎵€鏈変笁涓湇鍔″悗锛岃闂細

- **鍓嶇涓婚〉**锛歔http://localhost:5173](http://localhost:5173)
- **AI 鐢熸垚椤?*锛歔http://localhost:5173/ai/title-summary](http://localhost:5173/ai/title-summary)
- **鍚庣 API**锛歔http://127.0.0.1:8000](http://127.0.0.1:8000)
- **AI 鏈嶅姟**锛歔http://127.0.0.1:8001](http://127.0.0.1:8001)

---

## 鍏€丄I 鏍囬鎽樿鐢熸垚妯″潡璇存槑

### 鍔熻兘姒傝

鍦?`/ai/title-summary` 椤甸潰锛岀敤鎴峰彲浠ワ細
1. 鎵嬪姩杈撳叆鎴栦粠鏂伴椈璇︽儏椤靛鍏ユ鏂?
2. 閫夋嫨鍙傛暟锛氭爣棰樻暟銆佹憳瑕侀鏍笺€佹憳瑕佺被鍨嬬瓑
3. 鐐瑰嚮鐢熸垚锛岃幏寰楋細
   - 澶氫釜鍊欓€夋爣棰?
   - 鐭?闀挎憳瑕?
   - 鎽樿瑕佺偣
   - 鍏抽敭璇?
   - 鏂伴椈鍏绱狅紙Who/What/When/Where/Why/How锛?
   - 涓€鑷存€ц瘎鍒嗗拰鏀硅繘寤鸿
4. 鏌ョ湅鍜屽鐢ㄧ敓鎴愬巻鍙?

### 宸ヤ綔妯″紡

#### 妯″紡 1锛氬姩鎬?Mock锛堟帹鑽愬揩閫熸祴璇曪級

```bash
# .env 閰嶇疆
LLM_ENABLED=false

# 鐗圭偣
鉁?蹇€熻繑鍥烇紙<100ms锛?
鉁?鏃犻渶閰嶇疆 API Key
鉁?鍩轰簬瑙勫垯鐢熸垚锛屾晥鏋滄紨绀?
鉁?鑷姩闄嶇骇鐩爣

# 鐢ㄩ€?
婕旂ず瀹屾暣鍔熻兘銆佸揩閫熷師鍨嬮獙璇併€佸湪绾挎紨绀?
```

#### 妯″紡 2锛氱湡瀹?LLM锛堟櫤璋?GLM-4-Flash锛?

```bash
# .env 閰嶇疆
LLM_ENABLED=true
LLM_API_KEY=sk-浣犵殑瀹為檯APIKey

# 鐗圭偣
鉁?鐪熷疄 AI 鐢熸垚锛?-5绉掞級
鉁?鏇存櫤鑳界殑鏍囬鍜屾憳瑕?
鉁?鐪熷疄鐨勫叧閿瘝鍜岃绱犳彁鍙?
鉁?澶辫触鑷姩 fallback 鍒?Mock

# 瑕佹眰
1. 鎷ユ湁鏅鸿氨 API Key锛坔ttps://open.bigmodel.cn/锛?
2. 缃戠粶杩炴帴姝ｅ父
3. 鎰挎剰绛夊緟 2-5 绉掑搷搴旀椂闂?

# 鐢ㄩ€?
鐢熶骇鐜銆佺湡瀹炲簲鐢ㄣ€佹櫤鑳戒綋楠?
```

### 閰嶇疆璇﹁В

**ai-service/.env 鍏抽敭閰嶇疆**锛?

```env
# 鍚敤/绂佺敤 LLM
LLM_ENABLED=false      # false: Mock 妯″紡, true: LLM 妯″紡

# 鏅鸿氨 API 閰嶇疆锛堜粎 LLM_ENABLED=true 鏃堕渶瑕侊級
LLM_API_KEY=sk-浣犵殑APIKey          # 浠?https://open.bigmodel.cn/ 鑾峰彇
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/  # 瀹樻柟 API 鍦板潃
LLM_MODEL=glm-4-flash              # 浣跨敤鐨勬ā鍨?

# 瓒呮椂鍜屾€ц兘閰嶇疆
LLM_TIMEOUT=45                     # LLM 璋冪敤瓒呮椂鏃堕棿锛堢锛?
LLM_TEMPERATURE=0.3                # 鐢熸垚娓╁害锛?=纭畾鎬э紝1=闅忔満鎬э級
LLM_MAX_TOKENS=2048                # 鏈€澶ц緭鍑?Token 鏁?

# 鍏朵粬閰嶇疆
LLM_THINKING_TYPE=disabled         # 鎬濈淮閾剧被鍨?
```

**鍓嶇瓒呮椂閰嶇疆锛堣嚜鍔紝鏃犻渶淇敼锛?*锛?
- AI 鐢熸垚鎺ュ彛锛?0 绉?
- 鍏朵粬鎺ュ彛锛?0 绉?

**鍚庣瓒呮椂閰嶇疆锛堣嚜鍔紝鏃犻渶淇敼锛?*锛?
- AI 杞彂锛?0 绉?
- 鍏朵粬鎺ュ彛锛?0 绉?

### 濡備綍鑾峰彇鏅鸿氨 API Key

1. 璁块棶 [https://open.bigmodel.cn/](https://open.bigmodel.cn/)
2. 娉ㄥ唽璐﹀彿
3. 鍒涘缓 API Key
4. 澶嶅埗 Key 鍊煎埌 `ai-service/.env`锛歚LLM_API_KEY=sk-...`

### 鏁呴殰鎺掓煡

| 闂 | 鍘熷洜 | 瑙ｅ喅鏂规 |
| --- | --- | --- |
| 鈥渢imeout of 10000ms exceeded鈥?| 鍓嶇瓒呮椂 | 妫€鏌?ai-service 鏄惁鍚姩涓旂綉缁滄甯?|
| 鈥淎I 鏈嶅姟鏆傛椂涓嶅彲鐢ㄢ€?| LLM 璋冪敤澶辫触 | 妫€鏌?API Key 鎴栫綉缁滐紝fallback 鍒?Mock 搴旇鏈夋晥 |
| 鐢熸垚閫熷害鎱紙>10s锛?| 缃戠粶寤惰繜鎴?LLM 绻佸繖 | 灞炴甯哥幇璞★紝鍙皾璇曠缉鐭緭鍏ユ枃鏈?|
| 杩斿洖 Mock 鑰屼笉鏄?LLM | LLM 璋冪敤澶辫触鑷姩 fallback | 妫€鏌?API Key 鍜岀綉缁滐紝鎴栦娇鐢?LLM_ENABLED=false 妯″紡 |

---

## 涔濄€侀」鐩枃妗?

璇︾粏鐨勫紑鍙戞枃妗ｄ綅浜?`docs/` 鐩綍锛?

- `README.md` - 椤圭洰姒傝堪
- `api.md` - 鎺ュ彛鏂囨。
- `development_plan.md` - 寮€鍙戣鍒?
- `development_standard.md` - 寮€鍙戣鑼?
- `ai_module_guide.md` - AI 妯″潡浣跨敤鎸囧崡
- `stage_9_3_summary.md` - 闃舵 9.3 瀹屾垚璇存槑锛圠LM 鎺ュ叆锛?
- `stage_9_4_timeout_fix.md` - 闃舵 9.4 瀹屾垚璇存槑锛堣秴鏃朵慨澶嶏級
- `stage_9_4_quick_reference.md` - 蹇€熷弬鑰冨崱鐗?

## 鍗併€佺壒鍒鏄?

### 鈿狅笍 .env 鏂囦欢澶勭悊

**閲嶈**锛歚ai-service/.env` 鍖呭惈鏁忔劅淇℃伅锛圓PI Key锛夛紝**涓嶄細琚彁浜ゅ埌 Git**銆?

浣跨敤姝ら」鐩椂锛?
1. 鑷姩鐢熸垚鐨?`.env.example` 鍖呭惈閰嶇疆妯℃澘
2. 鍏嬮殕椤圭洰鍚庯紝澶嶅埗 `.env.example` 涓?`.env`
3. 缂栬緫 `.env`锛屽～鍏ヤ綘鐨?API Key锛堝彲閫夛紝榛樿浣跨敤 Mock锛?
4. `.env` 宸插湪 `.gitignore` 涓紝涓嶄細琚彁浜?

### 馃攧 宸ヤ綔娴佺▼

```
鍏嬮殕椤圭洰
    鈫?
cp ai-service/.env.example ai-service/.env
    鈫?
缂栬緫 ai-service/.env锛堝彲閫夛級
    鈫?
鍚姩鍓嶇銆佸悗绔€乤i-service
    鈫?
璁块棶 http://localhost:5173
    鈫?
娴嬭瘯 AI 鐢熸垚鍔熻兘
```

---

## 鍗佷竴銆佸悗缁鍒?

- 绗?6 闃舵锛氭暟鎹簱鎺ュ叆涓庡巻鍙叉寔涔呭寲
- 绗?7 闃舵锛氱ぞ鍖轰簰鍔ㄦā鍧?
- 绗?8 闃舵锛氱敤鎴蜂腑蹇冨拰鍐呭绠＄悊
- 鏀寔鏇村 LLM 鏈嶅姟鍟嗭紙OpenAI銆佹枃蹇冧竴瑷€绛夛級
- 鐢熸垚缁撴灉缂撳瓨浼樺寲
- 鐢ㄦ埛鍙嶉鍜岃瘎鍒嗙郴缁?

---

## 鍗佷簩銆佽鍙瘉

椤圭洰閲囩敤 MIT 璁稿彲璇併€傝瑙?LICENSE 鏂囦欢銆?

---

**绁濅綘浣跨敤鎰夊揩锛?* 馃殌

鏈変换浣曢棶棰樻垨寤鸿锛屾杩庢彁浜?Issue銆?

## 闄勫綍锛氭暟鎹簱鍒濆鍖栦笌瀵煎叆娴佺▼

杩欎竴閮ㄥ垎琛ュ厖椤圭洰鐜板湪宸茬粡钀藉湴鐨勬暟鎹簱鎿嶄綔娴佺▼銆傚綋鍓嶆暟鎹簱闃舵宸茬粡瀹屾垚浜嗏€滃缓搴撱€佸缓琛ㄣ€佸鍏ュ熀纭€鏁版嵁鈥濅笁姝ワ紝鍚庣画鍙鎸夌収涓嬮潰椤哄簭鎵ц鍗冲彲銆?

### A. 鍏堢‘璁?MySQL 鍙敤

鍦?Windows PowerShell 涓嬶紝鍏堢‘璁?MySQL 瀹㈡埛绔兘姝ｅ父杩炴帴锛?

```powershell
mysql -u llm_news_user -p llm_news_system
```

杈撳叆瀵嗙爜锛?

```text
123456
```

濡傛灉宸茬粡鑳芥甯歌繘鍏ユ暟鎹簱锛岃鏄庤处鍙枫€佹巿鏉冨拰鏁版嵁搴撻兘宸茬粡灏辩华銆?

### B. 瀵煎叆鏁版嵁搴撹〃缁撴瀯

濡傛灉浣犳槸绗竴娆″湪鏈湴鎼缓锛屽厛鎵ц琛ㄧ粨鏋勮剼鏈細

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
```

杈撳叆瀵嗙爜锛?

```text
123456
```

璇存槑锛?

- 鐢变簬 PowerShell 涓嶆敮鎸佺洿鎺ヤ娇鐢?`<` 閲嶅畾鍚戯紝鎵€浠ヨ繖閲岀敤鐨勬槸 `cmd /c`
- `--default-character-set=utf8mb4` 鏄负浜嗛伩鍏嶄腑鏂囧瓧娈靛鍏ユ姤瀛楃闆嗛敊璇?

### C. 瀵煎叆鍩虹绉嶅瓙鏁版嵁

琛ㄧ粨鏋勫鍏ュ畬鎴愬悗锛屽啀瀵煎叆鍩虹鏁版嵁锛?

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

杈撳叆瀵嗙爜锛?

```text
123456
```

### D. 濡傛灉浣犻亣鍒颁腑鏂囨姤閿?

濡傛灉瀵煎叆 `seed.sql` 鏃跺嚭鐜扮被浼?`Incorrect string value` 鐨勬姤閿欙紝浼樺厛妫€鏌ヤ互涓嬪嚑鐐癸細

1. 浣跨敤鐨勬槸 `--default-character-set=utf8mb4`
2. `database/schema.sql` 鍜?`database/seed.sql` 閮芥槸 UTF-8 缂栫爜
3. 缁堢娌℃湁鎶婁腑鏂囧瓧绗﹂泦杞崲鎴愬埆鐨勭紪鐮?

浣犱篃鍙互鏀圭敤 PowerShell 绠￠亾鏂瑰紡锛?

```powershell
chcp 65001
Get-Content database\seed.sql | mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system
```

### E. 瀵煎叆瀹屾垚鍚庣殑楠岃瘉鍛戒护

瀵煎叆瀹屾瘯鍚庯紝寤鸿鎵ц杩欎簺 SQL 鐪嬩竴涓嬪熀纭€鏁版嵁鏄惁姝ｅ父锛?

```sql
SELECT COUNT(*) FROM user;
SELECT COUNT(*) FROM news_category;
SELECT COUNT(*) FROM news_topic;
SELECT COUNT(*) FROM news;
SELECT COUNT(*) FROM news_comment;
SELECT COUNT(*) FROM hot_topic;
SELECT COUNT(*) FROM event_timeline;
```

濡傛灉鏁伴噺姝ｅ父锛岃鏄庢暟鎹簱鍩虹鐜宸茬粡鍙互鏀拺鍚庣画寮€鍙戝拰鑱旇皟銆?

### F. 鎺ㄨ崘鐨勫畬鏁存墽琛岄『搴?

```text
1. 鍚姩 MySQL
2. 鍒涘缓鏁版嵁搴撳拰璐﹀彿
3. 瀵煎叆 database/schema.sql
4. 瀵煎叆 database/seed.sql
5. 鍚姩 backend
6. 鍚姩 frontend
7. 鍚姩 ai-service
8. 璁块棶 http://localhost:5173
```

### G. 鐩墠鏁版嵁搴撻樁娈电殑鐘舵€?

- 鏁版嵁搴撳凡寤哄ソ
- 椤圭洰璐﹀彿宸插垱寤?
- 琛ㄧ粨鏋勫凡鍒涘缓
- 鍩虹鏁版嵁宸插鍏ユ垨鍙寜涓婇潰鐨勫懡浠ら噸鏂板鍏?
- 鍚庣画濡傛灉缁х画鍋氳仈璋冿紝浼樺厛妫€鏌?`seed.sql` 鐨勫鍏ユ槸鍚︽垚鍔?

### H. 绗竴娆℃搷浣滄祦绋?

濡傛灉杩欐槸浣犵涓€娆″湪鏈湴鍒濆鍖栬繖涓」鐩紝寤鸿鎸変笅闈㈤『搴忓仛涓€閬嶏細

```text
1. 鎵撳紑 MySQL 鏈嶅姟
2. 鍒涘缓鏁版嵁搴撳拰椤圭洰璐﹀彿
3. 瀵煎叆 database/schema.sql
4. 瀵煎叆 database/seed.sql
5. 妫€鏌ユ暟鎹簱琛ㄥ拰鍩虹鏁版嵁鏄惁姝ｅ父
6. 閰嶇疆 backend/.env
7. 鍚姩 backend
8. 鍚姩 frontend
9. 鍚姩 ai-service
10. 鎵撳紑 http://localhost:5173 杩涜娴嬭瘯
```

绗竴娆℃搷浣滄椂閲嶇偣鍏虫敞涓や欢浜嬶細

- `schema.sql` 鏄惁鎴愬姛鎵ц
- `seed.sql` 鏄惁鍥犱负瀛楃闆嗘垨鏉冮檺闂瀵煎叆澶辫触

濡傛灉 `seed.sql` 瀵煎叆鏃舵姤涓枃瀛楃閿欒锛屼紭鍏堜娇鐢ㄤ笅闈㈣繖绉嶆柟寮忥細

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

### I. 鎿嶄綔杩囦竴娆′箣鍚庣殑甯歌娴佺▼

濡傛灉鏁版嵁搴撳凡缁忓垱寤鸿繃銆佽〃缁撴瀯涔熷凡缁忓瓨鍦紝鍚庣画姣忔鏈湴鍚姩鍙互鐩存帴鎸夊父瑙勬祦绋嬫潵锛?

```text
1. 鍚姩 MySQL
2. 妫€鏌ユ暟鎹簱鏈嶅姟鏄惁鍦ㄧ嚎
3. 濡傛湁闇€瑕侊紝鍐嶅鍏ユ柊鐨?seed 鏁版嵁
4. 鍚姩 backend
5. 鍚姩 frontend
6. 鍚姩 ai-service
7. 鎵撳紑 http://localhost:5173
```

甯歌娴佺▼閲岋紝涓€鑸笉闇€瑕佹瘡娆￠兘閲嶆柊鎵ц `schema.sql`锛屽洜涓洪偅浼氶噸寤鸿〃缁撴瀯锛涘彧鏈夊湪浣犳兂閲嶇疆鏁版嵁搴撴椂鎵嶉噸鏂板鍏ャ€?

濡傛灉浣犲彧鏄兂鍒锋柊鍩虹鏁版嵁锛屽彲浠ュ崟鐙墽琛岋細

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

鏇寸ǔ濡ョ殑涔犳儻鏄細

- 绗竴娆℃惌寤猴細鍏?`schema.sql`锛屽啀 `seed.sql`
- 鏃ュ父鍚姩锛氬厛鏈嶅姟锛屽啀鍓嶇
- 鎯抽噸缃暟鎹細閲嶆柊瀵煎叆 `seed.sql`

### J. 绗竴娆℃搷浣滃懡浠ゆ竻鍗?

濡傛灉浣犳槸绗竴娆″畬鏁村垵濮嬪寲鏈」鐩紝寤鸿鐩存帴鎸変笅闈㈠懡浠ら『搴忔墽琛岋細

```powershell
# 1. 杩涘叆椤圭洰鏍圭洰褰?
cd .

# 2. 鍚姩 MySQL 鍚庯紝鍏堝鍏ヨ〃缁撴瀯
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"

# 3. 鍐嶅鍏ュ熀纭€鏁版嵁
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"

# 4. 楠岃瘉鏁版嵁鏄惁瀵煎叆鎴愬姛
cmd /c 'mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e "SELECT COUNT(*) FROM user; SELECT COUNT(*) FROM news; SELECT COUNT(*) FROM news_topic;"'

# 5. 鍚姩鍚庣
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 6. 鍚姩鍓嶇
cd ..\frontend
npm install
npm run dev

# 7. 鍚姩 AI 鏈嶅姟
cd ..\ai-service
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

濡傛灉浣犲湪 PowerShell 閲岀洿鎺ヨ繍琛?MySQL 瀵煎叆鍛戒护鎶ョ孩锛屼紭鍏堜娇鐢ㄤ笂闈㈢殑 `cmd /c` 鐗堟湰銆?

### K. 甯歌鎿嶄綔鍛戒护娓呭崟

濡傛灉鏁版嵁搴撳拰鍩虹鏁版嵁宸茬粡鍒濆鍖栬繃锛屾棩甯稿惎鍔ㄤ竴鑸彧闇€瑕佽繖浜涘懡浠わ細

```powershell
# 1. 鍚姩鍚庣
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. 鍚姩鍓嶇
cd frontend
npm run dev

# 3. 鍚姩 AI 鏈嶅姟
cd ai-service
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

濡傛灉浣犳兂鍒锋柊鍩虹鏁版嵁锛屽彧鎵ц涓嬮潰杩欎竴鏉″嵆鍙細

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

甯歌鎿嶄綔閲岄€氬父涓嶉渶瑕侀噸澶嶆墽琛?`schema.sql`锛岄櫎闈炰綘瑕侀噸寤烘暣濂楄〃缁撴瀯銆?

---

## 附录补充：当前版本启动、数据库与爬虫操作说明

> 本节是在保留 README 原有内容基础上的最新补充。如果上文旧命令或阶段状态与本节冲突，请以本节为准。

### 1. 当前功能完成状态

当前系统已完成前后端基础框架、AI 服务、数据库接入、新闻浏览、新闻互动、AI 生成、个人中心、Timeline、社区互动和权限控制等核心功能。

当前数据库化联调状态：

- 新闻模块：数据库优先，mock 兜底。
- 新闻互动：数据库优先，mock 兜底。
- 个人中心：数据库优先，mock 兜底。
- AI 生成记录：生成成功后写入 `ai_generate_record`。
- Timeline：数据库优先，mock 兜底。
- 社区模块：数据库优先，mock 兜底。
- 登录鉴权：优先读取 `user` 表，同时兼容 `mock-token-user`、`mock-token-editor`、`mock-token-admin`。
- RSS 爬虫：支持 `source_url` 去重、正文解析、封面图提取、`crawl_log` 日志和旧新闻归档。

开发阶段状态：

| 阶段 | 说明 | 状态 |
| --- | --- | --- |
| 第 0 阶段 | 项目总骨架搭建 | 已完成 |
| 第 1 阶段 | 前端基础框架搭建 | 已完成 |
| 第 2 阶段 | 后端 FastAPI 基础框架搭建 | 已完成 |
| 第 3 阶段 | AI 服务框架搭建 | 已完成 |
| 第 4 阶段 | 用户与权限 mock 搭建 | 已完成 |
| 第 5 阶段 | 核心模块并行开发 | 已完成 |
| 第 6 阶段 | 数据库接入与联调 | 已完成 |

数据库化阶段补充：

- DB4：新闻模块数据库化，已完成。
- DB5：新闻互动与个人中心数据库化，已完成。
- DB7：AI 生成记录落库，已完成。
- DB8：Timeline 数据库化，已完成。
- DB9：社区模块数据库化，已完成。
- DB10：登录鉴权优先读取 `user` 表，已完成。
- DB11：全项目数据库化联调验收，已完成。
- DB12：真实新闻展示与爬虫质量修复，已完成。
- DB12.5：首页真实数据展示、侧边栏分类、热榜和订阅管理修复，已完成。

### 2. 技术栈补充

后端与数据库当前使用：

- FastAPI
- Pydantic
- Uvicorn
- MySQL 8.0
- PyMySQL
- python-dotenv
- 数据库优先 + mock 兜底

AI 服务说明保留原有设计：

- 支持动态 Mock。
- 支持 GLM-4-Flash。
- LLM 调用失败时 fallback 到 Mock。
- AI 生成成功后，backend 会将生成记录保存到 `ai_generate_record` 表，个人中心可以查看生成历史。
- 如果 ai-service 未启动，backend 会返回友好的 503 错误，不会导致 backend 崩溃。

### 3. 目录结构补充

```text
database/        数据库 schema、seed、migrations
scripts/         RSS 新闻爬虫和工具脚本
```

### 4. 第一次完整操作流程

#### 4.1 创建数据库和项目账号

先进入 MySQL：

```powershell
mysql -u root -p
```

说明：

- root 密码使用你自己本机 MySQL 的 root 密码。
- README 不记录 MySQL root 密码。

进入 MySQL 后执行：

```sql
CREATE DATABASE IF NOT EXISTS llm_news_system
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'llm_news_user'@'localhost'
IDENTIFIED BY '123456';

GRANT ALL PRIVILEGES ON llm_news_system.* TO 'llm_news_user'@'localhost';

FLUSH PRIVILEGES;

exit;
```

#### 4.2 导入表结构和基础数据

PowerShell 中不要直接使用 `<`，请使用 `cmd /c` 包装：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

输入项目数据库密码：

```text
123456
```

注意：

- `seed.sql` 主要用于第一次初始化基础数据。
- 不建议在已有业务数据上随意反复执行 `seed.sql`。
- 如果确实需要重置数据库，建议先备份，再重新执行 `schema.sql`、`seed.sql` 和 migrations。

#### 4.3 按顺序执行 migrations

请以 `database/migrations/` 目录中实际存在的文件为准。当前项目中可执行：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\001_add_news_source_url_and_crawl_log.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\002_add_ai_generate_record_source_fields.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\003_add_community_post_tags.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\005_create_user_category_subscription.sql"
```

#### 4.4 配置 backend/.env

在 `backend/.env` 中配置：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=llm_news_system
DB_USER=llm_news_user
DB_PASSWORD=123456
AI_SERVICE_URL=http://127.0.0.1:8001
```

注意：

- `backend/.env` 不要提交到 Git。
- 不要在 README 或代码中写 MySQL root 密码。
- 如果组员本地数据库账号密码不同，需要自行修改 `backend/.env`。

#### 4.5 验证数据库

推荐使用下面这条 PowerShell 可运行命令：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT COUNT(*) AS user_count FROM user; SELECT COUNT(*) AS news_count FROM news; SELECT COUNT(*) AS category_count FROM news_category; SELECT COUNT(*) AS topic_count FROM news_topic;"""
```

### 5. 三端启动方式

日常启动项目时，需要打开三个 PowerShell 窗口分别启动。不要把 backend、ai-service、frontend 写成一个连续命令，因为 `uvicorn` 和 `npm run dev` 会占用当前终端。

#### 窗口 1：启动 backend

第一次启动：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

第二次及以后启动：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 窗口 2：启动 ai-service

第一次启动：

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

第二次及以后启动：

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### 窗口 3：启动 frontend

第一次启动：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

第二次及以后启动：

```powershell
cd frontend
npm.cmd run dev
```

访问地址：

- frontend：<http://localhost:5173>
- backend：<http://127.0.0.1:8000>
- backend Swagger：<http://127.0.0.1:8000/docs>
- ai-service：<http://127.0.0.1:8001>
- ai-service Swagger：<http://127.0.0.1:8001/docs>

### 6. 操作过一次之后的常规流程

如果数据库、虚拟环境和依赖都已经配置过，日常启动通常只需要三个窗口：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

```powershell
cd frontend
npm.cmd run dev
```

一般不需要每天重复执行 `schema.sql` 或 `seed.sql`。

### 7. RSS 新闻爬虫说明

当前爬虫脚本：

```text
scripts/crawlers/rss_news_crawler.py
```

支持能力：

1. RSS 新闻解析。
2. `source_url` 去重。
3. 原文页正文解析。
4. 封面图 `cover_image` 提取。
5. `crawl_log` 爬取日志。
6. `--cleanup-days` 归档旧新闻。
7. `--update-existing-content` 补全已有新闻正文和封面图。

预览，不写入数据库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --dry-run --max-items 3 --fetch-content
```

正式入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content
```

补全已有新闻正文和封面图：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 20 --fetch-content --update-existing-content
```

归档 30 天前旧新闻：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content --cleanup-days 30
```

说明：

- 当前只保存图片 URL，不下载图片文件。
- 正文解析失败时使用 RSS 摘要兜底。
- 不建议高频无限爬取。
- 建议每 15 分钟执行一次，每次每源 5 到 10 条。

### 8. 常见问题

#### 8.1 打开 http://127.0.0.1:8000/ 是 404

这是正常的。请访问：

- <http://127.0.0.1:8000/api/health>
- <http://127.0.0.1:8000/docs>

#### 8.2 AI 服务暂时不可用

通常表示 ai-service 未启动，或 LLM 调用失败。请启动：

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### 8.3 页面仍显示 mock 数据

可能原因：

1. MySQL 未启动。
2. `backend/.env` 配置错误。
3. 对应数据库表为空。
4. backend 触发 mock fallback。

可检查：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT COUNT(*) FROM news; SELECT COUNT(*) FROM community_post; SELECT COUNT(*) FROM news_category;"""
```

#### 8.4 新闻分类显示问号或乱码

优先检查 `news_category`：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT id,name,code FROM news_category ORDER BY sort;"""
```

如果分类数据异常，请确认导入时使用了 `--default-character-set=utf8mb4`。

#### 8.5 PowerShell 中 MySQL 导入失败

PowerShell 里不要直接执行：

```powershell
mysql -u llm_news_user -p llm_news_system < database\schema.sql
```

请使用：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
```

### 9. 提交前检查

```powershell
git status
```

不要提交：

- `backend/.env`
- `ai-service/.env`
- `node_modules`
- `dist`
- `.vite-temp`
- `__pycache__`
- `*.pyc`
- 真实 API Key
- MySQL root 密码

检查冲突标记：

```powershell
Select-String -Path .\* -Pattern "<<<<<<<","=======",">>>>>>>" -Recurse
```

如需检查旧项目名称，请在本地将下面命令中的占位词替换为要检查的旧名称：

```powershell
Select-String -Path .\* -Pattern "旧项目名称关键词" -Recurse
```
