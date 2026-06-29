ALTER TABLE event_timeline
ADD COLUMN metadata_json TEXT DEFAULT NULL COMMENT '事件脉络元数据（overview/key_figures/phases）';

ALTER TABLE event_timeline
ADD COLUMN relationships_json TEXT DEFAULT NULL COMMENT '事件关联关系数据（有向图边）';

ALTER TABLE event_timeline
ADD COLUMN schema_version VARCHAR(20) DEFAULT '1.0' COMMENT '数据结构版本号';
