------------------------------------------------------------------------------------------------------------------------
-- version 1.0.0 荆门万华板业 update 2019.6.22
------------------------------------------------------------------------------------------------------------------------

-- 荆门万华板业 权限表
create table if not exists wh_roles
(
  phone  varchar(11) primary key,
  name   varchar(20)  default '',
  rights varchar(1)[] default '{}', -- 权限 1: 超级管理员, 2: 系统设置, 3: 数据录入, 4: 报表导入, 5: 报表模板, 6: 基础数据, 7: 报表查询
  time   integer
);

-- 砂光锯切表
create table if not exists wh_sanding_sawing
(
  date         date primary key, -- 日期
  schedule     varchar(36),      -- 班次 wh_schedules.uuid
  working_time varchar(1),       -- 上班时间: 早, 中, 晚
  recorder     varchar(20),      -- 记录人
  reviewer     varchar(20)       -- 审核人
);

-- 砂光锯切数据表
create table if not exists wh_sanding_sawing_data
(
  date           date,
  type           varchar(10),            -- sanding/sawing
  stack_number   varchar(20),            -- 堆垛号
  class          varchar(20) default '', -- 等级
  specification1 float,                  -- 规格1
  specification2 float,                  -- 规格2
  specification3 float,                  -- 规格3
  count          float,                  -- 数量
  sanding_amount float                   -- 砂光量
);
create index wh_sanding_sawing_data_index on wh_sanding_sawing_data (date);

-- 压机操作记录
create table if not exists wh_press_operation
(
  date         date primary key, -- 日期
  schedule     varchar(36),      -- 班次 wh_schedules.uuid
  working_time varchar(1),       -- 上班时间: 早, 中, 晚
  operator     varchar(20),      -- 操作人
  reviewer     varchar(20)       -- 审核人
);

-- 压机操作记录数据表
create table if not exists wh_press_operation_data
(
  date    date,        -- 日期
  time    varchar(20), -- 时间
  content varchar(100) -- 内容
);
create index wh_press_operation_data_index on wh_press_operation_data (date);

-- 物资消耗
create table if not exists wh_material_consumption
(
  date                date primary key, -- 日期
  schedule            varchar(36),      -- 班次 wh_schedules.uuid
  working_time        varchar(1),       -- 上班时间: 早, 中, 晚
  fuel                float,            -- 燃料
  glue                float,            -- 胶水
  waterproofing_agent float,            -- 防水剂
  power_consumption   float,            -- 电耗
  abrasive_belt       float,            -- 砂带
  shaving_blade       float             -- 削片刀片
);

------------------------------------------------------------------------------------
-- 基础数据 version 1.0.0 update 2019/6/22 jcj_version
------------------------------------------------------------------------------------

-- 年度生产计划表
create table wh_annual_plan
(
  date            varchar(10) primary key, -- 年度计划中的日期，格式为2019-1，还有一个2019-total
  output          integer,                 -- 总产量
  good_rate       varchar(10),             -- 合格率, 类似格式为'>80%'
  best_rate       varchar(10),             -- 优异率, 类似格式为'>10%'
  ng_rate         varchar(10),             -- 废品率, 类似格式为'<2%'
  production_days smallint                 -- 生产天数
);

-- 产品表
create table wh_product
(
  uuid varchar(36) PRIMARY KEY default uuid_generate_v4(), -- uuid
  id   varchar(20) not null unique,                        -- 产品编码
  name varchar(20) not null unique,                        -- 产品名称
  time integer
);

-- 班次表
create table wh_schedules
(
  uuid varchar(36) PRIMARY KEY default uuid_generate_v4(), -- 班次编码
  name varchar(20) not null unique,                        -- 班次名称
  time integer
);

insert into wh_schedules(uuid, name, time) values ('A', 'A班', 1561715421);
insert into wh_schedules(uuid, name, time) values ('B', 'B班', 1561715421);
insert into wh_schedules(uuid, name, time) values ('C', 'C班', 1561715421);

-- 车间表
create table wh_workshop
(
  uuid varchar(36) PRIMARY KEY default uuid_generate_v4(), -- uuid
  id   varchar(20) not null unique,                        -- 车间编码
  name varchar(20) not null unique,                        -- 车间名称
  time integer
);

-- 工段表
create table wh_section
(
  uuid varchar(36) PRIMARY KEY default uuid_generate_v4(), -- uuid
  id   varchar(20) not null unique,                        -- 工段编码
  name varchar(20) not null unique,                        -- 工段名称
  time integer
);

------------------------------------------------------------------------------------
-- 数据导入 version 1.0.0 update 2019/6/22 jcj_version
------------------------------------------------------------------------------------

-- 压机运行记录表
create table if not exists wh_press_record
(
  uuid           varchar(36) PRIMARY KEY default uuid_generate_v4(), -- uuid
  date           date,                                               -- 日期
  schedule       varchar(36),                                        -- 班次
  work_time      varchar(4),                                         -- 上班时间
  specifications varchar(20),                                        -- 规格
  shutdown_count integer,                                            -- 停机次数
  shutdown_time  float,                                              -- 停机时间
  output         float[],                                            -- 产量
  scrap          float[],                                            -- 废品
  remark         varchar(100),                                       -- 规格备注
  approver       varchar(20)                                         -- 审核人
);

-- 物料消耗记录表
create table if not exists wh_material_record
(
  uuid                 varchar(36) PRIMARY KEY default uuid_generate_v4(), -- uuid
  date                 date,                                               -- 日期
  schedule             varchar(36),                                        -- 班次
  work_time            varchar(4),                                         -- 上班时间
  specifications       varchar(20),                                        -- 规格
  surface_shaving      float,                                              -- 表面刨花
  core_shaving         float,                                              -- 芯层刨花
  surface_consumption  float,                                              -- 表面胶耗
  core_consumption     float,                                              -- 芯层胶耗
  watch_core_wax       float,                                              -- 表芯层石蜡
  watch_core_agent     varchar(15),                                        -- 表芯层固化剂
  watch_core_tackifier float,                                              -- 表芯层增粘剂
  watch_core_additive  varchar(10),                                        -- 表芯层添加剂
  watch_core_technics  varchar(10),                                        -- 表芯层工艺
  parting_agent        float,                                              -- 脱模剂
  output               float[],                                            -- 产量
  scrap                varchar(10)[],                                      -- 废品
  approver             varchar(20)                                         -- 审核人
);

-- 停机记录表
create table if not exists wh_shutdown_record
(
  uuid         varchar(36) PRIMARY KEY default uuid_generate_v4(), -- uuid
  date         date,                                               -- 日期
  schedule     varchar(36),                                        -- 班次
  total_time   float,                                              -- 停机总时长
  elec_device  float,                                              -- 设备(电气)
  mach_device  float,                                              -- 设备(机械)
  product      float,                                              -- 生产
  metal_alarm  float,                                              -- 金属报警
  plan_check   float,                                              -- 计划检修
  out_poweroff float,                                              -- 外部停电
  outsourcing  float,                                              -- 外包
  prevent_fire float,                                              -- 消防
  other        float                                               -- 其他
);

-- 生产目标差异
create table if not exists wh_product_target_diff
(
  month varchar(6) primary key,
  data  varchar[][],
  time  integer default extract(epoch from now())::integer
);

create table if not exists wh_product_target_type
(
  id serial primary key,
  data json    default '{}' :: json,
  time  integer default extract(epoch from now())::integer
);

-- 生产日报表
create table if not exists wh_product_batch
(
  month    varchar(6) primary key,
  all_data json    default '{}' :: json,
  schedule json    default '{}' :: json,
  time     integer default extract(epoch from now())::integer
);

-- 生产质量表
create table if not exists wh_product_quality
(
  month    varchar(6) primary key,
  all_data json    default '{}' :: json,
  time     integer default extract(epoch from now())::integer
);

-- update 2019.7.10 hzy 同一日期下可以有多个班次
alter table wh_sanding_sawing drop constraint wh_sanding_sawing_pkey;
alter table wh_sanding_sawing add column uuid varchar(36) primary key default uuid_generate_v4();
alter table wh_sanding_sawing_data add column schedule varchar(36);

alter table wh_press_operation drop constraint wh_press_operation_pkey;
alter table wh_press_operation add column uuid varchar(36) primary key default uuid_generate_v4();
alter table wh_press_operation_data add column schedule varchar(36);

alter table wh_material_consumption drop constraint wh_material_consumption_pkey;
alter table wh_material_consumption add column uuid varchar(36) primary key default uuid_generate_v4();
