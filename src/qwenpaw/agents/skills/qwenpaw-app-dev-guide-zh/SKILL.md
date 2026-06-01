---
name: qwenpaw-app-dev-guide
description: "用于指导在 QwenPaw 项目中开发 AI 场景应用的完整流程。包含从需求设计到部署测试的 7 个完整阶段。"
metadata:
  builtin_skill_version: "1.0"
  qwenpaw:
    emoji: "🚀"
    requires: {}
---

# QwenPaw AI 应用开发流程指南

## 概述

本技能详细描述了在 QwenPaw 项目中开发 AI 场景应用的完整流程，包括从需求设计到部署测试的 7 个核心阶段。

---

## 第 1 步：需求设计方案

### 1.1 主要内容

- 明确产品目标和用户场景
- 定义功能边界和核心需求
- 识别技术约束和依赖
- 输出：需求文档、功能清单、技术栈选型

### 1.2 具体动作

#### 1.2.1 调研项目结构

使用 `LS` 和 `Read` 工具探索项目结构，理解项目架构：

```
查看项目结构：
- console/ - 前端 React 应用
- src/qwenpaw/ - 后端 Python 服务
- src/backend/scenes/ - 场景开发目录
- plugins/ - 插件目录
```

重点查看：
- [pyproject.toml](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\pyproject.toml) - 后端依赖
- [console/package.json](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\package.json) - 前端依赖
- 现有示例场景：[marketing](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing)

#### 1.2.2 与用户澄清需求

使用 `AskUserQuestion` 向用户确认以下问题：

- 应用的主要目标是什么？
- 目标用户是谁？
- 核心功能有哪些？
- 技术约束（如需要什么 API、数据库等）
- 预期交付时间

#### 1.2.3 输出需求文档

创建需求文档，记录：
- 产品概述
- 用户故事/使用场景
- 功能列表
- 非功能需求（性能、安全等）

### 1.3 基于的技能和工具

- **技能：** `search`（探索项目代码）、`TodoWrite`（管理任务）
- **工具：** `Read`、`LS`、`Glob`、`AskUserQuestion`

---

## 第 2 步：产品原型设计与 UI 组件规划

### 2.1 主要内容

- 设计页面布局和交互流程
- 确定 UI/UX 风格，保持与项目一致
- 规划业务模块结构
- 创建可交互的原型或直接开始组件化设计
- 输出：UI 组件结构规划、原型验证结果

### 2.2 具体动作

#### 2.2.1 研究项目现有 UI 模式

查看项目的前端代码，理解已有的设计模式：

**核心技术栈：**
```
- React 18 + TypeScript
- Ant Design 5.x
- @agentscope-ai/chat / @agentscope-ai/design
- Less 样式系统
- i18n 国际化支持
- Zustand 状态管理
- React Router 路由
```

**重点学习的文件和组件：**
1. **页面组件示例：**
   - [Marketing 商机列表页](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\business\marketing\pages\Opportunities\index.tsx) - 表格、卡片、标签页的完整应用
   - [Chat 聊天页](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\pages\Chat\index.tsx) - 复杂交互页面的结构

2. **通用组件：**
   - [PageHeader](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\components\PageHeader\index.tsx) - 页面头部组件，用于面包屑、标题和操作
   - [MainLayout](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\layouts\MainLayout\index.tsx) - 主布局结构

3. **样式文件示例：**
   - [Chat 页面样式](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\pages\Chat\index.module.less) - Less CSS Modules 的使用方式
   - 注意深色模式 `:global(.dark-mode)` 的支持

#### 2.2.2 规划业务模块结构（Business Module）

在 QwenPaw 中，业务场景通常在 `console/src/business/` 目录下创建独立模块，参考 [marketing 模块](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\business\marketing)：

**标准业务模块结构：**
```
console/src/business/my_module/
├── manifest.ts              # 模块声明（路由、菜单等）
├── pages/
│   ├── MyListPage/
│   │   ├── index.tsx
│   │   ├── components/
│   │   │   ├── MyList.tsx
│   │   │   ├── MyItemCard.tsx
│   │   │   └── MyForm.tsx
│   │   └── hooks/
│   │       └── useMyList.ts
│   └── MyDetailPage/
│       └── index.tsx
├── components/              # 模块内共享组件
│   ├── MyCommonComponent.tsx
│   └── adapters.ts         # 数据适配
└── utils/                  # 工具函数
```

**manifest.ts 的作用：**
- 定义路由配置
- 注册菜单项
- 声明模块依赖

#### 2.2.3 设计页面组件结构

基于需求，为每个页面规划组件层次：

**列表页组件结构示例：**
```
MyListPage (页面容器)
├── PageHeader (通用头部，标题 + 刷新按钮)
├── Card (内容容器)
│   ├── Toolbar (筛选、搜索区)
│   └── Table / List (数据展示)
│       └── ActionButtons (查看、编辑、删除等)
└── Modal (详情/编辑弹窗)
```

**参考 Marketing 页面的实现模式：**
- 使用 Ant Design 的 `Card`、`Table`、`Tag`、`Button`、`Modal` 组件
- 使用 `useTranslation` 进行国际化
- 使用 `useNavigate` 进行路由导航
- API 调用独立到 `api/modules/` 下

#### 2.2.4 创建原型或直接开始实现

根据需求复杂度选择：

**选项 A：快速原型（简单场景）**
直接按照项目模式创建组件文件，使用占位数据渲染界面。

**选项 B：完整规划（复杂场景）**
先创建一份设计文档，描述：
- 页面布局草图
- 组件间的数据流
- 状态管理方案
- API 调用时机

#### 2.2.5 验证设计与项目风格一致

检查点：
- [ ] 使用了 `PageHeader` 组件保持统一的页面头部
- [ ] 使用了项目的主题色（橙色 #ff7f16 等）
- [ ] 支持了深色模式样式
- [ ] 使用了 i18n 进行文本管理
- [ ] 组件命名符合项目规范（PascalCase 组件名，camelCase 文件名）

### 2.3 基于的技能和工具

- **技能：** `web-artisan`（构建前端）、`frontend-design`（UI 设计）
- **工具：** `Read`、`Write`、`LS`（查看项目结构）
- **关键参考代码：**
  - Marketing 商机页面
  - PageHeader 组件
  - Chat 页面的样式结构

---

## 第 3 步：接口定义

### 3.1 主要内容

- 定义 API 端点
- 确定请求/响应数据结构
- 编写接口文档
- 输出：API Schema（Pydantic/TypeScript）、接口文档

### 3.2 具体动作

#### 3.2.1 参考现有 API 结构

查看项目现有的 API 定义：

- 前端 API 模块：[console/src/api/](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\api)
  - [console.ts](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\api\modules\console.ts) - console 模块 API
- 后端路由：[src/qwenpaw/app/routers/](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\qwenpaw\app\routers)
- 场景路由示例：[marketing/router.py](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing\router.py)

#### 3.2.2 定义后端数据模型（Pydantic）

创建 schemas 文件，参考 [marketing/schemas/](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing\schemas)：

```python
# schemas/my_scene.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class MySceneCreate(BaseModel):
    name: str = Field(..., description="名称")
    description: Optional[str] = None

class MySceneRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### 3.2.3 定义前端 API 类型（TypeScript）

在 [console/src/api/types/](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\api\types) 创建类型定义：

```typescript
export interface MyScene {
  id: number;
  name: string;
  createdAt: string;
}

export interface CreateMySceneRequest {
  name: string;
  description?: string;
}
```

#### 3.2.4 定义后端 API 路由

创建 router.py，使用 FastAPI，参考 [marketing/router.py](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing\router.py)：

```python
from fastapi import APIRouter

def create_router() -> APIRouter:
    router = APIRouter(prefix="/api/backend/my-scene", tags=["backend", "my-scene"])
    
    @router.get("/items")
    def list_items():
        return {"items": []}
    
    return router
```

#### 3.2.5 定义前端 API 模块

在 [console/src/api/modules/](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\api\modules) 创建模块文件：

```typescript
import { request } from "../request";
import type { MyScene, CreateMySceneRequest } from "../types/my-scene";

export const mySceneApi = {
  list: () => request<{ items: MyScene[] }>("/api/backend/my-scene/items"),
  create: (data: CreateMySceneRequest) => 
    request<MyScene>("/api/backend/my-scene/items", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
```

### 3.3 基于的技能和工具

- **技能：** `API Documentation Generator`（文档生成）
- **工具：** `Read`、`Write`、`Edit`、`SearchCodebase`

---

## 第 4 步：前后端实现

### 4.1 主要内容

- 实现后端服务（Service、Repository、Router）
- 实现前端页面组件
- 连接前后端
- 输出：完整可运行的功能代码

### 4.2 具体动作

#### 4.2.1 创建场景后端目录结构

参考 [marketing](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing) 场景，创建以下结构：

```
src/backend/scenes/my_scene/
├── __init__.py
├── manifest.py
├── router.py
├── service.py
├── repository.py
├── persistence.py
├── dependencies.py
├── exceptions.py
├── schemas/
│   ├── __init__.py
│   └── my_scene.py
└── hooks/
    └── __init__.py
```

#### 4.2.2 实现后端 Service 层

参考 [marketing/service.py](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing\service.py)，创建业务逻辑服务。

#### 4.2.3 实现后端 Repository 层

创建数据访问层，处理数据存储。

#### 4.2.4 注册场景路由

在 `src/backend/__init__.py` 或适当位置注册你的场景路由。

#### 4.2.5 创建前端页面

在 [console/src/pages/](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\pages) 创建新页面目录：

```
console/src/pages/MyScene/
├── index.tsx
├── components/
│   ├── MySceneList.tsx
│   └── MySceneForm.tsx
└── hooks/
    └── useMyScene.ts
```

使用 React + Ant Design 实现页面，参考 [Chat](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\pages\Chat) 或 [Agent](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\pages\Agent) 页面。

#### 4.2.6 配置前端路由

在 [console/src/App.tsx](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\App.tsx) 中添加新页面路由（如需要）。

#### 4.2.7 运行项目测试

启动前后端服务测试：

**后端**（根据项目文档）：
```powershell
# 在项目根目录
qwenpaw serve
```

**前端**：
```powershell
cd console
npm run dev
```

### 4.3 基于的技能和工具

- **技能：** `web-artisan`、`general_purpose_task`（子任务执行）
- **工具：** `Write`、`Edit`、`Read`、`RunCommand`、`GetDiagnostics`

---

## 第 5 步：技能开发

### 5.1 主要内容

- 设计技能的触发条件
- 实现技能逻辑（SKILL.md）
- 测试技能
- 输出：完整的 SKILL.md 文件

### 5.2 具体动作

#### 5.2.1 学习现有技能结构

查看项目内置技能示例：
- [make-skill-zh](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\qwenpaw\agents\skills\make-skill-zh)
- [cron-zh](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\qwenpaw\agents\skills\cron-zh)
- [file_reader-zh](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\qwenpaw\agents\skills\file_reader-zh)

#### 5.2.2 创建技能目录

在工作区或项目技能目录创建技能：

```
my-skill-zh/
└── SKILL.md
```

#### 5.2.3 编写 SKILL.md

SKILL.md 的基本结构：

```markdown
---
name: my-skill
description: "技能描述，说明何时触发这个技能"
metadata:
  builtin_skill_version: "1.0"
  qwenpaw:
    emoji: "🎯"
    requires: {}
---

# 技能名称

## 步骤 1：...

具体的操作指导...

## 步骤 2：...
```

要点：
- `name`：技能标识，用于 `/<name>` 调用
- `description`：详细的触发条件说明
- 使用祈使句写作
- 分步骤，每步明确操作和工具使用

#### 5.2.4 使用 make-skill 技能（可选）

如果是从对话中沉淀技能，可以使用内置的 `make-skill` 技能：
- 输入 `/make-skill <focus>` 或自然语言如「把这个变成 skill」
- 按照 make-skill 的指引完成

#### 5.2.5 测试技能

在 QwenPaw 中加载并测试技能：
- 确认技能已正确注册
- 测试各种触发场景
- 验证技能执行效果

### 5.3 基于的技能和工具

- **技能：** `make-skill`（从对话生成）、`skill-creator`（技能创建）
- **工具：** `Write`、`Read`、`RunCommand`（测试验证）

---

## 第 6 步：技能集成

### 6.1 主要内容

- 将技能注册到系统
- 在前端集成技能入口
- 配置技能权限和依赖
- 输出：集成后的完整应用

### 6.2 具体动作

#### 6.2.1 将技能放入技能目录

如果是自定义技能，放置在合适的位置：
- Workspace 技能：工作区的 `.qwenpaw/skills/` 目录
- 内置技能（项目级）：`src/qwenpaw/agents/skills/` 目录

#### 6.2.2 在前端添加技能入口

如需要，在前端添加技能调用入口。查看 [Skill Pool](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\api\modules\skill.ts) 相关代码。

#### 6.2.3 配置 Agent 使用技能

在 Agent 配置中启用你的技能，参考 [Agent 相关代码](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\src\api\modules\agent.ts)。

#### 6.2.4 集成 Hooks（可选）

如需要后端 Hook（如回复后处理），参考 [marketing/hooks/post_reply.py](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\src\backend\scenes\marketing\hooks\post_reply.py)。

### 6.3 基于的技能和工具

- **技能：** `search`（查找集成点）
- **工具：** `Read`、`Edit`、`Write`

---

## 第 7 步：部署测试

### 7.1 主要内容

- 完整的端到端测试
- 修复 Bug
- 性能优化
- 准备部署
- 输出：可交付的完整应用

### 7.2 具体动作

#### 7.2.1 运行项目测试

查看项目的测试配置：
- 后端：[pyproject.toml](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\pyproject.toml) 中的 pytest 配置
- 前端：[console/package.json](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\console\package.json) 中的 test 脚本

运行测试命令：

```powershell
# 后端测试
pytest

# 前端测试
cd console
npm run test
npm run lint
```

#### 7.2.2 使用 TRAD 相关技能进行质量保证

- **TRAE-code-review**：执行代码审查
- **TRAE-security-review**：安全扫描
- **TRAE-debugger**：如果有运行时问题，进行调试

#### 7.2.3 E2E 测试（如需要）

查看项目的 [e2e](file:///f:\QiLuProject\QwenPawPlus\QwenPawPro1.9_digital\e2e) 目录，使用 Playwright 进行端到端测试。

#### 7.2.4 构建生产版本

前端构建：
```powershell
cd console
npm run build:prod
```

后端打包（按项目文档）。

#### 7.2.5 编写部署文档

记录部署步骤、环境配置、依赖等。

### 7.3 基于的技能和工具

- **技能：** `TRAE-code-review`、`TRAE-security-review`、`TRAE-debugger`
- **工具：** `RunCommand`、`GetDiagnostics`、`TodoWrite`（跟踪测试任务）

---

## 完整流程检查清单

在交付前，确认完成以下所有项：

- [ ] 需求文档已编写并确认
- [ ] 产品原型已创建并通过审核
- [ ] API 接口已定义并文档化
- [ ] 后端 Service/Repository/Router 已实现
- [ ] 前端页面组件已实现
- [ ] 前后端联调通过
- [ ] 技能已开发完成（如需要）
- [ ] 技能已集成到应用
- [ ] 单元测试已通过
- [ ] E2E 测试已通过
- [ ] 代码审查已完成
- [ ] 安全扫描已通过
- [ ] 部署文档已编写

---

## 技巧与建议

1. **从小处开始**：先实现最小可行产品（MVP），再迭代完善
2. **参考现有代码**：大量复用项目中已有的 patterns
3. **频繁测试**：每完成一步就测试，不要等到最后
4. **使用 TodoWrite**：管理开发任务，保持条理清晰
5. **善用子代理**：对于复杂任务，使用 `general_purpose_task` 分解
