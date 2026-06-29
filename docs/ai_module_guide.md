# AI 标题摘要生成模块使用指南

## 项目概述

本模块为"基于大语言模型的智能新闻摘要与协同互动系统"中的 AI 生成功能，提供智能新闻标题和摘要生成能力。

## 功能特性

### 1. 标题生成
- 支持生成 1、3、5 个候选标题
- 三种风格支持：
  - **客观新闻型**: 中立、正式的新闻标题
  - **吸引点击型**: 更有吸引力的标题（但不夸张）
  - **简洁概括型**: 短小精悍的标题

### 2. 摘要生成
- 两种摘要方式：
  - **生成式摘要**: 通过关键词和句子重新组织摘要
  - **抽取式摘要**: 直接从原文中抽取关键句
- 三种风格：
  - **简明扼要**: 简短、直接
  - **客观正式**: 正式、学术性语言
  - **通俗易懂**: 大众化、易理解的表达
- 三种长度配置：
  - **短摘要**: 仅返回短摘要
  - **长摘要**: 仅返回长摘要
  - **双摘要**: 同时返回短摘要和长摘要

### 3. 关键词提取
- 自动识别输入文本中的关键词
- 基于词频和词长排序

### 4. 新闻六要素识别
- Who（谁）: 识别新闻主体
- What（什么）: 识别事件
- When（何时）: 识别时间
- Where（何地）: 识别地点
- Why（为什么）: 推断原因
- How（怎样）: 识别方式

### 5. 一致性质量评估
- 质量评分: 0-100 分
- 风险等级: 低/中/高
- 问题识别: 列举检测到的问题
- 改进建议: 提供针对性建议

### 6. 生成历史管理
- 查看生成历史
- 查看历史详情（包含完整的生成结果）
- 复用历史记录（快速填充输入和参数）
- 删除历史记录

## 使用流程

### 方式一：手动输入

1. 打开页面: `/ai/title-summary`
2. 在输入框中粘贴或输入新闻正文
3. 调整生成参数（标题数、摘要风格等）
4. 点击"生成标题和摘要"按钮
5. 查看生成结果
6. 点击"复制"将结果复制到剪贴板

### 方式二：从新闻详情页导入

1. 打开任意新闻详情页
2. 点击"✨ 用 AI 生成标题和摘要"按钮
3. 自动跳转到 AI 生成页，正文已自动填充
4. 调整参数后点击生成
5. 查看结果

### 方式三：从历史记录复用

1. 在 AI 生成页下方找到"📚 生成历史"区域
2. 找到要复用的历史记录
3. 点击"复用"按钮
4. 输入框和参数自动填充
5. 可修改后重新生成

## API 接口

### 生成标题和摘要

**请求**
```
POST /api/ai/generate
Content-Type: application/json

{
  "input_text": "新闻正文...",
  "title_count": 3,
  "summary_type": "generate",
  "summary_style": "简明扼要",
  "title_style": "客观新闻型",
  "summary_length": "both"
}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "candidate_titles": ["标题1", "标题2", "标题3"],
    "summary_short": "短摘要内容",
    "summary_long": "长摘要内容",
    "summary_points": ["要点1", "要点2"],
    "keywords": ["关键词1", "关键词2"],
    "elements": {
      "who": "新闻主体",
      "what": "新闻事件",
      "when": "新闻时间",
      "where": "新闻地点",
      "why": "新闻原因",
      "how": "新闻方式"
    },
    "consistency": {
      "score": 92,
      "risk_level": "low",
      "issues": [],
      "suggestions": ["文本质量满足生成条件"]
    }
  }
}
```

### 获取历史列表

**请求**
```
GET /api/ai/records
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "source": "news",
        "source_news_id": 3,
        "source_title": "新闻标题",
        "title_count": 3,
        "risk_level": "low",
        "created_at": "2026-06-23T10:00:00"
      }
    ],
    "total": 1
  }
}
```

### 获取历史详情

**请求**
```
GET /api/ai/records/{record_id}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "source": "news",
    "source_news_id": 3,
    "source_title": "新闻标题",
    "input_text": "完整的输入文本",
    "params": { ... },
    "result": { ... },
    "created_at": "2026-06-23T10:00:00"
  }
}
```

### 删除历史记录

**请求**
```
DELETE /api/ai/records/{record_id}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "历史记录已删除"
  }
}
```

## 当前实现状态

### 已完成 ✅
- [x] 手动输入新闻正文
- [x] 参数选择和配置
- [x] AI 结果生成（Mock 实现）
- [x] 关键词、要素、质量评估显示
- [x] 新闻详情页导入
- [x] 生成历史管理（Mock 实现）
- [x] 历史记录复用

### 实现方式 ⏳
- 🔹 **Mock 数据生成**: 基于输入文本的动态 Mock，不接真实 LLM
- 🔹 **历史存储**: 内存存储（运行时数据），不持久化到数据库
- 🔹 **历史 Mock 数据**: 预置 3 条示例记录

### 后续规划 📋
- [ ] 接入真实大语言模型 API（如 Claude、GPT 等）
- [ ] 历史记录持久化（接入数据库）
- [ ] 生成结果导出功能（PDF、JSON 等）
- [ ] 生成结果评分和反馈
- [ ] 批量生成功能

## 技术架构

### 三层调用链路

```
前端 (Frontend)
    ↓ HTTP POST
后端 (Backend) - /api/ai/*
    ↓ HTTP 内部调用
AI 服务 (AI Service) - /ai/*
    ↓
Mock 数据生成（当前阶段）
未来：LLM API 调用
```

### 关键文件

**前端**
- `frontend/src/api/ai.ts` - API 封装
- `frontend/src/stores/aiDraft.ts` - 状态管理
- `frontend/src/views/ai-generate/AIGenerateView.vue` - 主页面
- `frontend/src/components/ai/` - AI 组件库
  - `AIInputPanel.vue` - 输入区
  - `AIParamPanel.vue` - 参数区
  - `AIResultPanel.vue` - 结果展示
  - `AIGenerateHistory.vue` - 历史管理
  - `KeywordTags.vue` - 关键词展示
  - `NewsElements.vue` - 要素展示
  - `ConsistencyCheckPanel.vue` - 质量评估

**后端**
- `backend/app/modules/ai/router.py` - 路由定义
- `backend/app/modules/ai/service.py` - 业务逻辑
- `backend/app/modules/ai/schema.py` - 数据模型
- `backend/app/mock/ai_records.py` - 历史记录 Mock

**AI 服务**
- `ai-service/app/routers/generate.py` - 路由
- `ai-service/app/services/generate_service.py` - 生成逻辑
- `ai-service/app/schemas/generate.py` - 数据模型

## 限制和注意事项

1. **输入文本限制**
   - 输入文本不能为空
   - 文本太短（<50字）会降低质量评分

2. **参数限制**
   - 标题数量: 1-5
   - 摘要长度: short/long/both

3. **Mock 数据特性**
   - 生成结果基于输入文本的关键词和句子
   - 不是真正的智能生成，但能演示完整功能
   - 关键词识别基于中文词汇频率

4. **历史记录**
   - 内存存储，服务重启后丢失
   - 运行时新增记录不会被持久化

## 常见问题

### Q: 为什么生成的标题和摘要和输入不匹配？
A: 当前使用 Mock 实现，是基于输入文本的动态生成，而不是真实的 AI 生成。后续接入真实 LLM 后将改善。

### Q: 历史记录为什么重启后丢失？
A: 当前历史存储为内存数据，不持久化。接入数据库后将保留。

### Q: 如何导出生成结果？
A: 导出功能当前为占位，点击会提示"导出功能后续接入"。

### Q: 能否只生成摘要不生成标题？
A: 当前设计中标题和摘要一起生成。如需要分离，请提交功能需求。
