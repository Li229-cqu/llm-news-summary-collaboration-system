-- ============================================================
-- Seed Phase 1: 35用户系统
-- 3核心 + 12活跃 + 15被动 + 2系统 + 3原始 = 35
-- 时间: 2026-06-03 ~ 2026-07-03
-- ============================================================
SET NAMES utf8mb4;

-- ============================================================
-- 🔴 CORE USERS (3人) — 贡献50%评论+点赞+发帖
-- ============================================================

-- Core-1: 科技深度评论员
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'core_tech_chen', '123456', '科技评论员陈思远', 'user', '', 1, '2026-06-03 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'core_tech_chen');
SET @cu1 = COALESCE((SELECT id FROM `user` WHERE username='core_tech_chen'), LAST_INSERT_ID());

-- Core-2: 社区领航者
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'core_community_liu', '123456', '社区领航者刘洋', 'user', '', 1, '2026-06-04 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'core_community_liu');
SET @cu2 = COALESCE((SELECT id FROM `user` WHERE username='core_community_liu'), LAST_INSERT_ID());

-- Core-3: 深度观察者
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'core_observer_huang', '123456', '深度观察者黄志明', 'user', '', 1, '2026-06-05 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'core_observer_huang');
SET @cu3 = COALESCE((SELECT id FROM `user` WHERE username='core_observer_huang'), LAST_INSERT_ID());

-- ============================================================
-- 🟡 ACTIVE USERS (12人) — 中等互动，覆盖全领域
-- ============================================================

-- A1: 时政
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_politics_zhao', '123456', '时政观察员赵文博', 'user', '', 1, '2026-06-05 14:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_politics_zhao');
SET @au1 = COALESCE((SELECT id FROM `user` WHERE username='active_politics_zhao'), LAST_INSERT_ID());

-- A2: 国际
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_world_qian', '123456', '环球视野钱雪梅', 'user', '', 1, '2026-06-06 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_world_qian');
SET @au2 = COALESCE((SELECT id FROM `user` WHERE username='active_world_qian'), LAST_INSERT_ID());

-- A3: 财经
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_finance_sun', '123456', '财经分析师孙浩然', 'user', '', 1, '2026-06-06 15:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_finance_sun');
SET @au3 = COALESCE((SELECT id FROM `user` WHERE username='active_finance_sun'), LAST_INSERT_ID());

-- A4: 社会
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_society_zhou', '123456', '社会观察者周丽华', 'user', '', 1, '2026-06-07 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_society_zhou');
SET @au4 = COALESCE((SELECT id FROM `user` WHERE username='active_society_zhou'), LAST_INSERT_ID());

-- A5: 体育
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_sports_wu', '123456', '体育评论员吴志强', 'user', '', 1, '2026-06-08 11:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_sports_wu');
SET @au5 = COALESCE((SELECT id FROM `user` WHERE username='active_sports_wu'), LAST_INSERT_ID());

-- A6: 娱乐
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_entertain_zheng', '123456', '娱乐达人郑晓芸', 'user', '', 1, '2026-06-09 13:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_entertain_zheng');
SET @au6 = COALESCE((SELECT id FROM `user` WHERE username='active_entertain_zheng'), LAST_INSERT_ID());

-- A7: 科技
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_tech_ma', '123456', '科技探索者马天宇', 'user', '', 1, '2026-06-10 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_tech_ma');
SET @au7 = COALESCE((SELECT id FROM `user` WHERE username='active_tech_ma'), LAST_INSERT_ID());

-- A8: 跨界
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_cross_lin', '123456', '跨界思考者林雪芬', 'user', '', 1, '2026-06-11 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_cross_lin');
SET @au8 = COALESCE((SELECT id FROM `user` WHERE username='active_cross_lin'), LAST_INSERT_ID());

-- A9: 教育
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_edu_he', '123456', '教育观察员何建华', 'user', '', 1, '2026-06-12 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_edu_he');
SET @au9 = COALESCE((SELECT id FROM `user` WHERE username='active_edu_he'), LAST_INSERT_ID());

-- A10: 健康
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_health_xu', '123456', '健康关注者许美玲', 'user', '', 1, '2026-06-13 11:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_health_xu');
SET @au10 = COALESCE((SELECT id FROM `user` WHERE username='active_health_xu'), LAST_INSERT_ID());

-- A11: 环保
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_green_gao', '123456', '绿色生活家高远', 'user', '', 1, '2026-06-14 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_green_gao');
SET @au11 = COALESCE((SELECT id FROM `user` WHERE username='active_green_gao'), LAST_INSERT_ID());

-- A12: 法律
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'active_law_duan', '123456', '法律爱好者段明哲', 'user', '', 1, '2026-06-15 14:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'active_law_duan');
SET @au12 = COALESCE((SELECT id FROM `user` WHERE username='active_law_duan'), LAST_INSERT_ID());

-- ============================================================
-- ⚪ PASSIVE USERS (15人) — 浏览为主，少量点赞
-- ============================================================

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_reader_wang', '123456', '读者王大明', 'user', '', 1, '2026-06-10 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_reader_wang');
SET @pu1 = COALESCE((SELECT id FROM `user` WHERE username='passive_reader_wang'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_lily_li', '123456', '莉莉在读书', 'user', '', 1, '2026-06-12 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_lily_li');
SET @pu2 = COALESCE((SELECT id FROM `user` WHERE username='passive_lily_li'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_zhang_wei', '123456', '张伟的日常', 'user', '', 1, '2026-06-14 11:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_zhang_wei');
SET @pu3 = COALESCE((SELECT id FROM `user` WHERE username='passive_zhang_wei'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_chen_jie', '123456', '陈洁小窝', 'user', '', 1, '2026-06-16 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_chen_jie');
SET @pu4 = COALESCE((SELECT id FROM `user` WHERE username='passive_chen_jie'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_yang_fan', '123456', '杨帆启航', 'user', '', 1, '2026-06-18 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_yang_fan');
SET @pu5 = COALESCE((SELECT id FROM `user` WHERE username='passive_yang_fan'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_liu_yu', '123456', '雨过天晴刘', 'user', '', 1, '2026-06-20 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_liu_yu');
SET @pu6 = COALESCE((SELECT id FROM `user` WHERE username='passive_liu_yu'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_huang_li', '123456', '黄鹂鸟', 'user', '', 1, '2026-06-22 11:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_huang_li');
SET @pu7 = COALESCE((SELECT id FROM `user` WHERE username='passive_huang_li'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_zhao_qiang', '123456', '赵强不强', 'user', '', 1, '2026-06-24 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_zhao_qiang');
SET @pu8 = COALESCE((SELECT id FROM `user` WHERE username='passive_zhao_qiang'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_sun_tao', '123456', '孙涛的笔记', 'user', '', 1, '2026-06-26 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_sun_tao');
SET @pu9 = COALESCE((SELECT id FROM `user` WHERE username='passive_sun_tao'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_wu_lin', '123456', '吴林好风光', 'user', '', 1, '2026-06-28 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_wu_lin');
SET @pu10 = COALESCE((SELECT id FROM `user` WHERE username='passive_wu_lin'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_zhou_jie', '123456', '周杰不是伦', 'user', '', 1, '2026-06-30 11:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_zhou_jie');
SET @pu11 = COALESCE((SELECT id FROM `user` WHERE username='passive_zhou_jie'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_xu_ting', '123456', '许婷听风', 'user', '', 1, '2026-06-05 12:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_xu_ting');
SET @pu12 = COALESCE((SELECT id FROM `user` WHERE username='passive_xu_ting'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_ma_dong', '123456', '马东说新闻', 'user', '', 1, '2026-06-08 13:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_ma_dong');
SET @pu13 = COALESCE((SELECT id FROM `user` WHERE username='passive_ma_dong'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_gao_min', '123456', '高敏的时光', 'user', '', 1, '2026-06-15 14:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_gao_min');
SET @pu14 = COALESCE((SELECT id FROM `user` WHERE username='passive_gao_min'), LAST_INSERT_ID());

INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'passive_duan_wei', '123456', '段伟在路上', 'user', '', 1, '2026-06-19 15:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'passive_duan_wei');
SET @pu15 = COALESCE((SELECT id FROM `user` WHERE username='passive_duan_wei'), LAST_INSERT_ID());

-- ============================================================
-- 🛡️ SYSTEM USERS (2人)
-- ============================================================

-- Editor
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'editor_in_chief', '123456', '内容主编赵立新', 'editor', '', 1, '2026-06-03 07:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'editor_in_chief');
SET @ed = COALESCE((SELECT id FROM `user` WHERE username='editor_in_chief'), LAST_INSERT_ID());

-- Admin
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `avatar`, `status`, `created_at`)
SELECT 'ops_admin_wu', '123456', '平台运营吴晓芳', 'admin', '', 1, '2026-06-03 06:00:00'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `username` = 'ops_admin_wu');
SET @ad = COALESCE((SELECT id FROM `user` WHERE username='ops_admin_wu'), LAST_INSERT_ID());

-- ============================================================
-- 变量清单 (共35用户: 3原始 + 3核心 + 12活跃 + 15被动 + 2系统)
-- ============================================================
-- 原始: uid=1(user),uid=2(editor),uid=3(admin)
-- 核心: @cu1 @cu2 @cu3
-- 活跃: @au1~@au12
-- 被动: @pu1~@pu15
-- 系统: @ed @ad

SELECT @cu1 AS core1, @cu2 AS core2, @cu3 AS core3,
       @au1 AS act1, @au2 AS act2, @au3 AS act3, @au4 AS act4,
       @au5 AS act5, @au6 AS act6, @au7 AS act7, @au8 AS act8,
       @au9 AS act9, @au10 AS act10, @au11 AS act11, @au12 AS act12,
       @pu1 AS pas1, @pu2 AS pas2, @pu3 AS pas3, @pu4 AS pas4, @pu5 AS pas5,
       @pu6 AS pas6, @pu7 AS pas7, @pu8 AS pas8, @pu9 AS pas9, @pu10 AS pas10,
       @pu11 AS pas11, @pu12 AS pas12, @pu13 AS pas13, @pu14 AS pas14, @pu15 AS pas15,
       @ed AS editor_new, @ad AS admin_new;
