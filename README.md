# HMI 工具箱 — 完整工具包

专为 **Qt / HMI** 嵌入式 HMI 工程师打造的 5 款效率工具。

## 工具清单

| # | 工具 | 定价 | 形态 | 说明 |
|---|------|------|------|------|
| 01 | 📊 PLC 变量自动映射表 | ¥99 | Python 脚本 | PLC变量→Qt/Qt标签映射 |
| 02 | 🔢 Modbus 地址批量计算器 | ¥69 | 网页工具 (HTML) | 地址计算+导出 |
| 03 | 🔄 配方数据 Excel ↔ HMI 互转 | ¥129 | Python 脚本 | Excel/HMI双向转换 |
| 04 | 🏷️ 标签批量导入/导出工具 | ¥149 | Python 脚本 | 提取+归类+差分对比 |
| 05 | 📋 IO 点表自动生成报告 | ¥79 | Python 脚本 | 自动分类+统计+交付文档 |
| 🧰 | **全套工具包（省 40%）** | **¥299** | 全部打包 | 终身更新+优先支持 |

## 系统要求

- **Python 3.6+**（工具 01/03/04/05 需要）
- **现代浏览器**（工具 02 需要，Chrome/Edge/Firefox）
- Windows / macOS / Linux

## 快速开始

```bash
# 1. PLC 变量自动映射（使用示例数据）
cd "01-PLC变量映射表"
python plc_to_hmi_mapper.py -i ../examples/siemens_export.csv -o ./output/

# 2. Modbus 地址计算器（网页版，双击打开）
# 直接双击打开 02-Modbus地址计算器/modbus_calculator.html

# 3. 配方数据互转（生成示例）
cd "03-配方数据互转"
python recipe_converter.py -m example -o ./output/

# 4. 标签工具（生成示例）
cd "04-标签导入导出"
python tag_manager.py --generate-example -o ./output/

# 5. IO 点表报告（生成示例）
cd "05-IO点表报告"
python io_report_generator.py --example -o ./output/
```

---

*HMI Toolbox — https://tianyuwa.github.io/hmi-tools/*
