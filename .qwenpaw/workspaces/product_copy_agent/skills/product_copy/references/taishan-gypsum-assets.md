# 泰山石膏本地素材映射

## 用法

当任务涉及“泰山石膏 + 客户拜访/走访/PPT/演示稿/汇报”时：

1. 优先从 `assets/taishan-gypsum/` 读取本地图片，而不是临时联网找图。
2. 生成 HTML 时优先引用英文别名文件，并使用相对路径。
3. 保留中文原图作为原始资产，默认不要在模板中直接引用中文文件名。
4. 若输出目录不在技能目录内，则将所需图片复制到输出目录旁边，再用相对路径引用。

## 命名原则

- `assets/taishan-gypsum/` 里同时保留中文原图与英文别名。
- 新生成的 HTML、模板、脚本、素材映射，一律优先使用英文别名。
- 这样可以降低跨机器、跨系统编码、压缩包解压后乱码等风险。

## 中文文件名与英文别名对照

### 企业与品牌
- `公司简介.png` -> `company-profile.png`
- `荣誉资质.png` -> `honors-and-qualifications.png`

### 产品体系
- `纸面石膏板.png` -> `paper-faced-gypsum-board.png`
- `布面石膏板.png` -> `fabric-faced-gypsum-board.png`
- `石膏基阻燃板.png` -> `gypsum-based-fire-board.png`
- `分解甲醛石膏板.png` -> `formaldehyde-reducing-gypsum-board.png`
- `轻钢龙骨.png` -> `light-steel-keel.png`
- `抹灰石膏.png` -> `plaster-gypsum.png`
- `石膏纤维板.png` -> `gypsum-fiber-board.png`
- `植物纤维板.png` -> `plant-fiber-board.png`
- `生肖系列石膏板.png` -> `zodiac-series-gypsum-board.png`

### 辅材与配套
- `嵌缝粉.png` -> `joint-compound-powder.png`
- `界面胶.png` -> `interface-adhesive.png`
- `背涂胶.png` -> `back-coating-adhesive.png`
- `瓷砖胶.png` -> `tile-adhesive.png`
- `内墙腻子粉.png` -> `interior-wall-putty.png`
- `平砂浆.png` -> `leveling-mortar.png`
- `金砖龙骨.png` -> `gold-brick-keel.png`
- `烤漆龙骨.png` -> `painted-keel.png`

### 案例
- `大兴国际机场案例.png` -> `case-daxing-airport.png`
- `冬奥馆案例.png` -> `case-winter-olympics-venue.png`
- `雄安站案例.png` -> `case-xiongan-station.png`

## 推荐取图规则

### 企业与品牌页
- 优先：`company-profile.png`
- 荣誉页优先：`honors-and-qualifications.png`

### 产品体系页
- 常规板材：`paper-faced-gypsum-board.png`
- 防火安全：`gypsum-based-fire-board.png`
- 环保健康：`formaldehyde-reducing-gypsum-board.png`
- 系统配套：`light-steel-keel.png`
- 粉料施工：`plaster-gypsum.png`

### 案例页
- 交通枢纽：`case-daxing-airport.png`
- 重大赛事 / 公共建筑：`case-winter-olympics-venue.png`
- 国家重点工程：`case-xiongan-station.png`

## 现成模板

- `assets/taishan-gypsum/taishan-gypsum-client-visit.html`
  - 技能内可分发版本
  - 图片与 HTML 同目录
  - 使用相对路径
  - 后续如需改图，优先替换为英文别名文件
