# 《基于大语言模型的智能新闻摘要与协同互动系统》新闻模块 Mock 数据说明

## 一、当前阶段说明

当前新闻模块仍处于 Mock 数据开发阶段，暂不连接数据库。现阶段新闻、评论、点赞、收藏和浏览记录等数据均来自 `backend/app/mock` 目录中的静态数据文件，主要用于后续新闻模块接口开发、前后端联调和小组协作阶段的结构验证。

## 二、涉及文件

- `backend/app/mock/news.py`
- `backend/app/mock/comments.py`

## 三、`news.py` 数据结构

`news.py` 中包含以下变量：

| 变量名 | 说明 |
| --- | --- |
| `NEWS_CATEGORIES` | 新闻分类数据，包含推荐、时政、社会、财经、科技、体育、娱乐等分类信息 |
| `MOCK_NEWS` | 新闻主体数据，包含新闻列表和新闻详情页所需的主要展示字段 |
| `MOCK_NEWS_LIKES` | 用户点赞新闻关系数据，用于模拟点赞状态 |
| `MOCK_NEWS_FAVORITES` | 用户收藏新闻关系数据，用于模拟收藏状态 |
| `MOCK_BROWSE_HISTORY` | 用户浏览记录数据，用于模拟浏览历史 |

## 四、`comments.py` 数据结构

`comments.py` 中包含以下变量：

| 变量名 | 说明 |
| --- | --- |
| `MOCK_NEWS_COMMENTS` | 新闻评论原始数据，使用 `parent_id` 表示评论与回复关系 |
| `MOCK_COMMENT_LIKES` | 用户点赞评论关系数据，用于模拟评论点赞状态 |

## 五、字段说明

### 1. 新闻字段

| 字段 | 说明 |
| --- | --- |
| `id` | 新闻 ID |
| `title` | 新闻标题 |
| `summary` | 新闻摘要 |
| `content` | 新闻正文内容 |
| `cover_image` | 新闻封面图地址，当前阶段可为空字符串 |
| `category_id` | 分类 ID |
| `category_name` | 分类名称 |
| `source` | 新闻来源 |
| `author` | 作者或记者 |
| `publish_time` | 发布时间，格式为 `YYYY-MM-DD HH:mm` |
| `view_count` | 浏览量 |
| `like_count` | 点赞数 |
| `comment_count` | 评论数 |
| `favorite_count` | 收藏数 |
| `status` | 新闻状态，当前阶段 `1` 表示正常发布 |
| `tags` | 新闻标签数组 |

### 2. 评论字段

| 字段 | 说明 |
| --- | --- |
| `id` | 评论 ID |
| `news_id` | 所属新闻 ID |
| `user_id` | 评论用户 ID |
| `username` | 用户名 |
| `nickname` | 用户昵称 |
| `avatar` | 用户头像，当前阶段可为空字符串 |
| `parent_id` | 父评论 ID，一级评论为 `None`，回复评论为被回复评论 ID |
| `content` | 评论内容 |
| `like_count` | 评论点赞数 |
| `status` | 评论状态，当前阶段约定 `1` 正常、`2` 折叠、`3` 待审核、`4` 删除 |
| `create_time` | 评论时间，格式为 `YYYY-MM-DD HH:mm` |

## 六、与后续数据库的对应关系

当前 Mock 数据后续大致会对应以下数据表：

| Mock 数据结构 | 后续数据库表 |
| --- | --- |
| `NEWS_CATEGORIES` | `news_category` |
| `MOCK_NEWS` | `news` |
| `MOCK_NEWS_COMMENTS` | `news_comment` |
| `MOCK_NEWS_LIKES` / `MOCK_COMMENT_LIKES` | `user_like` |
| `MOCK_NEWS_FAVORITES` | `favorite` |
| `MOCK_BROWSE_HISTORY` | `browse_history` |

说明：

- 当前阶段仅做结构映射参考，不代表最终数据库字段百分百固定。
- 后续接入数据库时，主要替换 `service.py` 中的数据来源。

## 七、与其他成员的对接点

### 1. 与成员 B AI 模块对接

新闻详情页跳转 AI 生成页时，需要能够提供以下字段：

- `id`
- `title`
- `content`

因此，新闻详情接口在后续开发中应确保这些字段可直接返回，便于成员 B 的 AI 生成功能接入。

### 2. 与成员 D 个人中心模块对接

成员 D 后续实现个人中心时，会使用以下数据做聚合展示：

- 浏览历史
- 收藏记录
- 评论记录

因此，`MOCK_BROWSE_HISTORY`、`MOCK_NEWS_FAVORITES` 和 `MOCK_NEWS_COMMENTS` 中的用户关联字段需要保持稳定。

### 3. 与后台模块对接

评论的 `status` 字段后续会用于：

- 审核状态控制
- 评论折叠
- 评论删除
- 评论展示过滤

因此，评论状态字段应继续保留，不建议在新闻模块开发中随意变更命名。

## 八、当前限制

- Mock 数据不会持久化保存。
- 服务重启后，运行过程中产生的内存修改会丢失。
- 当前不做真实数据库查询。
- 当前不保证多用户并发修改时的数据一致性。
- 当前阶段主要用于接口结构开发和前后端联调。
- 后续接数据库时，重点替换 `service.py` 中的数据来源，不需要先改前端接口路径。

