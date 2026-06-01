# AI辅助评审系统 Demo

基于 [AI辅助评审系统技术方案](./AI辅助评审系统技术方案.md) 构建的单文件演示系统。

## 核心流程

```
创建项目 → 规则提取 → 登记供应商(解压) → AI评审(主智能体+3子智能体并行) → 查看结果 → 生成报告
```

## 智能体技能体系

| 角色 | Skill ID | 核心能力 |
|------|----------|---------|
| 🤖 主智能体 | `ai-bid-master` | 并行任务调度、结果聚合、上下文传递（3项） |
| 🕵️ 验真智能体 | `ai-bid-auth` | 营业执照核验、资质证书核验、主体一致性、业绩真实性（4项） |
| 📋 合规审核智能体 | `ai-bid-compliance` | 资格条件审核、否决项检查、符合性审查、法律法规合规（4项） |
| 📊 数据稽核智能体 | `ai-bid-audit` | 金额一致性、报价完整性、价格合理性、算术正确性（4项） |

每个 Skill 包含：
- `SKILL.md` — 完整的技能定义（职责、能力、输入输出契约、失败策略）
- `skill.json` — 结构化元数据（capabilities、check_items、schema）

## 如何运行

### 方式一：Python 直接启动

```bash
pip install fastapi uvicorn python-multipart
python app.py
```

访问 http://localhost:8000

### 方式二：Docker

```bash
docker build -t ai-review-demo .
docker run -p 8000:8000 ai-review-demo
```

### 方式三：一键脚本

```bash
# Linux/macOS
bash start.sh

# Windows
start.bat
```

## 核心场景演示步骤

打开 http://localhost:8000，页面有两个标签页：

### 📋 评审流程（默认）

1. **创建项目** — 填写项目名称、类型、开标时间
2. **规则提取** — 从招标模板自动提取 10 条结构化评审规则
3. **登记供应商** — 点击「快速模拟」跳过文件上传
4. **AI 评审** — 观看三个子智能体并行评审的动画进度
5. **查看结果** — 评审总览 + 明细表 + 子智能体执行摘要
6. **生成报告** — 自动生成最终评审报告

### 🧩 技能管理

1. 点击顶部「技能管理」标签
2. 查看四个智能体的 Skill 卡片列表
3. 点击任一卡片查看详情：核心能力、检查项、输入/输出契约、失败策略
4. 点击「✏️ 编辑 SKILL.md」可在线修改技能定义
5. 点击「💾 保存」将修改写回（内存 + 磁盘）

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger UI。

### 评审业务 API

| Method | Endpoint | 说明 |
|--------|----------|------|
| POST | `/api/agents/{agentId}/bid-projects` | 创建项目 |
| GET | `/api/agents/{agentId}/bid-projects/{pid}` | 查询项目 |
| POST | `.../rule-extraction-jobs` | 规则提取 |
| GET | `.../review-rules` | 查询规则 |
| POST | `.../suppliers` | 登记供应商 |
| GET | `.../suppliers/{sid}/files` | 文件清单 |
| POST | `.../suppliers/{sid}/review-jobs` | 启动评审 |
| GET | `.../suppliers/{sid}/review-summary` | 评审总览 |
| GET | `.../suppliers/{sid}/review-details` | 评审详情 |
| GET | `.../suppliers/{sid}/review-result` | 原始结果 |
| POST | `.../suppliers/{sid}/report-jobs` | 生成报告 |
| GET | `.../suppliers/{sid}/report-result` | 报告结果 |

### Skill 管理 API

| Method | Endpoint | 说明 |
|--------|----------|------|
| GET | `/api/skills` | 列出所有 Skill |
| GET | `/api/skills/{skillId}` | 获取 Skill 元数据 |
| GET | `/api/skills/{skillId}/skill-md` | 获取 SKILL.md 内容 |
| PUT | `/api/skills/{skillId}/skill-md` | 更新 SKILL.md 内容 |

## 已知限制

1. **无真实 Agent 调用** — 智能体行为完全由 Mock 模拟，不依赖 qwenpaw 运行时
2. **内存存储** — 数据仅部分持久化到 `demo_data/`，重启后需重新操作
3. **单供应商** — UI 只演示单个供应商的完整流程，实际系统支持多供应商
4. **无用户认证** — 无登录/权限控制
5. **Mock 数据固定** — 评审结果预设，不根据上传文件内容变化
6. **异步任务无持久化** — 刷新页面不会中断后台任务，但重启会丢失
7. **仅 Happy Path** — 未处理网络超时、并发冲突、异常重试等边缘场景

## 技术栈

- Python 3.10+
- FastAPI + Uvicorn
- 嵌入式单页 Web UI（原生 JS，零依赖，双标签页）
- Pydantic v2 数据模型
