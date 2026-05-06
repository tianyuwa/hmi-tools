# PLC 变量自动映射表 v2.0

## 概述

将 PLC 变量的导出文件自动映射为 HMI 工程可用的标签格式。
自动检测 PLC 品牌（Siemens/TIA / Mitsubishi GX Works / Omron CX-P），
输出 Qt QML 绑定、C++ 头文件、CSV 映射表。

## 功能

- 自动读取主流 PLC 变量导出文件（CSV 格式）
- 自动检测 PLC 品牌 + 地址归一化
- 智能数据类型映射（BOOL bool, INT int16, REAL float...）
- 自动变量去重 + 分组归类
- 输出 3 种格式：

  | 格式 | 用途 | 文件 |
  |------|------|------|
  | Qt QML | Qt Quick 属性绑定 | `hmi_mapping_qt.qml` |
  | CSV 映射表 | 归档/文档/审查 | `hmi_mapping_table.csv` |
  | C++ Header | Qt C++ 后端变量声明 | `plc_hmi_mapping.h` |

## 使用方法

```bash
python plc_to_hmi_mapper.py -i export.csv -o ./output/  # 全部格式
python plc_to_hmi_mapper.py -i export.csv -o ./output/ -f qml  # 仅 QML
python plc_to_hmi_mapper.py -i export.csv -o ./output/ -f csv  # 仅 CSV
```

## 支持的 PLC

- Siemens TIA Portal (STEP 7)
- Mitsubishi GX Works2 / GX Works3
- Omron CX-Programmer
- 通用 CSV（自动检测字段名）

## 输出示例

### Qt QML

```qml
Item {
    property bool Motor_Start: 0   // 电机启动信号
    property bool Motor_Stop: 0    // 电机停止信号
    property int Motor_Speed: 0    // 电机当前转速
}
```

### C++ Header

```c
extern bool PLC_Motor_Start;      // 电机启动
extern float PLC_Motor_Temp;      // 电机温度
extern int16_t PLC_Motor_Speed;   // 转速
```

## 文件清单

```
01-PLC变量映射表/
├── plc_to_hmi_mapper.py    # 主程序
├── README.md               # 使用说明
└── output/                 # 输出目录（运行后生成）
    ├── hmi_mapping_qt.qml
    ├── hmi_mapping_table.csv
    └── plc_hmi_mapping.h
```

## 系统要求

- Python 3.6+
- Windows / macOS / Linux
- 无需额外依赖（仅标准库）
