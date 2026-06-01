# Marketing Modules Design

## 背景

当前 `src/backend/scenes/marketing` 已经同时承载产品成果与项目商机两类业务对象：

- 产品成果：结果主表、附件表、结果 CRUD、自动落库
- 项目商机：商机表、商机 CRUD、自动落库

现状虽然已经按 `router -> service -> repository` 做了分层，但 `parser` 与 `persistence` 仍以 `marketing` 总入口承载两类业务逻辑，导致：

- `business_result` 字段归一化规则集中在单文件，后续会继续膨胀
- 产品成果与项目商机虽然数据表已经拆开，但代码归属仍混在一起
- `modules/` 目录目前只有占位说明，没有形成真实业务边界

本次目标是在不改变对外入口的前提下，把 `marketing` 内部拆成真正独立的 `modules/product` 与 `modules/opportunity`。

## 目标

- 保留 `marketing` 作为统一业务场景
- 保留现有 API 路由、SQLite 表名、agent hook、output binding、测试入口不变
- 仅调整 `marketing` 内部目录与编排关系
- 将产品成果与项目商机的解析、持久化、仓储、服务实现分别归属到独立模块
- 让外层 `marketing` 仅承担统一编排与兼容出口

## 非目标

- 不拆分现有 `marketing` 场景为多个顶层 scene
- 不修改现有数据库表名与对外接口路径
- 不改变当前 `market_agent` 的绑定方式
- 不在本轮引入新的业务对象

## 方案对比

### 方案一：仅拆内部模块，保留统一入口

做法：

- 保留 `marketing/router.py`
- 保留 `marketing/hooks/post_reply.py`
- 保留 `marketing/parsers/business_result.py`
- 保留 `marketing/persistence.py`
- 但将具体产品成果与项目商机逻辑下沉到：
  - `marketing/modules/product`
  - `marketing/modules/opportunity`

优点：

- 改动最小
- 对外兼容性最好
- 能快速建立真实模块边界

缺点：

- 外层仍保留统一入口编排文件

### 方案二：只拆 parser/persistence，service/repository 继续放外层

做法：

- 只把解析与落库编排分模块
- 结果与商机的 service/repository 继续留在 `marketing` 根目录

优点：

- 改动更少

缺点：

- 业务归属不完整
- 后续继续扩展时边界仍会模糊

### 方案三：一次拆到完整子模块闭环

做法：

- `product` / `opportunity` 分别拥有 router、hook、parser、persistence、service、repository
- `marketing` 仅做注册聚合

优点：

- 独立性最高

缺点：

- 当前改动范围过大
- 与“最小侵入”目标不一致

## 结论

采用方案一。

原因：

- 符合当前“场景合并、代码独立”的诉求
- 满足最小改动原则
- 为后续继续拆解 `campaign/content/customer` 预留统一模式

## 目标目录

```text
src/backend/scenes/marketing/
  hooks/
    post_reply.py
  parsers/
    business_result.py
  persistence.py
  router.py
  dependencies.py
  manifest.py
  modules/
    product/
      __init__.py
      parser.py
      persistence.py
      repository.py
      service.py
      schemas.py
    opportunity/
      __init__.py
      parser.py
      persistence.py
      repository.py
      service.py
      schemas.py
```

## 职责划分

### 外层 marketing

- `hooks/post_reply.py`
  - 负责在 Agent reply 后触发统一后处理
  - 只负责调用总 parser 和总 persistence
- `parsers/business_result.py`
  - 负责从 Agent 最终文本中提取 `business_result`
  - 负责根据内容分流到 `product` 或 `opportunity` 模块解析器
  - 负责组装统一 `structured_result`
- `persistence.py`
  - 负责读取 `Msg.metadata`
  - 负责判断消息内包含哪些业务对象
  - 负责调用模块级 persistence 完成落库
- `router.py`
  - 仍保留 `/results` 和 `/opportunities` 两类接口
  - 内部改为依赖模块级 service

### modules/product

- `parser.py`
  - 负责产品成果相关结构化 payload 的生成与附件规范化
- `persistence.py`
  - 负责结果主表与附件表落库编排
- `repository.py`
  - 负责 `marketing_product_results` 与 `marketing_result_files`
- `service.py`
  - 负责结果 CRUD 与保存动作
- `schemas.py`
  - 负责产品成果与附件 DTO

### modules/opportunity

- `parser.py`
  - 负责商机列表抽取与字段归一化
- `persistence.py`
  - 负责商机自动落库编排
- `repository.py`
  - 负责 `marketing_opportunities`
- `service.py`
  - 负责商机 CRUD
- `schemas.py`
  - 负责商机 DTO

## 数据流

### Agent 自动落库链路

1. `QwenPawAgent.reply()` 完成模型回复
2. `MarketingPostReplyHook` 调用 `inject_business_result_metadata`
3. `marketing/parsers/business_result.py` 提取 `business_result`
4. 外层 parser 根据内容调用：
   - `modules/product/parser.py`
   - `modules/opportunity/parser.py`
5. 统一写回 `structured_result`
6. `marketing/persistence.py` 根据 metadata 调用模块 persistence
7. 模块 persistence 调用各自 service 与 repository 落库

### HTTP CRUD 链路

1. `marketing/router.py` 接受 `/results` 与 `/opportunities` 请求
2. 结果接口走 `modules/product/service.py`
3. 商机接口走 `modules/opportunity/service.py`
4. service 在事务中调用各自 repository

## 兼容边界

本轮保持以下内容不变：

- `market_agent` 默认 output binding
- `MarketingPostReplyHook` 类名与装配入口
- `inject_business_result_metadata` 导出路径
- `/api/backend/marketing/results*`
- `/api/backend/marketing/opportunities*`
- `marketing_product_results`
- `marketing_result_files`
- `marketing_opportunities`

## 迁移步骤

1. 将现有 result 相关 schema/service/repository 拆入 `modules/product`
2. 将现有 opportunity 相关 schema/service/repository 拆入 `modules/opportunity`
3. 将 `persistence.py` 中结果与商机落库逻辑拆分到两个模块 persistence
4. 将 `business_result.py` 中产品成果与商机抽取逻辑拆分到两个模块 parser
5. 外层 `marketing` 保留兼容导出与编排
6. 更新现有 import，不改外部调用方式
7. 更新并补充测试

## 错误处理

- 模块 parser 只做字段归一化与对象识别，不吞掉结构错误
- 外层 hook manager 继续保持异常隔离，避免单个业务模块阻断 reply
- persistence 仍保持 Guard Clauses，避免无效 metadata 触发落库

## 测试策略

- 保留现有回归测试，保证对外行为不变
- 新增模块级单测：
  - `modules/product/parser`
  - `modules/product/persistence`
  - `modules/opportunity/parser`
  - `modules/opportunity/persistence`
- 继续保留集成链路测试：
  - hook -> parser -> persistence
  - result CRUD
  - opportunity CRUD

## 风险点

- `business_result` 字段协议当前存在多处兼容写法，拆分时容易出现规则丢失
- 现有 `structured_result` 的 `product/business` 分流逻辑必须保持一致
- `summary` 与旧字段 `text` 的兼容逻辑需要在迁移时统一，避免新旧行为漂移

## 验收标准

- 现有对外 API 与表结构不变
- 现有核心测试继续通过
- `product` 与 `opportunity` 各自拥有独立模块代码
- 外层 `marketing` 文件明显收敛，只保留编排与兼容出口
