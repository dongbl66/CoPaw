# 输出文件管理规范

## 目录结构

```
output/
├── html/           # HTML 格式文案输出
├── md/             # Markdown 格式文案输出
└── resources/      # 文案相关资源（图片、附件等）
```

## 文件命名规范

### 命名格式
```
[产品英文名]-[文案类型]-[日期].[扩展名]
```

### 示例
- `paper-faced-gypsum-board-product-page-20260323.html`
- `formaldehyde-reducing-gypsum-board-social-post-20260323.md`
- `light-steel-keel-comparison-20260323.html`

### 文案类型标识
| 类型 | 标识 | 说明 |
|-----|------|-----|
| 产品详情页 | product-page | 完整产品介绍 |
| 社媒推广 | social-post | 朋友圈/小红书等 |
| 对比文案 | comparison | 产品对比表 |
| 案例展示 | case-study | 案例包装文案 |
| 企业介绍 | company-intro | 企业/品牌介绍 |
| 活动促销 | promotion | 促销/活动文案 |

## 输出指南

### 1. HTML 输出

**适用场景：**
- 产品详情页
- 需要精美排版的文案
- 可直接分发的宣传页

**模板位置：**
参考 `assets/taishan-gypsum/taishan-gypsum-client-visit.html`

**输出要求：**
- 图片使用相对路径引用
- 如需使用素材图片，复制到 `output/resources/` 目录
- 图片引用路径：`resources/[图片文件名]`

**HTML 示例结构：**
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>产品名称 - 泰山石膏</title>
    <style>
        /* 内联样式，确保独立可分发 */
    </style>
</head>
<body>
    <img src="resources/paper-faced-gypsum-board.png" alt="产品图" />
    <!-- 文案内容 -->
</body>
</html>
```

### 2. Markdown 输出

**适用场景：**
- 快速文案输出
- 需要二次编辑的文案
- 内部文档/笔记

**输出要求：**
- 图片使用相对路径引用
- 如需使用素材图片，复制到 `output/resources/` 目录
- 图片引用路径：`![描述](resources/[图片文件名])`

**Markdown 示例结构：**
```markdown
# 产品名称

![产品图](resources/paper-faced-gypsum-board.png)

## 核心优势
- 卖点 1
- 卖点 2
- 卖点 3

## 立即咨询
联系方式...
```

### 3. 资源文件管理

**何时复制资源：**
- 文案需要独立分发给他人
- 文案需要打包发送
- 文案需要在不同环境使用

**何时不复制资源：**
- 仅在本地查看
- 使用技能目录内的相对路径（`../../assets/taishan-gypsum/`）

**资源命名：**
- 使用英文别名（与 `references/taishan-gypsum-assets.md` 一致）
- 避免中文文件名

## 输出工作流

```
1. 确定输出格式（HTML / MD）
   ↓
2. 选择文案模板
   ↓
3. 撰写文案内容
   ↓
4. 确定图片使用方式
   ├─ 本地查看 → 使用 ../../assets/taishan-gypsum/ 路径
   └─ 分发输出 → 复制图片到 output/resources/
   ↓
5. 保存文件到对应目录
   ├─ HTML → output/html/
   └─ MD → output/md/
   ↓
6. 命名文件（遵循命名规范）
   ↓
7. 检查文件完整性
```

## 文件版本管理

### 版本标识
如需保留多个版本，在日期后添加版本号：
```
[产品英文名]-[文案类型]-[日期]-v[版本].[扩展名]
```

示例：
- `paper-faced-gypsum-board-product-page-20260323-v1.html`
- `paper-faced-gypsum-board-product-page-20260323-v2.html`

### 清理规则
- 保留最新 3 个版本
- 删除超过 30 天的草稿版本
- 定稿版本添加 `_final` 标识

## 批量输出

当需要为多个产品生成文案时：

1. 为每个产品创建独立文件
2. 可创建 `batch-[日期]/` 子目录组织
3. 使用 Excel/CSV 记录输出清单

示例：
```
output/
├── batch-20260323/
│   ├── paper-faced-gypsum-board-...
│   ├── fabric-faced-gypsum-board-...
│   └── gypsum-based-fire-board-...
└── resources/
```

## 质量检查

输出前确认：
- [ ] 文件名符合命名规范
- [ ] 图片路径正确（相对路径）
- [ ] 资源文件已复制到 resources/（如需分发）
- [ ] 文案内容完整
- [ ] 联系方式准确
- [ ] 无乱码或格式错误

---

**版本**: v1.0
**更新日期**: 2026-03-23
