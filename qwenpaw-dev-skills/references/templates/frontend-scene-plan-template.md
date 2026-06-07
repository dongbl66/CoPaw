# <场景名称>前端实现计划模板

## 1. 目标

- 

## 2. 文件落点

```text
console/src/business/<scene>/
  manifest.ts
  pages/
    Results/
    ResultDetail/
  workbench/
    <Scene>WorkbenchPage.tsx

console/src/pages/Chat/result-panel/<Scene>Report.tsx
console/src/api/modules/<scene>Result.ts
console/src/api/types/<scene>.ts
```

## 3. ResultPanel

分流条件：

```ts
result.result.type === "business" &&
payload.scene === "<scene>_report"
```

展示区块：

- 基础信息
- 分析详情
- 重复条目
- 评分 / 风险 / 建议

## 4. Business 页面

菜单：

```text
<业务名称>
- 结果列表
- 结果详情
- ResultWorkbench 业务页
```

要求：
- `manifest.ts` 注册 routes、menus、`resultWorkbench`
- Workbench 页负责 latest、direct JSON 显示、保存、详情跳转
- 保存成功后派发 `<scene>:results-updated`
- 列表页监听 `<scene>:results-updated` 并刷新

## 5. API Module

```ts
export const <scene>ResultApi = {
  listResults,
  getLatestResult,
  getResult,
  saveResult,
};
```

## 6. 测试

- renderer 测试
- ResultWorkbench 业务页测试
- direct JSON 自动显示测试
- 保存前 latest 回查测试
- 保存后列表刷新测试
- 列表页测试
- 详情页测试
- API module 测试
