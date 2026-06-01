"""
AI辅助评审系统 - Demo (单文件实现)
=====================================
基于 FastAPI，模拟完整评审流程：项目创建 → 规则提取 → 供应商登记 →
AI评审(主智能体+3子智能体并行) → 结果查看 → 报告生成

启动: python app.py
访问: http://localhost:8000
"""

import asyncio
import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

AGENT_ID = "ai-bid-master"
AUTH_AGENT_ID = "ai-bid-auth"
COMPLIANCE_AGENT_ID = "ai-bid-compliance"
AUDIT_AGENT_ID = "ai-bid-audit"

WORKSPACE_DIR = Path("./demo_data")
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# 枚举
# ──────────────────────────────────────────────

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    RULES_READY = "rules_ready"
    REVIEW_COMPLETED = "review_completed"
    REPORT_GENERATED = "report_generated"


class SupplierStatus(str, Enum):
    CREATED = "created"
    EXTRACTING_FILES = "extracting_files"
    FILES_READY = "files_ready"
    REVIEWING = "reviewing"
    REVIEWED = "reviewed"
    REPORT_READY = "report_ready"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    RULE_EXTRACTION = "rule_extraction"
    REVIEW = "review"
    REPORT = "report"


# ──────────────────────────────────────────────
# 数据模型
# ──────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    name: str
    project_type: str = "服务类"
    description: str = ""
    bid_opening_time: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    project_type: str
    description: str
    bid_opening_time: str
    status: ProjectStatus
    main_review_agent_id: str
    auth_agent_id: str
    compliance_agent_id: str
    audit_agent_id: str
    rule_file_path: Optional[str] = None
    created_at: str
    updated_at: str


class SupplierRequest(BaseModel):
    supplier_name: str


class SupplierResponse(BaseModel):
    id: str
    project_id: str
    supplier_name: str
    status: SupplierStatus
    extract_dir: Optional[str] = None
    file_list_path: Optional[str] = None
    created_at: str


class JobResponse(BaseModel):
    job_id: str
    project_id: str
    supplier_id: Optional[str] = None
    job_type: JobType
    status: JobStatus
    agent_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str


class ReviewSummary(BaseModel):
    project_name: str
    supplier_name: str
    final_conclusion: str
    review_time: str
    item_count: int
    confidence: str


class ReviewItem(BaseModel):
    item_id: str
    category: str
    item_name: str
    requirement: str
    conclusion: str
    detail: str


class ReviewDetail(BaseModel):
    project_name: str
    supplier_name: str
    review_time: str
    final_conclusion: str
    confidence: str
    review_items: list[dict]
    sub_agent_results: dict
    issues: list[dict]


# ──────────────────────────────────────────────
# 内存存储 (Mock)
# ──────────────────────────────────────────────

projects: dict[str, dict] = {}
suppliers: dict[str, dict] = {}
jobs: dict[str, dict] = {}
rules: dict[str, dict] = {}
review_results: dict[str, dict] = {}
report_results: dict[str, dict] = {}


def now_iso() -> str:
    return datetime.now().isoformat()


def project_dir(project_id: str) -> Path:
    p = WORKSPACE_DIR / "projects" / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def supplier_dir(project_id: str, supplier_id: str) -> Path:
    p = WORKSPACE_DIR / "projects" / project_id / "runtime" / supplier_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def results_dir(project_id: str, supplier_id: str) -> Path:
    p = WORKSPACE_DIR / "projects" / project_id / "results" / supplier_id
    p.mkdir(parents=True, exist_ok=True)
    return p


# ──────────────────────────────────────────────
# Mock 智能体系统
# ──────────────────────────────────────────────

MOCK_RULES_TEMPLATE = {
    "rules": [
        {"id": "R001", "category": "资质条件", "item_name": "营业执照", "requirement": "必须提供有效的营业执照，经营范围包含本项目相关业务"},
        {"id": "R002", "category": "资质条件", "item_name": "资质证书", "requirement": "ISO9001质量管理体系认证或同等资质"},
        {"id": "R003", "category": "否决项", "item_name": "投标保证金", "requirement": "投标保证金不低于投标总价的2%，须在开标前到账"},
        {"id": "R004", "category": "否决项", "item_name": "投标有效期", "requirement": "投标有效期不少于90天"},
        {"id": "R005", "category": "符合性", "item_name": "投标函签署", "requirement": "投标函须由法定代表人签字并加盖公章"},
        {"id": "R006", "category": "符合性", "item_name": "授权委托书", "requirement": "如有授权代表，须提供有效的授权委托书"},
        {"id": "R007", "category": "商务评审", "item_name": "报价完整性", "requirement": "报价清单须覆盖全部采购项，无缺项漏项"},
        {"id": "R008", "category": "商务评审", "item_name": "分项报价合理性", "requirement": "各分项报价不得明显偏离市场均价（±30%以内）"},
        {"id": "R009", "category": "技术评审", "item_name": "技术方案完整性", "requirement": "技术方案须包含系统架构、部署方案、实施计划"},
        {"id": "R010", "category": "技术评审", "item_name": "人员配置", "requirement": "项目经理须具备PMP或同等认证，核心技术人员不少于3人"},
    ]
}


def mock_verification_result(supplier_name: str) -> dict:
    return {
        "agent_role": "验真智能体",
        "conclusion": "通过",
        "issues": [],
        "evidence": [
            {"item": "营业执照", "check": "工商系统查询一致", "result": "真实有效"},
            {"item": "资质证书", "check": "发证机构官网核实", "result": "证书有效"},
            {"item": "主体一致性", "check": "投标人名称与营业执照一致", "result": "一致"},
        ],
        "summary": f"「{supplier_name}」提交的材料真实有效，主体信息与工商登记一致，资质证书在有效期内。"
    }


def mock_compliance_result(supplier_name: str) -> dict:
    return {
        "agent_role": "合规审核智能体",
        "conclusion": "通过（1项建议整改）",
        "issues": [
            {
                "rule_id": "R003",
                "severity": "建议",
                "description": "投标保证金汇款凭证中备注信息不完整，建议补充项目编号"
            }
        ],
        "evidence": [
            {"rule_id": "R001", "check": "营业执照", "result": "符合"},
            {"rule_id": "R002", "check": "资质证书", "result": "符合"},
            {"rule_id": "R003", "check": "投标保证金", "result": "建议整改"},
            {"rule_id": "R004", "check": "投标有效期", "result": "符合"},
            {"rule_id": "R005", "check": "投标函签署", "result": "符合"},
            {"rule_id": "R006", "check": "授权委托书", "result": "符合"},
        ],
        "summary": f"「{supplier_name}」满足全部资格条件和否决项要求，无重大不合规项。1项建议整改（保证金备注）。"
    }


def mock_audit_result(supplier_name: str) -> dict:
    return {
        "agent_role": "数据稽核智能体",
        "conclusion": "通过",
        "issues": [],
        "evidence": [
            {"item": "投标总价", "expected": "≤预算", "actual": "¥8,560,000", "result": "在预算内"},
            {"item": "分项报价合计", "expected": "=投标总价", "actual": "¥8,560,000", "result": "一致"},
            {"item": "大写金额", "expected": "=小写金额", "actual": "捌佰伍拾陆万元整", "result": "一致"},
            {"item": "数量×单价", "expected": "=分项金额", "actual": "已核对10项", "result": "一致"},
        ],
        "summary": f"「{supplier_name}」报价金额一致，大写小写匹配，分项合计与总价一致，无算术错误。"
    }


def mock_review_result(project_name: str, supplier_name: str, rules_data: dict) -> dict:
    """模拟主智能体聚合三个子智能体结果"""
    return {
        "project_name": project_name,
        "supplier_name": supplier_name,
        "review_time": now_iso(),
        "final_conclusion": "通过",
        "review_items": [
            {
                "item_id": r["id"],
                "category": r["category"],
                "item_name": r["item_name"],
                "requirement": r["requirement"],
                "verification": "通过",
                "compliance": "建议整改" if r["id"] == "R003" else "通过",
                "audit": "通过" if r["category"] == "商务评审" else "不适用",
                "conclusion": "通过"
            }
            for r in rules_data.get("rules", [])
        ],
        "sub_agent_results": {
            "verification_result": {"conclusion": "通过", "summary": "所有材料真实有效"},
            "compliance_result": {"conclusion": "通过（1项建议整改）", "summary": "满足资格条件，1项建议"},
            "audit_result": {"conclusion": "通过", "summary": "报价数据一致无误"}
        },
        "issues": [],
        "confidence": "high"
    }


def mock_report_result(project_name: str, supplier_name: str, review: dict) -> dict:
    return {
        "report_title": f"AI辅助评审报告 - {project_name}",
        "supplier_name": supplier_name,
        "generated_at": now_iso(),
        "final_conclusion": review.get("final_conclusion", "N/A"),
        "confidence": review.get("confidence", "N/A"),
        "summary": {
            "total_items": len(review.get("review_items", [])),
            "passed": sum(1 for i in review.get("review_items", []) if i.get("conclusion") == "通过"),
            "issues": len(review.get("issues", [])),
        },
        "report_items": review.get("review_items", []),
        "issues": review.get("issues", []),
        "sub_agent_summary": review.get("sub_agent_results", {}),
        "disclaimer": "本报告由AI辅助评审系统自动生成，仅供参考，最终评审结果以人工确认为准。"
    }


# ──────────────────────────────────────────────
# Skill 管理 — 子智能体技能定义
# ──────────────────────────────────────────────

SKILLS_DIR = WORKSPACE_DIR / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

SKILL_DEFINITIONS = {
    "ai-bid-auth": {
        "id": "ai-bid-auth",
        "name": "验真智能体",
        "version": "1.0.0",
        "description": "负责投标材料真伪核验与主体一致性检查",
        "agent_role": "验真",
        "capabilities": [
            {"name": "营业执照核验", "method": "工商系统比对", "check_items": ["统一社会信用代码有效性", "经营范围匹配", "注册资本满足要求", "经营状态正常"]},
            {"name": "资质证书核验", "method": "发证机构官网核实", "check_items": ["证书编号真实性", "有效期检查", "认证范围覆盖", "发证机构权威性"]},
            {"name": "主体一致性", "method": "多文件交叉比对", "check_items": ["投标人名称一致性", "法定代表人一致性", "地址一致性", "公章一致性"]},
            {"name": "业绩真实性", "method": "合同/验收单核验", "check_items": ["合同签约方一致性", "项目金额合理性", "时间逻辑性"]},
        ],
        "input_schema": {"files": "投标文件清单 (files.json)", "rules": "评审规则引用"},
        "output_schema": {"format": "verification-result.json", "fields": ["agent_role", "conclusion", "issues", "evidence", "summary"]},
        "failure_strategy": "标记issues，conclusion降级为'需复核'",
        "skill_md": """# 验真智能体 (Verification Agent)

## 职责
对投标供应商提交的材料进行真伪核验，确保所有资质文件、主体信息真实有效。

## 核心能力

### 1. 营业执照核验
- 通过工商系统查询统一社会信用代码
- 核验经营范围是否覆盖本项目
- 检查注册资本是否满足招标要求
- 确认企业经营状态正常（非注销/吊销）

### 2. 资质证书核验
- 在发证机构官网查验证书编号
- 确认证书在有效期内
- 核验认证范围是否覆盖采购需求

### 3. 主体一致性检查
- 投标人名称 vs 营业执照名称
- 法定代表人 vs 工商登记信息
- 公章样式 vs 备案样式
- 地址信息一致性

### 4. 业绩真实性核验
- 合同签约方一致性
- 项目金额合理性
- 时间逻辑性（合同→验收）

## 输出格式
```json
{
  "agent_role": "验真智能体",
  "conclusion": "通过|需复核|不通过",
  "issues": [],
  "evidence": [{"item": "", "check": "", "result": ""}],
  "summary": ""
}
```

## 失败策略
发现材料造假 → conclusion="不通过"
材料缺失但可补正 → conclusion="需复核"，在issues中列出
"""
    },
    "ai-bid-compliance": {
        "id": "ai-bid-compliance",
        "name": "合规审核智能体",
        "version": "1.0.0",
        "description": "负责资格条件、否决项与符合性审查",
        "agent_role": "合规审核",
        "capabilities": [
            {"name": "资格条件审核", "method": "规则逐条匹配", "check_items": ["营业范围", "资质等级", "财务状况", "业绩要求", "人员要求"]},
            {"name": "否决项检查", "method": "红色标记触发", "check_items": ["投标保证金", "投标有效期", "联合体要求", "分包限制"]},
            {"name": "符合性审查", "method": "形式要件校验", "check_items": ["投标函签署", "授权委托书", "技术方案完整性", "报价表盖章"]},
            {"name": "法律法规合规", "method": "法规条款比对", "check_items": ["政府采购法", "招标投标法", "行业监管要求"]},
        ],
        "input_schema": {"rules": "评审规则文件 (rules.json)", "files": "投标文件清单"},
        "output_schema": {"format": "compliance-result.json", "fields": ["agent_role", "conclusion", "issues", "evidence", "summary"]},
        "failure_strategy": "否决项不通过→整体不通过；建议项→标记issues",
        "skill_md": """# 合规审核智能体 (Compliance Agent)

## 职责
依据招标文件和评审规则，对投标文件进行资格条件、否决项与符合性逐项审核。

## 核心能力

### 1. 资格条件审核
逐条对照招标文件中的资格要求：
- 营业范围是否覆盖采购内容
- 资质等级是否满足要求
- 财务状况（审计报告）是否符合门槛
- 类似业绩数量/金额是否达标
- 人员配置是否满足最低要求

### 2. 否决项检查
触发即不通过的关键项：
- 投标保证金金额/到账时间
- 投标有效期（不少于90天）
- 联合体协议（如适用）
- 分包限制合规性

### 3. 符合性审查
形式要件完整性：
- 投标函法定代表人签字+公章
- 授权委托书有效性
- 技术方案结构完整
- 报价表签字盖章

### 4. 法律法规合规
- 政府采购法相关条款
- 招标投标法要求
- 行业特定监管要求

## 判定规则
- 否决项不通过 → 整体结论"不通过"
- 资格条件不满足 → 整体结论"不通过"
- 符合性缺失（可补正）→ 标记issues，结论"建议整改"

## 输出格式
```json
{
  "agent_role": "合规审核智能体",
  "conclusion": "通过|建议整改|不通过",
  "issues": [{"rule_id": "", "severity": "否决|建议", "description": ""}],
  "evidence": [{"rule_id": "", "check": "", "result": ""}],
  "summary": ""
}
```
"""
    },
    "ai-bid-audit": {
        "id": "ai-bid-audit",
        "name": "数据稽核智能体",
        "version": "1.0.0",
        "description": "负责报价金额一致性与算术正确性校验",
        "agent_role": "数据稽核",
        "capabilities": [
            {"name": "金额一致性", "method": "多维度交叉验证", "check_items": ["大写金额=小写金额", "分项合计=投标总价", "数量×单价=分项金额", "税率计算正确"]},
            {"name": "报价完整性", "method": "清单逐项核对", "check_items": ["无缺项漏项", "报价项与采购清单一一对应", "备品备件报价完整"]},
            {"name": "价格合理性", "method": "市场均价偏离度", "check_items": ["分项报价偏离度≤±30%", "总价在预算内", "无异常低价竞标"]},
            {"name": "算术正确性", "method": "公式重新计算", "check_items": ["合计=∑分项", "含税价=不含税价×(1+税率)", "折扣后价格计算正确"]},
        ],
        "input_schema": {"files": "报价相关文件", "budget": "预算金额（来自规则）"},
        "output_schema": {"format": "audit-result.json", "fields": ["agent_role", "conclusion", "issues", "evidence", "summary"]},
        "failure_strategy": "算术错误→标记issues并重新计算；严重偏离→不通过",
        "skill_md": """# 数据稽核智能体 (Audit Agent)

## 职责
对投标报价进行数据一致性校验和算术正确性验证，确保报价无计算错误和逻辑矛盾。

## 核心能力

### 1. 金额一致性验证
- 大写金额 vs 小写金额
- 分项报价合计 vs 投标总价
- 数量 × 单价 vs 分项金额
- 税率计算（含税/不含税）

### 2. 报价完整性检查
- 逐项核对报价清单是否覆盖全部采购项
- 检查是否有漏报（缺项）或多报
- 备品备件、专用工具报价完整性

### 3. 价格合理性分析
- 分项报价与市场均价偏离度（±30%阈值）
- 投标总价是否在预算范围内
- 异常低价竞标检测

### 4. 算术正确性
- 合计=∑各分项金额
- 含税价=不含税价×(1+税率)
- 折扣后价格=原价×(1-折扣率)
- 运杂费、保险费等附加项计算正确

## 输出格式
```json
{
  "agent_role": "数据稽核智能体",
  "conclusion": "通过|需复核|不通过",
  "issues": [{"item": "", "expected": "", "actual": "", "result": ""}],
  "evidence": [{"item": "", "expected": "", "actual": "", "result": ""}],
  "summary": ""
}
```

## 容忍度
- 分项合计与总价偏差 < 0.01元 → 视为一致
- 市场均价偏离 ≤30% → 正常范围
"""
    },
    "ai-bid-master": {
        "id": "ai-bid-master",
        "name": "AI辅助评审主智能体",
        "version": "1.0.0",
        "description": "负责并行调度三个子智能体并聚合评审结果",
        "agent_role": "主评审编排",
        "capabilities": [
            {"name": "并行任务调度", "method": "submit_to_agent + check_agent_task", "check_items": ["同时启动三子智能体", "轮询子任务状态", "超时处理"]},
            {"name": "结果聚合", "method": "子结果读取+合并", "check_items": ["读取三个子结果JSON", "按评审项逐条合并", "生成统一结论"]},
            {"name": "上下文传递", "method": "prompt注入", "check_items": ["规则路径", "文件清单路径", "子智能体ID", "输出路径"]},
        ],
        "input_schema": {"rules_file_path": "评审规则路径", "files_manifest_path": "文件清单路径", "supplier_name": "供应商名称", "sub_agent_ids": ["auth", "compliance", "audit"]},
        "output_schema": {"format": "review-result.json", "fields": ["project_name", "supplier_name", "final_conclusion", "review_items", "sub_agent_results", "issues", "confidence"]},
        "failure_strategy": "单子智能体失败→issues标记，final_conclusion降级为'需复核'",
        "skill_md": """# AI辅助评审主智能体 (Master Review Agent)

## 职责
接收Backend传入的评审上下文，并行调度验真、合规审核、数据稽核三个子智能体，聚合结果生成统一评审报告。

## 核心流程

### 1. 上下文解析
从prompt中提取：
- `rules_file_path` — 评审规则JSON路径
- `files_manifest_path` — 供应商文件清单路径
- `supplier_name` — 供应商名称
- `auth_agent_id` / `compliance_agent_id` / `audit_agent_id` — 子智能体ID
- 三个子结果输出路径 + 主结果输出路径

### 2. 并行调度
使用 qwenpaw 内置工具：
- `submit_to_agent(auth_agent_id, prompt)` → 验真任务
- `submit_to_agent(compliance_agent_id, prompt)` → 合规审核任务
- `submit_to_agent(audit_agent_id, prompt)` → 数据稽核任务
- `check_agent_task(task_id)` → 轮询三个子任务

### 3. 结果聚合
- 读取三个子结果JSON文件
- 按评审规则逐条合并（每条评审项标注验真/合规/稽核结果）
- 生成 final_conclusion（三子全通过→通过；任一不通过→不通过；任一需复核→需复核）
- 汇总 issues 列表
- 评估 confidence（三子置信度加权）

### 4. 输出
- 写入 review-result.json 到指定路径
- 包含 sub_agent_results 字段引用三个子结果路径
"""
    },
}

# 初始化：将 Skill 定义写入文件系统
def _init_skills():
    for skill_id, skill_data in SKILL_DEFINITIONS.items():
        skill_dir = SKILLS_DIR / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)
        # 写入 SKILL.md
        (skill_dir / "SKILL.md").write_text(skill_data["skill_md"], encoding="utf-8")
        # 写入 skill.json（元数据，不含完整md内容）
        meta = {k: v for k, v in skill_data.items() if k != "skill_md"}
        (skill_dir / "skill.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

_init_skills()


def get_skill_meta(skill_id: str) -> Optional[dict]:
    """获取 Skill 元数据"""
    if skill_id in SKILL_DEFINITIONS:
        return {k: v for k, v in SKILL_DEFINITIONS[skill_id].items() if k != "skill_md"}
    return None


def get_skill_md(skill_id: str) -> Optional[str]:
    """获取 Skill 的 SKILL.md 内容"""
    if skill_id in SKILL_DEFINITIONS:
        return SKILL_DEFINITIONS[skill_id]["skill_md"]
    return None


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

app = FastAPI(title="AI辅助评审系统 Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════
# Web UI (嵌入式单页)
# ══════════════════════════════════════════════

WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI辅助评审系统 - Demo</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;color:#333}
.header{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:20px 40px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:22px;font-weight:600}
.header .badge{background:rgba(255,255,255,.2);padding:4px 12px;border-radius:12px;font-size:12px}
.container{max-width:1200px;margin:24px auto;padding:0 20px}
.card{background:#fff;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card h3{font-size:16px;margin-bottom:16px;color:#1a73e8;border-bottom:2px solid #e8eaed;padding-bottom:8px}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end}
.form-group{display:flex;flex-direction:column;gap:6px;min-width:180px}
.form-group label{font-size:13px;color:#666;font-weight:500}
.form-group input,.form-group select{padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px}
.form-group input:focus,.form-group select:focus{outline:none;border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.15)}
.btn{padding:8px 20px;border:none;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500;transition:all .2s}
.btn-primary{background:#1a73e8;color:#fff}
.btn-primary:hover{background:#1557b0}
.btn-success{background:#0d904f;color:#fff}
.btn-success:hover{background:#0a6e3c}
.btn-warning{background:#e8a817;color:#fff}
.btn-warning:hover{background:#c48f14}
.btn:disabled{opacity:.5;cursor:not-allowed}
.flow-steps{display:flex;gap:8px;margin-bottom:24px;overflow-x:auto}
.flow-step{flex:1;min-width:120px;padding:12px;border-radius:8px;text-align:center;font-size:13px;background:#e8eaed;color:#999;position:relative}
.flow-step.active{background:#1a73e8;color:#fff;font-weight:600}
.flow-step.done{background:#e6f4ea;color:#0d904f;font-weight:500}
.flow-step .step-num{display:block;font-size:20px;font-weight:700;margin-bottom:4px}
.result-box{background:#f8f9fa;border-radius:8px;padding:16px;margin-top:12px;max-height:500px;overflow-y:auto}
.result-box pre{font-size:12px;white-space:pre-wrap;word-break:break-all;margin:0}
.tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500}
.tag-pass{background:#e6f4ea;color:#0d904f}
.tag-warn{background:#fef7e0;color:#e8a817}
.tag-info{background:#e8f0fe;color:#1a73e8}
.info-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-top:12px}
.info-item{background:#f8f9fa;padding:10px 14px;border-radius:8px}
.info-item .label{font-size:11px;color:#999;text-transform:uppercase}
.info-item .value{font-size:15px;font-weight:600;margin-top:2px}
.progress-bar{height:4px;background:#e8eaed;border-radius:2px;margin-top:12px;overflow:hidden}
.progress-bar .fill{height:100%;background:#1a73e8;border-radius:2px;transition:width .3s}
.table{width:100%;border-collapse:collapse;font-size:13px}
.table th{background:#f8f9fa;padding:10px 12px;text-align:left;font-weight:600;border-bottom:2px solid #e8eaed}
.table td{padding:10px 12px;border-bottom:1px solid #e8eaed}
/* Tab Navigation */
.tab-nav{display:flex;gap:0;margin-bottom:20px;border-bottom:2px solid #e8eaed}
.tab-btn{padding:10px 24px;border:none;background:none;font-size:14px;cursor:pointer;color:#666;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .2s}
.tab-btn.active{color:#1a73e8;border-bottom-color:#1a73e8;font-weight:600}
.tab-btn:hover{color:#1a73e8}
/* Skill cards */
.skill-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.skill-card{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;cursor:pointer;transition:all .2s}
.skill-card:hover{border-color:#1a73e8;box-shadow:0 2px 8px rgba(26,115,232,.12)}
.skill-card.selected{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.2)}
.skill-card .skill-icon{font-size:28px;margin-bottom:8px}
.skill-card .skill-name{font-size:15px;font-weight:600;margin-bottom:4px}
.skill-card .skill-desc{font-size:12px;color:#666;margin-bottom:8px}
.cap-list{margin:0;padding:0;list-style:none}
.cap-list li{padding:6px 0;font-size:13px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between}
.cap-list li:last-child{border-bottom:none}
.skill-detail-panel{background:#fff;border-radius:12px;padding:24px;margin-top:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.skill-md-editor{width:100%;min-height:300px;font-family:'SF Mono',Monaco,'Cascadia Code',monospace;font-size:13px;padding:16px;border:1px solid #ddd;border-radius:8px;resize:vertical;line-height:1.6}
.skill-md-editor:focus{outline:none;border-color:#1a73e8}
/* Check items */
.check-items{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.check-item{background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:10px;font-size:11px}
#log .log-line{padding:3px 0;font-size:12px;font-family:monospace;color:#666}
#log .log-line.info{color:#1a73e8}
#log .log-line.success{color:#0d904f}
#log .log-line.warn{color:#e8a817}
</style>
</head>
<body>
<div class="header">
  <div><h1>🤖 AI辅助评审系统</h1><span style="font-size:12px;opacity:.8">主智能体 + 验真 / 合规审核 / 数据稽核 三子智能体并行评审</span></div>
  <span class="badge">Demo v1.0</span>
</div>

<div class="container">

  <!-- 标签导航 -->
  <div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('review')">📋 评审流程</button>
    <button class="tab-btn" onclick="switchTab('skills')">🧩 技能管理</button>
  </div>

  <!-- ======== Tab: 评审流程 ======== -->
  <div class="tab-content" id="tab-review">

  <!-- 流程步骤条 -->
  <div class="flow-steps">
    <div class="flow-step active" id="step1"><span class="step-num">1</span>创建项目</div>
    <div class="flow-step" id="step2"><span class="step-num">2</span>规则提取</div>
    <div class="flow-step" id="step3"><span class="step-num">3</span>登记供应商</div>
    <div class="flow-step" id="step4"><span class="step-num">4</span>AI评审</div>
    <div class="flow-step" id="step5"><span class="step-num">5</span>查看结果</div>
    <div class="flow-step" id="step6"><span class="step-num">6</span>生成报告</div>
  </div>

  <!-- 项目信息 -->
  <div class="card" id="projectCard" style="display:none">
    <h3>📋 项目信息</h3>
    <div class="info-grid" id="projectInfo"></div>
  </div>

  <!-- Step 1: 创建项目 -->
  <div class="card" id="card1">
    <h3>Step 1 — 创建评审项目</h3>
    <div class="row">
      <div class="form-group" style="flex:2">
        <label>项目名称</label>
        <input id="projName" value="2025年智慧城市云平台技术服务公开采购项目" placeholder="输入项目名称">
      </div>
      <div class="form-group">
        <label>项目类型</label>
        <select id="projType"><option>服务类</option><option>货物类</option><option>工程类</option></select>
      </div>
      <div class="form-group">
        <label>开标时间</label>
        <input id="projTime" type="datetime-local" value="2025-06-15T14:00">
      </div>
      <div class="form-group" style="justify-content:flex-end">
        <button class="btn btn-primary" onclick="createProject()">创建项目</button>
      </div>
    </div>
  </div>

  <!-- Step 2: 规则提取 -->
  <div class="card" id="card2" style="display:none">
    <h3>Step 2 — 规则提取</h3>
    <p style="color:#666;font-size:13px;margin-bottom:12px">从招标文件模板中自动提取结构化评审规则</p>
    <button class="btn btn-primary" onclick="extractRules()">🔍 提取评审规则</button>
    <div id="rulesResult" style="margin-top:12px"></div>
  </div>

  <!-- Step 3: 登记供应商 -->
  <div class="card" id="card3" style="display:none">
    <h3>Step 3 — 登记供应商</h3>
    <div class="row">
      <div class="form-group" style="flex:2">
        <label>供应商名称</label>
        <input id="supplierName" value="星辰科技有限公司" placeholder="输入供应商名称">
      </div>
      <div class="form-group">
        <label>投标文件包 (.zip)</label>
        <input type="file" id="supplierFile" accept=".zip" style="padding:7px">
      </div>
      <div class="form-group" style="justify-content:flex-end">
        <button class="btn btn-primary" onclick="registerSupplier()">登记供应商</button>
        <button class="btn btn-warning" onclick="registerSupplierMock()" style="margin-top:8px">⚡ 快速模拟（跳过上传）</button>
      </div>
    </div>
    <div id="supplierResult" style="margin-top:12px"></div>
  </div>

  <!-- Step 4: 启动评审 -->
  <div class="card" id="card4" style="display:none">
    <h3>Step 4 — 启动AI评审</h3>
    <p style="color:#666;font-size:13px;margin-bottom:12px">
      主智能体并行调度三个子智能体：<br>
      🕵️ <b>验真智能体</b> — 材料真伪、主体一致性<br>
      📋 <b>合规审核智能体</b> — 资格条件、否决项、符合性<br>
      📊 <b>数据稽核智能体</b> — 报价、金额、数量一致性
    </p>
    <button class="btn btn-success" id="btnReview" onclick="startReview()">🚀 启动AI评审</button>
    <div id="reviewProgress" style="margin-top:12px"></div>
  </div>

  <!-- Step 5: 评审结果 -->
  <div class="card" id="card5" style="display:none">
    <h3>Step 5 — 评审结果</h3>
    <div id="reviewSummary"></div>
    <div id="reviewDetails" style="margin-top:16px"></div>
  </div>

  <!-- Step 6: 生成报告 -->
  <div class="card" id="card6" style="display:none">
    <h3>Step 6 — 生成评审报告</h3>
    <button class="btn btn-success" onclick="generateReport()">📄 生成报告</button>
    <div id="reportResult" style="margin-top:12px"></div>
  </div>

  <!-- 操作日志 -->
  <div class="card" id="logCard" style="display:none">
    <h3>📝 操作日志</h3>
    <div id="log" style="max-height:200px;overflow-y:auto"></div>
  </div>

  </div><!-- /tab-review -->

  <!-- ======== Tab: 技能管理 ======== -->
  <div class="tab-content" id="tab-skills" style="display:none">

  <div class="skill-grid" id="skillGrid"></div>
  <div id="skillDetail" class="skill-detail-panel" style="display:none"></div>

  </div><!-- /tab-skills -->

</div><!-- /container -->

<script>
const API = '/api/agents/ai-bid-master/bid-projects';
const SKILL_API = '/api/skills';
let projectId = null, supplierId = null;
let selectedSkillId = null;

function switchTab(tab){
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c=>c.style.display='none');
  if(tab==='review'){
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
    document.getElementById('tab-review').style.display='block';
  }else{
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
    document.getElementById('tab-skills').style.display='block';
    loadSkills();
  }
}

async function loadSkills(){
  try{
    const res=await fetch(SKILL_API);
    const skills=await res.json();
    let html='';
    skills.forEach(s=>{
      const icons={verification:'🕵️',compliance:'📋',audit:'📊',orchestration:'🤖'};
      const icon=icons[s.agent_role]||'🧩';
      html+=`<div class="skill-card" id="skill-${s.id}" onclick="selectSkill('${s.id}')">
        <div class="skill-icon">${icon}</div>
        <div class="skill-name">${s.name}</div>
        <div class="skill-desc">${s.description}</div>
        <div style="font-size:11px;color:#999">v${s.version} · ${s.capability_count}项能力 · ID: ${s.id}</div>
      </div>`;
    });
    document.getElementById('skillGrid').innerHTML=html;
    if(selectedSkillId) selectSkill(selectedSkillId);
  }catch(e){log('加载技能列表失败: '+e.message,'warn')}
}

async function selectSkill(sid){
  selectedSkillId=sid;
  document.querySelectorAll('.skill-card').forEach(c=>c.classList.remove('selected'));
  const card=document.getElementById('skill-'+sid);
  if(card) card.classList.add('selected');

  try{
    const [metaRes,mdRes]=await Promise.all([
      fetch(SKILL_API+'/'+sid),
      fetch(SKILL_API+'/'+sid+'/skill-md')
    ]);
    const meta=await metaRes.json();
    const md=await mdRes.json();

    let capsHtml='';
    (meta.capabilities||[]).forEach((cap,i)=>{
      capsHtml+=`<li>
        <span><b>${i+1}. ${cap.name}</b> <span style="color:#999;font-size:11px">(${cap.method})</span></span>
        <span></span>
      </li>
      <li style="padding-left:20px;font-size:12px;color:#666">
        <div class="check-items">${(cap.check_items||[]).map(c=>`<span class="check-item">${c}</span>`).join('')}</div>
      </li>`;
    });

    document.getElementById('skillDetail').style.display='block';
    document.getElementById('skillDetail').innerHTML=`
      <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:16px">
        <div>
          <h3 style="border:none;margin:0;padding:0">${meta.name} <span class="tag tag-info">${meta.agent_role}</span></h3>
          <p style="color:#666;font-size:13px;margin-top:4px">${meta.description} · v${meta.version}</p>
        </div>
        <div>
          <button class="btn btn-primary" onclick="toggleEditor()" id="btnEdit">✏️ 编辑 SKILL.md</button>
          <button class="btn btn-success" onclick="saveSkillMd()" id="btnSave" style="display:none">💾 保存</button>
          <button class="btn" onclick="toggleEditor()" id="btnCancel" style="display:none;background:#ddd">取消</button>
        </div>
      </div>

      <h4 style="font-size:14px;margin-bottom:8px;color:#333">🛠️ 核心能力 (${meta.capability_count}项)</h4>
      <ul class="cap-list">${capsHtml}</ul>

      <div style="margin-top:16px">
        <h4 style="font-size:14px;margin-bottom:8px;color:#333">
          📥 输入 / 📤 输出
        </h4>
        <div class="info-grid" style="grid-template-columns:1fr 1fr">
          <div class="info-item">
            <div class="label">输入 Schema</div>
            <div class="value" style="font-size:12px;font-weight:normal">${JSON.stringify(meta.input_schema,null,2)}</div>
          </div>
          <div class="info-item">
            <div class="label">输出 Schema</div>
            <div class="value" style="font-size:12px;font-weight:normal">${JSON.stringify(meta.output_schema,null,2)}</div>
          </div>
        </div>
        <div class="info-item" style="margin-top:8px">
          <div class="label">失败策略</div>
          <div class="value" style="font-size:12px;font-weight:normal">${meta.failure_strategy}</div>
        </div>
      </div>

      <div style="margin-top:20px">
        <h4 style="font-size:14px;margin-bottom:8px;color:#333">📄 SKILL.md</h4>
        <textarea class="skill-md-editor" id="skillMdEditor" readonly></textarea>
        <div id="skillMdPreview" style="margin-top:8px;font-size:12px;color:#666"></div>
      </div>
    `;
    // 单独设置 textarea 内容避免模板字符串转义问题
    document.getElementById('skillMdEditor').value = md.content;
    document.getElementById('skillMdPreview').textContent =
      md.content.split('\n').length + ' 行 · ' + md.content.length + ' 字符';
  }catch(e){log('加载技能详情失败: '+e.message,'warn')}
}

function toggleEditor(){
  const editor=document.getElementById('skillMdEditor');
  const btnEdit=document.getElementById('btnEdit');
  const btnSave=document.getElementById('btnSave');
  const btnCancel=document.getElementById('btnCancel');
  if(editor.readOnly){
    editor.readOnly=false;
    editor.style.border='2px solid #1a73e8';
    editor.style.background='#fff';
    btnEdit.style.display='none';
    btnSave.style.display='inline-block';
    btnCancel.style.display='inline-block';
  }else{
    editor.readOnly=true;
    editor.style.border='1px solid #ddd';
    editor.style.background='#fafafa';
    btnEdit.style.display='inline-block';
    btnSave.style.display='none';
    btnCancel.style.display='none';
  }
}

async function saveSkillMd(){
  const editor=document.getElementById('skillMdEditor');
  const content=editor.value;
  try{
    const res=await fetch(SKILL_API+'/'+selectedSkillId+'/skill-md',{
      method:'PUT',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({content:content})
    });
    const data=await res.json();
    const lines=content.split('\n').length;
    document.getElementById('skillMdPreview').textContent=
      lines+' 行 · '+content.length+' 字符 · ✅ 已保存';
    toggleEditor();
    log('✅ Skill '+selectedSkillId+' 更新成功','success');
  }catch(e){log('❌ 保存失败: '+e.message,'warn')}
}

function log(msg, cls=''){
  const d=document.getElementById('log');
  const l=document.createElement('div');
  l.className='log-line '+cls;
  l.textContent='['+new Date().toLocaleTimeString()+'] '+msg;
  d.appendChild(l);
  d.scrollTop=d.scrollHeight;
  document.getElementById('logCard').style.display='block';
}

function setStep(n){
  for(let i=1;i<=6;i++){
    const s=document.getElementById('step'+i);
    s.className='flow-step'+(i<n?' done':i===n?' active':'');
  }
}

async function createProject(){
  const name=document.getElementById('projName').value.trim();
  if(!name){alert('请输入项目名称');return}
  const body={
    name:name,
    project_type:document.getElementById('projType').value,
    description:'Demo项目 - AI辅助评审系统演示',
    bid_opening_time:document.getElementById('projTime').value+':00'
  };
  log('创建项目: '+name,'info');
  try{
    const res=await fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(!res.ok){const e=await res.json();throw new Error(e.detail||'创建失败')}
    const data=await res.json();
    projectId=data.id;
    document.getElementById('projectInfo').innerHTML=
      '<div class="info-item"><div class="label">项目ID</div><div class="value" style="font-size:12px">'+data.id+'</div></div>'+
      '<div class="info-item"><div class="label">项目名称</div><div class="value">'+data.name+'</div></div>'+
      '<div class="info-item"><div class="label">类型</div><div class="value">'+data.project_type+'</div></div>'+
      '<div class="info-item"><div class="label">状态</div><div class="value"><span class="tag tag-info">'+data.status+'</span></div></div>'+
      '<div class="info-item"><div class="label">主智能体</div><div class="value" style="font-size:12px">'+data.main_review_agent_id+'</div></div>'+
      '<div class="info-item"><div class="label">验真智能体</div><div class="value" style="font-size:12px">'+data.auth_agent_id+'</div></div>'+
      '<div class="info-item"><div class="label">合规审核智能体</div><div class="value" style="font-size:12px">'+data.compliance_agent_id+'</div></div>'+
      '<div class="info-item"><div class="label">数据稽核智能体</div><div class="value" style="font-size:12px">'+data.audit_agent_id+'</div></div>';
    document.getElementById('projectCard').style.display='block';
    document.getElementById('card1').style.display='none';
    document.getElementById('card2').style.display='block';
    setStep(2);
    log('项目创建成功! ID='+data.id+', 状态='+data.status,'success');
  }catch(err){log('❌ '+err.message,'warn')}
}

async function extractRules(){
  log('开始规则提取...','info');
  try{
    const res=await fetch(API+'/'+projectId+'/rule-extraction-jobs',{method:'POST'});
    const data=await res.json();
    log('规则提取任务已创建: '+data.job_id,'info');
    // 等待完成
    let done=false;
    for(let i=0;i<15;i++){
      await new Promise(r=>setTimeout(r,500));
      const r2=await fetch(API+'/'+projectId+'/rule-extraction-jobs/'+data.job_id);
      const d2=await r2.json();
      if(d2.status==='succeeded'){done=true;break}
      if(d2.status==='failed'){throw new Error(d2.error_message||'规则提取失败')}
    }
    if(!done)throw new Error('规则提取超时');
    log('规则提取完成!','success');
    // 显示规则
    const rr=await fetch(API+'/'+projectId+'/review-rules');
    const rulesData=await rr.json();
    let html='<table class="table"><tr><th>ID</th><th>类别</th><th>评审项</th><th>要求</th></tr>';
    rulesData.rules.forEach(r=>{
      html+='<tr><td>'+r.id+'</td><td><span class="tag tag-info">'+r.category+'</span></td><td>'+r.item_name+'</td><td style="font-size:12px">'+r.requirement+'</td></tr>';
    });
    html+='</table>';
    document.getElementById('rulesResult').innerHTML=html;
    document.getElementById('card2').style.display='none';
    document.getElementById('card3').style.display='block';
    setStep(3);
  }catch(err){log('❌ '+err.message,'warn')}
}

async function registerSupplier(){
  const name=document.getElementById('supplierName').value.trim();
  const file=document.getElementById('supplierFile').files[0];
  if(!name){alert('请输入供应商名称');return}
  if(!file){alert('请选择投标文件包');return}
  log('登记供应商: '+name,'info');
  try{
    const fd=new FormData();
    fd.append('supplier_name',name);
    fd.append('package_file',file);
    const res=await fetch(API+'/'+projectId+'/suppliers',{method:'POST',body:fd});
    if(!res.ok){const e=await res.json();throw new Error(e.detail||'登记失败')}
    const data=await res.json();
    supplierId=data.id;
    log('供应商登记成功: '+data.id+' (状态: '+data.status+')','success');
    document.getElementById('supplierResult').innerHTML=
      '<div class="info-grid">'+
      '<div class="info-item"><div class="label">供应商ID</div><div class="value" style="font-size:12px">'+data.id+'</div></div>'+
      '<div class="info-item"><div class="label">名称</div><div class="value">'+data.supplier_name+'</div></div>'+
      '<div class="info-item"><div class="label">状态</div><div class="value"><span class="tag tag-pass">'+data.status+'</span></div></div>'+
      '<div class="info-item"><div class="label">解压目录</div><div class="value" style="font-size:11px">'+data.extract_dir+'</div></div>'+
      '</div>';
    document.getElementById('card3').style.display='none';
    document.getElementById('card4').style.display='block';
    setStep(4);
  }catch(err){log('❌ '+err.message,'warn')}
}

async function registerSupplierMock(){
  const name=document.getElementById('supplierName').value.trim()||'星辰科技有限公司';
  log('快速登记供应商(模拟): '+name,'info');
  try{
    const fd=new FormData();
    fd.append('supplier_name',name);
    // 不传文件，后端会创建mock文件
    const res=await fetch(API+'/'+projectId+'/suppliers?mock=true',{method:'POST',body:fd});
    if(!res.ok){const e=await res.json();throw new Error(e.detail||'登记失败')}
    const data=await res.json();
    supplierId=data.id;
    log('供应商登记成功(Mock): '+data.id,'success');
    document.getElementById('supplierResult').innerHTML=
      '<div class="info-grid">'+
      '<div class="info-item"><div class="label">供应商ID</div><div class="value" style="font-size:12px">'+data.id+'</div></div>'+
      '<div class="info-item"><div class="label">名称</div><div class="value">'+data.supplier_name+'</div></div>'+
      '<div class="info-item"><div class="label">状态</div><div class="value"><span class="tag tag-pass">'+data.status+'</span></div></div>'+
      '<div class="info-item"><div class="label">文件清单</div><div class="value" style="font-size:11px">6个文件(模拟)</div></div>'+
      '</div>';
    document.getElementById('card3').style.display='none';
    document.getElementById('card4').style.display='block';
    setStep(4);
  }catch(err){log('❌ '+err.message,'warn')}
}

async function startReview(){
  const btn=document.getElementById('btnReview');
  btn.disabled=true;
  btn.textContent='⏳ 评审进行中...';
  log('🚀 启动AI评审 — 主智能体并行调度三个子智能体...','info');
  document.getElementById('reviewProgress').innerHTML=
    '<div style="padding:12px"><div class="progress-bar"><div class="fill" id="progFill" style="width:0"></div></div>'+
    '<div id="progText" style="margin-top:8px;font-size:13px;color:#666">初始化...</div></div>';

  try{
    const res=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/review-jobs',{method:'POST'});
    const data=await res.json();
    log('评审任务已创建: '+data.job_id,'info');

    // 模拟进度
    const steps=[
      {pct:10,txt:'🕵️ 验真智能体: 核查营业执照、资质证书...'},
      {pct:25,txt:'🕵️ 验真智能体: 工商系统比对主体一致性...'},
      {pct:40,txt:'📋 合规审核智能体: 检查资格条件、否决项...'},
      {pct:55,txt:'📋 合规审核智能体: 核查投标函、授权书签署...'},
      {pct:70,txt:'📊 数据稽核智能体: 核对报价金额一致性...'},
      {pct:85,txt:'📊 数据稽核智能体: 验算分项合计与总价...'},
      {pct:95,txt:'🤖 主智能体: 聚合三子结果, 生成评审结论...'},
    ];
    for(const s of steps){
      await new Promise(r=>setTimeout(r,600));
      document.getElementById('progFill').style.width=s.pct+'%';
      document.getElementById('progText').textContent=s.txt;
    }

    // 等待任务完成
    let done=false;
    for(let i=0;i<30;i++){
      await new Promise(r=>setTimeout(r,500));
      const r2=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/review-jobs/'+data.job_id);
      const d2=await r2.json();
      if(d2.status==='succeeded'){done=true;break}
    }
    if(!done)throw new Error('评审超时');

    document.getElementById('progFill').style.width='100%';
    document.getElementById('progText').textContent='✅ 评审完成!';
    log('🤖 三子智能体并行评审完成!','success');
    document.getElementById('card4').style.display='none';
    document.getElementById('card5').style.display='block';
    setStep(5);
    await loadReviewResults();
  }catch(err){
    log('❌ '+err.message,'warn');
    btn.disabled=false;
    btn.textContent='🚀 启动AI评审';
  }
}

async function loadReviewResults(){
  try{
    // summary
    const s=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/review-summary');
    const sum=await s.json();
    document.getElementById('reviewSummary').innerHTML=
      '<div class="info-grid">'+
      '<div class="info-item"><div class="label">供应商</div><div class="value">'+sum.supplier_name+'</div></div>'+
      '<div class="info-item"><div class="label">最终结论</div><div class="value"><span class="tag tag-pass" style="font-size:14px">'+sum.final_conclusion+'</span></div></div>'+
      '<div class="info-item"><div class="label">评审时间</div><div class="value" style="font-size:13px">'+sum.review_time+'</div></div>'+
      '<div class="info-item"><div class="label">评审项数</div><div class="value">'+sum.item_count+' 项</div></div>'+
      '<div class="info-item"><div class="label">置信度</div><div class="value"><span class="tag tag-info">'+sum.confidence+'</span></div></div>'+
      '</div>';

    // details
    const d=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/review-details');
    const det=await d.json();
    let html='<h4 style="margin-bottom:8px">📊 评审明细</h4><table class="table"><tr><th>ID</th><th>类别</th><th>评审项</th><th>验真</th><th>合规</th><th>稽核</th><th>结论</th></tr>';
    det.review_items.forEach(r=>{
      html+='<tr><td>'+r.item_id+'</td><td><span class="tag tag-info">'+r.category+'</span></td><td>'+r.item_name+'</td>'+
        '<td><span class="tag '+(r.verification==='通过'?'tag-pass':'tag-warn')+'">'+(r.verification||'-')+'</span></td>'+
        '<td><span class="tag '+(r.compliance==='通过'?'tag-pass':'tag-warn')+'">'+(r.compliance||'-')+'</span></td>'+
        '<td><span class="tag '+(r.audit==='通过'?'tag-pass':'tag-info')+'">'+(r.audit||'-')+'</span></td>'+
        '<td><span class="tag tag-pass">'+r.conclusion+'</span></td></tr>';
    });
    html+='</table>';

    // 子智能体摘要
    html+='<h4 style="margin:16px 0 8px">🤖 子智能体执行摘要</h4>';
    const subs=det.sub_agent_results||{};
    for(const [k,v] of Object.entries(subs)){
      const names={verification_result:'🕵️ 验真智能体',compliance_result:'📋 合规审核智能体',audit_result:'📊 数据稽核智能体'};
      if(v && typeof v==='object'){
        html+='<div style="background:#f8f9fa;padding:12px;border-radius:8px;margin-bottom:8px">'+
          '<b>'+(names[k]||k)+'</b>: <span class="tag tag-pass">'+v.conclusion+'</span><br>'+
          '<span style="font-size:13px;color:#666">'+v.summary+'</span></div>';
      }
    }
    document.getElementById('reviewDetails').innerHTML=html;
    document.getElementById('card6').style.display='block';
    setStep(6);
  }catch(err){log('❌ '+err.message,'warn')}
}

async function generateReport(){
  log('📄 生成评审报告...','info');
  try{
    const res=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/report-jobs',{method:'POST'});
    const data=await res.json();
    await new Promise(r=>setTimeout(r,2000));
    const r2=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/report-jobs/'+data.job_id);
    const d2=await r2.json();
    if(d2.status!=='succeeded')throw new Error('报告生成失败');
    const r3=await fetch(API+'/'+projectId+'/suppliers/'+supplierId+'/report-result');
    const report=await r3.json();
    document.getElementById('reportResult').innerHTML=
      '<div class="info-grid">'+
      '<div class="info-item"><div class="label">报告标题</div><div class="value" style="font-size:13px">'+report.report_title+'</div></div>'+
      '<div class="info-item"><div class="label">供应商</div><div class="value">'+report.supplier_name+'</div></div>'+
      '<div class="info-item"><div class="label">最终结论</div><div class="value"><span class="tag tag-pass" style="font-size:14px">'+report.final_conclusion+'</span></div></div>'+
      '<div class="info-item"><div class="label">评审项</div><div class="value">总计'+report.summary.total_items+'项 / 通过'+report.summary.passed+'项</div></div>'+
      '<div class="info-item"><div class="label">问题数</div><div class="value">'+report.summary.issues+'</div></div>'+
      '<div class="info-item"><div class="label">生成时间</div><div class="value" style="font-size:12px">'+report.generated_at+'</div></div>'+
      '</div>';
    log('✅ 报告生成完成!','success');
    setStep(6);
  }catch(err){log('❌ '+err.message,'warn')}
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=WEB_UI_HTML)


# ══════════════════════════════════════════════
# API 路由
# ══════════════════════════════════════════════

PREFIX = "/api/agents/{agent_id}/bid-projects"


# ── 创建项目 ──

@app.post(PREFIX, status_code=201)
async def create_project(agent_id: str, req: CreateProjectRequest):
    pid = str(uuid.uuid4())[:12]
    proj = {
        "id": pid,
        "name": req.name,
        "project_type": req.project_type,
        "description": req.description,
        "bid_opening_time": req.bid_opening_time,
        "status": ProjectStatus.DRAFT.value,
        "main_review_agent_id": AGENT_ID,
        "auth_agent_id": AUTH_AGENT_ID,
        "compliance_agent_id": COMPLIANCE_AGENT_ID,
        "audit_agent_id": AUDIT_AGENT_ID,
        "rule_file_path": None,
        "report_file_path": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    projects[pid] = proj
    # 持久化到文件
    pd = project_dir(pid)
    (pd / "project.json").write_text(json.dumps(proj, ensure_ascii=False, indent=2))
    (pd / "suppliers.json").write_text("{}")
    (pd / "jobs.json").write_text("{}")
    return proj


# ── 查询项目 ──

@app.get(PREFIX + "/{project_id}")
async def get_project(agent_id: str, project_id: str):
    if project_id not in projects:
        raise HTTPException(404, "项目不存在")
    return projects[project_id]


# ── 规则提取 ──

@app.post(PREFIX + "/{project_id}/rule-extraction-jobs", status_code=202)
async def create_rule_extraction_job(agent_id: str, project_id: str):
    if project_id not in projects:
        raise HTTPException(404, "项目不存在")

    jid = f"job_rule_{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": jid,
        "project_id": project_id,
        "supplier_id": None,
        "job_type": JobType.RULE_EXTRACTION.value,
        "status": JobStatus.QUEUED.value,
        "agent_id": None,
        "error_message": None,
        "created_at": now_iso(),
    }
    jobs[jid] = job

    # 异步执行
    asyncio.create_task(_run_rule_extraction(project_id, jid))

    return job


async def _run_rule_extraction(project_id: str, job_id: str):
    await asyncio.sleep(1)
    try:
        jobs[job_id]["status"] = JobStatus.RUNNING.value

        # 模拟规则提取
        await asyncio.sleep(1.5)
        rules_data = json.loads(json.dumps(MOCK_RULES_TEMPLATE))

        pd = project_dir(project_id)
        rules_dir = pd / "rules"
        rules_dir.mkdir(exist_ok=True)
        rule_path = rules_dir / "rules.json"
        rule_path.write_text(json.dumps(rules_data, ensure_ascii=False, indent=2))

        rules[project_id] = rules_data
        projects[project_id]["rule_file_path"] = str(rule_path)
        projects[project_id]["status"] = ProjectStatus.RULES_READY.value
        projects[project_id]["updated_at"] = now_iso()

        jobs[job_id]["status"] = JobStatus.SUCCEEDED.value
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED.value
        jobs[job_id]["error_message"] = str(e)


@app.get(PREFIX + "/{project_id}/rule-extraction-jobs/{job_id}")
async def get_rule_job(agent_id: str, project_id: str, job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "任务不存在")
    return jobs[job_id]


@app.get(PREFIX + "/{project_id}/review-rules")
async def get_review_rules(agent_id: str, project_id: str):
    if project_id not in rules:
        raise HTTPException(404, "评审规则尚未生成，请先执行规则提取")
    return rules[project_id]


# ── 登记供应商 ──

@app.post(PREFIX + "/{project_id}/suppliers", status_code=201)
async def register_supplier(
    agent_id: str,
    project_id: str,
    supplier_name: str = "星辰科技有限公司",
    mock: bool = False,
    package_file: Optional[UploadFile] = File(None),
):
    if project_id not in projects:
        raise HTTPException(404, "项目不存在")

    sid = f"supplier_{uuid.uuid4().hex[:8]}"
    supp = {
        "id": sid,
        "project_id": project_id,
        "supplier_name": supplier_name,
        "status": SupplierStatus.CREATED.value,
        "extract_dir": None,
        "file_list_path": None,
        "created_at": now_iso(),
    }
    suppliers[sid] = supp

    # 异步解压
    asyncio.create_task(_extract_supplier_files(project_id, sid, package_file))

    return supp


async def _extract_supplier_files(project_id: str, supplier_id: str, package_file=None):
    await asyncio.sleep(0.5)
    try:
        suppliers[supplier_id]["status"] = SupplierStatus.EXTRACTING_FILES.value

        sd = supplier_dir(project_id, supplier_id)

        # Mock 文件清单
        mock_files = [
            "01-投标函.pdf",
            "02-法定代表人授权委托书.pdf",
            "03-营业执照.pdf",
            "04-资质证书/ISO9001认证.pdf",
            "05-技术方案/系统架构设计.pdf",
            "06-报价清单/分项报价表.xlsx",
        ]

        if package_file:
            content = await package_file.read()
            tmp = sd / "upload.zip"
            tmp.write_bytes(content)
            try:
                with zipfile.ZipFile(tmp) as zf:
                    zf.extractall(sd)
            except Exception:
                # 解压失败，创建mock
                for f in mock_files:
                    fp = sd / f
                    fp.parent.mkdir(parents=True, exist_ok=True)
                    fp.write_text(f"[Mock] {f}\n这是模拟的投标文件内容。")
        else:
            # 无文件上传时创建mock
            for f in mock_files:
                fp = sd / f
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(f"[Mock] {f}\n这是模拟的投标文件内容，用于演示AI辅助评审流程。")

        files_json = [{"path": f, "type": "file", "size": 1024} for f in mock_files]
        fl_path = sd / "files.json"
        fl_path.write_text(json.dumps(files_json, ensure_ascii=False, indent=2))

        suppliers[supplier_id]["extract_dir"] = str(sd)
        suppliers[supplier_id]["file_list_path"] = str(fl_path)
        suppliers[supplier_id]["status"] = SupplierStatus.FILES_READY.value
    except Exception as e:
        suppliers[supplier_id]["status"] = SupplierStatus.CREATED.value


# ── 查询文件清单 ──

@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/files")
async def get_supplier_files(agent_id: str, project_id: str, supplier_id: str):
    if supplier_id not in suppliers:
        raise HTTPException(404, "供应商不存在")
    supp = suppliers[supplier_id]
    if supp["status"] != SupplierStatus.FILES_READY.value:
        raise HTTPException(409, "文件尚未准备完成")
    fl_path = supp.get("file_list_path")
    if not fl_path or not Path(fl_path).exists():
        raise HTTPException(404, "文件清单不存在")
    return json.loads(Path(fl_path).read_text())


# ── 启动评审 ──

@app.post(PREFIX + "/{project_id}/suppliers/{supplier_id}/review-jobs", status_code=202)
async def create_review_job(agent_id: str, project_id: str, supplier_id: str):
    if project_id not in projects:
        raise HTTPException(404, "项目不存在")
    if supplier_id not in suppliers:
        raise HTTPException(404, "供应商不存在")

    proj = projects[project_id]
    supp = suppliers[supplier_id]

    if proj["status"] == ProjectStatus.DRAFT.value:
        raise HTTPException(409, "规则尚未生成，请先执行规则提取")
    if supp["status"] == SupplierStatus.CREATED.value:
        raise HTTPException(409, "供应商文件尚未准备完成")

    jid = f"job_review_{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": jid,
        "project_id": project_id,
        "supplier_id": supplier_id,
        "job_type": JobType.REVIEW.value,
        "status": JobStatus.QUEUED.value,
        "agent_id": AGENT_ID,
        "error_message": None,
        "created_at": now_iso(),
    }
    jobs[jid] = job

    asyncio.create_task(_run_review(project_id, supplier_id, jid))

    return job


async def _run_review(project_id: str, supplier_id: str, job_id: str):
    await asyncio.sleep(1)
    try:
        jobs[job_id]["status"] = JobStatus.RUNNING.value
        suppliers[supplier_id]["status"] = SupplierStatus.REVIEWING.value

        proj = projects[project_id]
        supp = suppliers[supplier_id]
        rules_data = rules.get(project_id, MOCK_RULES_TEMPLATE)

        # 模拟主智能体并行调度三个子智能体
        await asyncio.sleep(1.5)  # 子智能体执行中

        # 生成子结果
        rd = results_dir(project_id, supplier_id)

        verify_path = rd / "verification-result.json"
        compliance_path = rd / "compliance-result.json"
        audit_path = rd / "audit-result.json"

        verify_path.write_text(
            json.dumps(mock_verification_result(supp["supplier_name"]), ensure_ascii=False, indent=2)
        )
        compliance_path.write_text(
            json.dumps(mock_compliance_result(supp["supplier_name"]), ensure_ascii=False, indent=2)
        )
        audit_path.write_text(
            json.dumps(mock_audit_result(supp["supplier_name"]), ensure_ascii=False, indent=2)
        )

        # 聚合主结果
        review = mock_review_result(proj["name"], supp["supplier_name"], rules_data)
        review["sub_agent_results"] = {
            "verification_result_path": str(verify_path),
            "compliance_result_path": str(compliance_path),
            "audit_result_path": str(audit_path),
        }
        review_path = rd / "review-result.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2))

        review_results[f"{project_id}:{supplier_id}"] = review

        suppliers[supplier_id]["status"] = SupplierStatus.REVIEWED.value
        projects[project_id]["status"] = ProjectStatus.REVIEW_COMPLETED.value
        projects[project_id]["updated_at"] = now_iso()
        jobs[job_id]["status"] = JobStatus.SUCCEEDED.value
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED.value
        jobs[job_id]["error_message"] = str(e)
        suppliers[supplier_id]["status"] = SupplierStatus.FILES_READY.value


@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/review-jobs/{job_id}")
async def get_review_job(agent_id: str, project_id: str, supplier_id: str, job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "任务不存在")
    return jobs[job_id]


# ── 评审总览 ──

@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/review-summary")
async def get_review_summary(agent_id: str, project_id: str, supplier_id: str):
    key = f"{project_id}:{supplier_id}"
    if key not in review_results:
        raise HTTPException(404, "评审结果不存在")
    r = review_results[key]
    return {
        "project_name": r["project_name"],
        "supplier_name": r["supplier_name"],
        "final_conclusion": r["final_conclusion"],
        "review_time": r["review_time"],
        "item_count": len(r.get("review_items", [])),
        "confidence": r.get("confidence", "medium"),
    }


# ── 评审详情 ──

@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/review-details")
async def get_review_details(agent_id: str, project_id: str, supplier_id: str):
    key = f"{project_id}:{supplier_id}"
    if key not in review_results:
        raise HTTPException(404, "评审结果不存在")
    return review_results[key]


# ── 原始评审结果 ──

@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/review-result")
async def get_review_result_raw(agent_id: str, project_id: str, supplier_id: str):
    key = f"{project_id}:{supplier_id}"
    if key not in review_results:
        raise HTTPException(404, "评审结果不存在")
    return review_results[key]


# ── 生成报告 ──

@app.post(PREFIX + "/{project_id}/suppliers/{supplier_id}/report-jobs", status_code=202)
async def create_report_job(agent_id: str, project_id: str, supplier_id: str):
    key = f"{project_id}:{supplier_id}"
    if key not in review_results:
        raise HTTPException(409, "评审结果尚未生成，请先完成评审")

    jid = f"job_report_{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": jid,
        "project_id": project_id,
        "supplier_id": supplier_id,
        "job_type": JobType.REPORT.value,
        "status": JobStatus.QUEUED.value,
        "agent_id": AGENT_ID,
        "error_message": None,
        "created_at": now_iso(),
    }
    jobs[jid] = job

    asyncio.create_task(_run_report(project_id, supplier_id, jid))
    return job


async def _run_report(project_id: str, supplier_id: str, job_id: str):
    await asyncio.sleep(0.5)
    try:
        jobs[job_id]["status"] = JobStatus.RUNNING.value
        await asyncio.sleep(1.5)

        proj = projects[project_id]
        supp = suppliers[supplier_id]
        review = review_results.get(f"{project_id}:{supplier_id}", {})

        report = mock_report_result(proj["name"], supp["supplier_name"], review)

        rd = results_dir(project_id, supplier_id)
        report_path = rd / "report-result.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

        report_results[f"{project_id}:{supplier_id}"] = report

        suppliers[supplier_id]["status"] = SupplierStatus.REPORT_READY.value
        projects[project_id]["status"] = ProjectStatus.REPORT_GENERATED.value
        jobs[job_id]["status"] = JobStatus.SUCCEEDED.value
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED.value
        jobs[job_id]["error_message"] = str(e)


@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/report-jobs/{job_id}")
async def get_report_job(agent_id: str, project_id: str, supplier_id: str, job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "任务不存在")
    return jobs[job_id]


@app.get(PREFIX + "/{project_id}/suppliers/{supplier_id}/report-result")
async def get_report_result(agent_id: str, project_id: str, supplier_id: str):
    key = f"{project_id}:{supplier_id}"
    if key not in report_results:
        raise HTTPException(404, "报告尚未生成")
    return report_results[key]


# ══════════════════════════════════════════════
# Skill 管理 API
# ══════════════════════════════════════════════

SKILL_API = "/api/skills"


@app.get(SKILL_API)
async def list_skills():
    """列出所有已注册的 Skill"""
    return [
        {
            "id": sid,
            "name": meta["name"],
            "version": meta["version"],
            "description": meta["description"],
            "agent_role": meta["agent_role"],
            "capability_count": len(meta.get("capabilities", []))
        }
        for sid, meta in {k: get_skill_meta(k) for k in SKILL_DEFINITIONS}.items()
        if meta
    ]


@app.get(SKILL_API + "/{skill_id}")
async def get_skill_meta_endpoint(skill_id: str):
    """获取 Skill 元数据"""
    meta = get_skill_meta(skill_id)
    if not meta:
        raise HTTPException(404, f"Skill '{skill_id}' 不存在")
    return meta


@app.get(SKILL_API + "/{skill_id}/skill-md")
async def get_skill_md_endpoint(skill_id: str):
    """获取 Skill 的 SKILL.md 内容"""
    content = get_skill_md(skill_id)
    if not content:
        raise HTTPException(404, f"Skill '{skill_id}' 不存在")
    return {"skill_id": skill_id, "content": content}


@app.put(SKILL_API + "/{skill_id}/skill-md")
async def update_skill_md(skill_id: str, body: dict):
    """更新 Skill 的 SKILL.md 内容（Demo中仅更新内存）"""
    if skill_id not in SKILL_DEFINITIONS:
        raise HTTPException(404, f"Skill '{skill_id}' 不存在")
    new_content = body.get("content", "")
    SKILL_DEFINITIONS[skill_id]["skill_md"] = new_content
    # 同时写入磁盘
    skill_dir = SKILLS_DIR / skill_id
    (skill_dir / "SKILL.md").write_text(new_content, encoding="utf-8")
    return {"skill_id": skill_id, "status": "updated", "size": len(new_content)}


# ──────────────────────────────────────────────
# 启动入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  🤖 AI辅助评审系统 Demo")
    print("  主智能体 + 验真/合规审核/数据稽核 三子智能体")
    print("=" * 60)
    print(f"  Web UI:  http://localhost:8000")
    print(f"  API文档: http://localhost:8000/docs")
    print(f"  数据目录: {WORKSPACE_DIR.absolute()}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
