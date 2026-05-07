# 🛠️ HMI 工具箱 — 嵌入式 HMI 工程师效率工具

> 专为 **Qt/QML · 嵌入式 HMI · 工业自动化** 工程师打造的 5 款生产力工具。
>
> 告别重复劳动，把时间留给真正的设计。

---

## 📦 工具清单

| # | 工具 | 定价 | 形态 |
|---|------|------|------|
| 01 | 🔧 PLC 变量自动映射表 | ¥99 | Python 脚本 |
| 02 | 📐 Modbus 地址批量计算器 | ¥69 | 网页工具 (HTML) |
| 03 | 🔄 配方数据 Excel ↔ HMI 互转 | ¥129 | Python 脚本 |
| 04 | 🏷️ 标签批量导入/导出工具 | ¥149 | Python 脚本 |
| 05 | 📊 IO 点表自动生成报告 | ¥79 | Python 脚本 |
| 🎯 | **全套工具包（省 40%）** | **¥299** | **全部打包** |

**购买全套 → 终身更新 + 优先技术支持 + 免费新工具**

---

## 🔍 功能详解

### 01 — PLC 变量自动映射表
读取 PLC 导出的变量表（西门子/三菱/欧姆龙），自动生成：
- **HMI 标签文件**（QML、C Header）
- **映射对照表**（CSV/PDF）
- **差分对比报告**（版本迭代时快速定位变更）

### 02 — Modbus 地址批量计算器
- 批处理位地址 → 字地址 → 偏移量
- 支持 01/02/03/04 功能码
- 一键导出 Excel/CSV
- **纯网页工具，无需安装，双击即用**

### 03 — 配方数据 Excel ↔ HMI 互转
- Excel 配方表 → C++ 结构体 / QML 模型
- 支持配方参数批量校验
- 解决「电气写 Excel → 嵌入式写代码」的协作鸿沟

### 04 — 标签批量导入/导出工具
- 从已有项目批量提取标签定义
- 按 PLC 品牌归类（西门子/三菱/欧姆龙）
- **差分对比**：两个版本间增删改一目了然
- 导出 QML / C Header / 报告

### 05 — IO 点表自动生成报告
- 输入原始 IO 清单 → 自动分类（DI/DO/AI/AO/Internal）
- 生成结构化报告：Word / Markdown / PDF / CSV
- 统计数量、地址区间、预留情况

---

## 💻 系统要求

| 工具 | 环境 |
|------|------|
| 01 / 03 / 04 / 05 | Python 3.6+（Windows / macOS / Linux） |
| 02 | 任意现代浏览器（Chrome / Edge / Firefox） |

---

## 🚀 快速开始

```bash
# 01 — PLC 变量映射
cd "01-PLC变量映射表"
python plc_to_hmi_mapper.py -i ../examples/siemens_export.csv -o ./output/

# 02 — Modbus 计算器（双击打开网页）
# 双击 02-Modbus地址计算器/modbus_calculator.html

# 03 — 配方互转
cd "03-配方数据互转"
python recipe_converter.py -m example -o ./output/

# 04 — 标签工具
cd "04-标签导入导出"
python tag_manager.py --generate-example -o ./output/

# 05 — IO 点表报告
cd "05-IO点表报告"
python io_report_generator.py --example -o ./output/
```

---

## 📸 预览

> _(截图正在路上 — 可在 GitHub Pages 在线预览)_

🔗 **在线演示：** [https://tianyuwa.github.io/hmi-tools/](https://tianyuwa.github.io/hmi-tools/)

---

## 👨‍💻 关于作者

从事嵌入式 HMI 开发多年，日常与 Qt/QML、PLC 打交道。
这些工具来自实际项目中的痛点，自己用顺手了，分享给同行。

**购买 & 咨询：** 面包多搜索「HMI 工具箱」或联系作者。

---

## 📄 许可

个人/商业使用均需购买授权。详情请联系作者。

---

*HMI Toolbox — 为每一位 HMI 工程师节省时间*
