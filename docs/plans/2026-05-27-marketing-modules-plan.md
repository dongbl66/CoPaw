# Marketing Modules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变 `marketing` 对外入口、表结构与 agent 装配方式的前提下，将产品成果与项目商机拆入 `modules/product` 与 `modules/opportunity` 的独立内部模块。

**Architecture:** 保留 `marketing` 作为统一 scene，外层继续保留 `hook / parser / persistence / router` 兼容入口；把结果与商机的具体解析、持久化、仓储与服务逻辑分别下沉到两个内部模块，再由外层统一编排。整个实施过程采用 TDD，小步提交，先建立模块外壳，再迁移结果链路，再迁移商机链路，最后收敛兼容出口与测试。

**Tech Stack:** Python, FastAPI, Pydantic, SQLite, pytest

---

### Task 1: 建立模块目录与兼容外壳

**Files:**
- Create: `src/backend/scenes/marketing/modules/product/__init__.py`
- Create: `src/backend/scenes/marketing/modules/product/schemas.py`
- Create: `src/backend/scenes/marketing/modules/product/repository.py`
- Create: `src/backend/scenes/marketing/modules/product/service.py`
- Create: `src/backend/scenes/marketing/modules/product/parser.py`
- Create: `src/backend/scenes/marketing/modules/product/persistence.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/__init__.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/schemas.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/repository.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/service.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/parser.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/persistence.py`
- Modify: `src/backend/scenes/marketing/modules/__init__.py`
- Test: `tests/unit/backend/test_module_loading.py`

**Step 1: 写一个最小失败测试，验证模块可导入**

```python
from backend.scenes.marketing.modules.product import __all__ as product_exports
from backend.scenes.marketing.modules.opportunity import __all__ as opportunity_exports


def test_marketing_internal_modules_can_be_imported() -> None:
    assert "ProductResultService" in product_exports
    assert "OpportunityService" in opportunity_exports
```

**Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/backend/test_module_loading.py -q`
Expected: FAIL，提示模块或导出不存在

**Step 3: 写最小实现**

在两个模块下先创建空壳导出，保证：

```python
__all__ = [
    "ProductResultService",
    "ProductResultRepository",
    "ProductResultParser",
    "ProductResultPersistence",
]
```

```python
__all__ = [
    "OpportunityService",
    "OpportunityRepository",
    "OpportunityParser",
    "OpportunityPersistence",
]
```

先允许这些类仅作为占位包装器，内部暂时委托旧实现。

**Step 4: 重新运行测试**

Run: `python -m pytest tests/unit/backend/test_module_loading.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/backend/scenes/marketing/modules tests/unit/backend/test_module_loading.py
git commit -m "refactor: scaffold marketing internal modules"
```

### Task 2: 迁移产品成果 schema/service/repository 到 product 模块

**Files:**
- Create: `src/backend/scenes/marketing/modules/product/schemas.py`
- Create: `src/backend/scenes/marketing/modules/product/repository.py`
- Create: `src/backend/scenes/marketing/modules/product/service.py`
- Modify: `src/backend/scenes/marketing/schemas/result.py`
- Modify: `src/backend/scenes/marketing/repository.py`
- Modify: `src/backend/scenes/marketing/service.py`
- Test: `tests/unit/backend/test_marketing_results_service.py`

**Step 1: 先写失败测试，验证服务来自 product 模块**

在 `tests/unit/backend/test_marketing_results_service.py` 增加一条断言：

```python
from backend.scenes.marketing.modules.product.service import ProductResultService


def test_product_result_service_create_and_list(tmp_path):
    service = ProductResultService(BackendDatabase(tmp_path / "backend.sqlite3"))
    created = service.create_result(
        title="产品方案",
        result_type="product",
        scene="demo",
        summary="摘要",
        detail_content=[],
        info={},
        basic_info={},
        product_info={},
        attachments=[],
        session_id="s1",
        agent_id="market_agent",
    )
    assert created.title == "产品方案"
```

**Step 2: 运行目标测试确认失败**

Run: `python -m pytest tests/unit/backend/test_marketing_results_service.py -q`
Expected: FAIL，提示 `ProductResultService` 不存在或行为不完整

**Step 3: 写最小实现**

- 把 `MarketingResult*` 相关 DTO 迁入 `modules/product/schemas.py`
- 把结果仓储迁入 `modules/product/repository.py`
- 把结果服务迁入 `modules/product/service.py`
- 外层 `marketing/schemas/result.py` 暂时只做兼容 re-export：

```python
from backend.scenes.marketing.modules.product.schemas import (
    MarketingResultCreate,
    MarketingResultFileCreate,
    MarketingResultFileRead,
    MarketingResultRead,
    MarketingResultUpdate,
)
```

- 外层 `marketing/service.py` 暂时保留兼容别名：

```python
from backend.scenes.marketing.modules.product.service import (
    ProductResultService as MarketingResultService,
)
```

**Step 4: 重新运行产品结果测试**

Run: `python -m pytest tests/unit/backend/test_marketing_results_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/backend/scenes/marketing/modules/product src/backend/scenes/marketing/schemas/result.py src/backend/scenes/marketing/service.py src/backend/scenes/marketing/repository.py tests/unit/backend/test_marketing_results_service.py
git commit -m "refactor: move marketing result logic into product module"
```

### Task 3: 迁移项目商机 schema/service/repository 到 opportunity 模块

**Files:**
- Create: `src/backend/scenes/marketing/modules/opportunity/schemas.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/repository.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/service.py`
- Modify: `src/backend/scenes/marketing/schemas/opportunity.py`
- Modify: `src/backend/scenes/marketing/repository.py`
- Modify: `src/backend/scenes/marketing/service.py`
- Test: `tests/unit/backend/test_marketing_opportunities_service.py`

**Step 1: 写失败测试，验证商机服务已迁移**

```python
from backend.scenes.marketing.modules.opportunity.service import OpportunityService


def test_opportunity_service_create_and_list(tmp_path):
    service = OpportunityService(BackendDatabase(tmp_path / "backend.sqlite3"))
    created = service.create_opportunity(
        title="项目商机",
        opportunity_type="招投标",
        region="山东",
        source="平台",
        publish_time=None,
        deadline=None,
        credibility=0.8,
        contact="张三",
        budget=100.0,
        purchase_amount=50.0,
        link_status="valid",
        reason="命中行业",
        original_link="https://example.com",
        level="A",
        summary="摘要",
        session_id="s1",
        agent_id="market_agent",
    )
    assert created.title == "项目商机"
```

**Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/backend/test_marketing_opportunities_service.py -q`
Expected: FAIL，提示 `OpportunityService` 不存在或未实现

**Step 3: 写最小实现**

- 把商机 DTO 移入 `modules/opportunity/schemas.py`
- 把商机仓储移入 `modules/opportunity/repository.py`
- 把商机服务移入 `modules/opportunity/service.py`
- 外层 `marketing/schemas/opportunity.py` 保留兼容 re-export
- 外层 `marketing/service.py` 保留兼容别名：

```python
from backend.scenes.marketing.modules.opportunity.service import (
    OpportunityService as MarketingOpportunityService,
)
```

**Step 4: 重新运行商机测试**

Run: `python -m pytest tests/unit/backend/test_marketing_opportunities_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/backend/scenes/marketing/modules/opportunity src/backend/scenes/marketing/schemas/opportunity.py src/backend/scenes/marketing/service.py src/backend/scenes/marketing/repository.py tests/unit/backend/test_marketing_opportunities_service.py
git commit -m "refactor: move marketing opportunity logic into opportunity module"
```

### Task 4: 拆分产品成果 parser 与 persistence

**Files:**
- Create: `src/backend/scenes/marketing/modules/product/parser.py`
- Create: `src/backend/scenes/marketing/modules/product/persistence.py`
- Modify: `src/backend/scenes/marketing/parsers/business_result.py`
- Modify: `src/backend/scenes/marketing/persistence.py`
- Test: `tests/unit/backend/test_business_result_parser.py`
- Test: `tests/unit/backend/test_marketing_persistence.py`

**Step 1: 先写失败测试，验证产品成果附件与 structured_result 由 product parser 处理**

```python
from backend.scenes.marketing.modules.product.parser import ProductResultParser


def test_product_result_parser_builds_product_structured_result():
    parser = ProductResultParser()
    result = parser.build_structured_result(
        business_result={"title": "产品方案", "display_content": []},
        output_text="结构化摘要",
    )
    assert result["result"]["type"] == "product"
    assert result["result"]["payload"]["summary"] == "结构化摘要"
```

**Step 2: 运行目标测试确认失败**

Run: `python -m pytest tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py -q`
Expected: FAIL，提示新模块未接入

**Step 3: 写最小实现**

- `ProductResultParser` 负责：
  - `product` 类型 structured_result
  - 产品附件规范化
- `ProductResultPersistence` 负责：
  - 结果主表创建
  - 附件落库
- 外层 `business_result.py` 改成：

```python
if opportunity_parser.has_opportunities(business_result):
    return opportunity_parser.build_structured_result(...)
return product_parser.build_structured_result(...)
```

- 外层 `persistence.py` 改成：

```python
self._product_persistence.persist(...)
```

**Step 4: 重新运行解析与持久化测试**

Run: `python -m pytest tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/backend/scenes/marketing/modules/product src/backend/scenes/marketing/parsers/business_result.py src/backend/scenes/marketing/persistence.py tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py
git commit -m "refactor: move product parsing and persistence into module"
```

### Task 5: 拆分商机 parser 与 persistence

**Files:**
- Create: `src/backend/scenes/marketing/modules/opportunity/parser.py`
- Create: `src/backend/scenes/marketing/modules/opportunity/persistence.py`
- Modify: `src/backend/scenes/marketing/parsers/business_result.py`
- Modify: `src/backend/scenes/marketing/persistence.py`
- Test: `tests/unit/backend/test_business_result_parser.py`
- Test: `tests/unit/backend/test_marketing_persistence.py`

**Step 1: 写失败测试，验证商机列表识别与持久化由 opportunity 模块处理**

```python
from backend.scenes.marketing.modules.opportunity.parser import OpportunityParser


def test_opportunity_parser_extracts_business_items():
    parser = OpportunityParser()
    items = parser.extract_opportunities(
        {"opportunities": [{"title": "商机A", "budget": 10}]}
    )
    assert items[0]["title"] == "商机A"
```

**Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py -q`
Expected: FAIL

**Step 3: 写最小实现**

- `OpportunityParser` 负责：
  - 判断是否存在商机
  - 统一商机字段抽取
  - 构建 `business` 类型 structured_result
- `OpportunityPersistence` 负责：
  - 商机列表标准化
  - 调用 `OpportunityService.create_opportunity`
- 外层 `persistence.py` 改为同时委托：

```python
self._product_persistence.persist(...)
self._opportunity_persistence.persist(...)
```

**Step 4: 重新运行测试**

Run: `python -m pytest tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/backend/scenes/marketing/modules/opportunity src/backend/scenes/marketing/parsers/business_result.py src/backend/scenes/marketing/persistence.py tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py
git commit -m "refactor: move opportunity parsing and persistence into module"
```

### Task 6: 收敛外层 marketing 兼容出口

**Files:**
- Modify: `src/backend/scenes/marketing/router.py`
- Modify: `src/backend/scenes/marketing/dependencies.py`
- Modify: `src/backend/scenes/marketing/service.py`
- Modify: `src/backend/scenes/marketing/repository.py`
- Modify: `src/backend/scenes/marketing/modules/__init__.py`
- Test: `tests/unit/backend/test_marketing_router.py`
- Test: `tests/unit/agents/test_react_agent_structured_model.py`
- Test: `tests/unit/agents/hooks/test_business_post_reply_hook.py`

**Step 1: 写失败测试，验证外层兼容路径仍可工作**

```python
def test_marketing_router_latest_result_still_works(client):
    response = client.get("/api/backend/marketing/results/latest")
    assert response.status_code in {200, 404}
```

```python
async def test_reply_injects_business_result_metadata_from_output(...):
    result = await QwenPawAgent.reply(...)
    assert result.metadata["structured_result"]["result"]["type"] in {
        "product",
        "business",
    }
```

**Step 2: 运行兼容回归测试确认失败**

Run: `python -m pytest tests/unit/backend/test_marketing_router.py tests/unit/agents/test_react_agent_structured_model.py tests/unit/agents/hooks/test_business_post_reply_hook.py -q`
Expected: FAIL，如果旧导入还耦合在原文件

**Step 3: 写最小实现**

- `dependencies.py` 直接返回模块级 service
- `router.py` 保持原 URL 与响应模型，但 import 模块级 service
- 外层 `service.py`、`repository.py` 只保留兼容导出或薄包装，避免重复实现
- `modules/__init__.py` 统一导出 product/opportunity 模块

**Step 4: 运行完整回归**

Run: `python -m pytest tests/unit/agents/hooks/test_business_post_reply_hook.py tests/unit/agents/test_react_agent_structured_model.py tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py tests/unit/backend/test_marketing_opportunities_service.py tests/unit/backend/test_marketing_results_service.py tests/unit/backend/test_marketing_router.py tests/unit/backend/test_module_loading.py -q`
Expected: PASS

**Step 5: 运行诊断与项目检查**

Run: `python -m pytest tests/unit/agents/hooks/test_business_post_reply_hook.py tests/unit/agents/test_react_agent_structured_model.py tests/unit/backend/test_business_result_parser.py tests/unit/backend/test_marketing_persistence.py tests/unit/backend/test_marketing_opportunities_service.py tests/unit/backend/test_marketing_results_service.py tests/unit/backend/test_marketing_router.py tests/unit/backend/test_module_loading.py -q`
Expected: PASS

然后运行：

```bash
npm run check:output
```

如果根目录不存在 `package.json`，记录为当前仓库不适用，并检查最近修改文件的诊断结果。

**Step 6: Commit**

```bash
git add src/backend/scenes/marketing tests/unit/agents tests/unit/backend docs/plans/2026-05-27-marketing-modules-design.md docs/plans/2026-05-27-marketing-modules-plan.md
git commit -m "refactor: split marketing internals into product and opportunity modules"
```
