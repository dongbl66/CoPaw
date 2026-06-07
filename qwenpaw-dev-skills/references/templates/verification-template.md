# <场景名称>验证计划模板

## 1. 后端验证

- [ ] parser 单测
- [ ] hook 单测
- [ ] persistence 单测
- [ ] router 单测
- [ ] manifest loading 测试
- [ ] hook registry 幂等性测试

## 2. 前端验证

- [ ] ResultPanel renderer 测试
- [ ] ResultWorkbench 业务页测试
- [ ] direct JSON 自动显示
- [ ] 刷新只请求当前 `biz_module`
- [ ] 保存前可回查 latest
- [ ] 保存后派发 `<scene>:results-updated`
- [ ] business 列表页测试
- [ ] 详情页测试
- [ ] API module 测试
- [ ] mock structured_result 渲染测试

## 3. Skill / Agent 验证

- [ ] 过程辅助型 Skill 不输出 structured_result
- [ ] 报告输出型 Skill 输出标准 structured_result
- [ ] Agent 绑定 parser
- [ ] parser 注入 metadata
- [ ] ResultPanel 自动打开
- [ ] hook 持久化

## 4. Smoke Test

```text
输入业务材料
-> Skill / Agent
-> structured_result
-> ResultWorkbench
-> ResultPanel
-> save
-> persistence
-> business list/detail
```
