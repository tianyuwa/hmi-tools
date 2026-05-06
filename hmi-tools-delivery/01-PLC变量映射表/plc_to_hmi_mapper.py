#!/usr/bin/env python3
"""
PLC 变量自动映射表 v2.0
========================
原生解析 Siemens TIA Portal / Mitsubishi GX Works / Omron CX-Programmer
导出文件的变量，自动映射为 Qt QML / C++ / CSV 格式。
支持自动品牌检测、地址归一化、批量偏移、智能分组。

用法:
    python plc_to_hmi_mapper.py -i <输入文件.csv> -o <输出目录>
    python plc_to_hmi_mapper.py -i export.csv -f qml          # 仅 QML
    python plc_to_hmi_mapper.py -i export.csv --offset 100     # 地址偏移
    python plc_to_hmi_mapper.py --example                      # 示例

作者: HMI Toolbox
"""

import csv
import json
import os
import sys
import argparse
import re
from datetime import datetime
from collections import defaultdict

# ───────────────────────────────────────────────
#  数据类型映射
# ───────────────────────────────────────────────

PLC_TO_HMI_TYPES = {
    'BOOL':       {'qml': 'bool',       'c_type': 'bool'},
    'BYTE':       {'qml': 'int',        'c_type': 'uint8_t'},
    'WORD':       {'qml': 'int',        'c_type': 'uint16_t'},
    'DWORD':      {'qml': 'int',        'c_type': 'uint32_t'},
    'INT':        {'qml': 'int',        'c_type': 'int16_t'},
    'DINT':       {'qml': 'int',        'c_type': 'int32_t'},
    'REAL':       {'qml': 'real',       'c_type': 'float'},
    'SINT':       {'qml': 'int',        'c_type': 'int8_t'},
    'USINT':      {'qml': 'int',        'c_type': 'uint8_t'},
    'UINT':       {'qml': 'int',        'c_type': 'uint16_t'},
    'UDINT':      {'qml': 'int',        'c_type': 'uint32_t'},
    'ULINT':      {'qml': 'int',        'c_type': 'uint64_t'},
    'LREAL':      {'qml': 'double',     'c_type': 'double'},
    'STRING':     {'qml': 'string',     'c_type': 'char*'},
    'WSTRING':    {'qml': 'string',     'c_type': 'wchar_t*'},
    'TIME':       {'qml': 'int',        'c_type': 'uint32_t'},
    'DATE':       {'qml': 'int',        'c_type': 'uint32_t'},
    'BIT':        {'qml': 'bool',       'c_type': 'bool'},
    'BIN16':      {'qml': 'int',        'c_type': 'uint16_t'},
    'BIN32':      {'qml': 'int',        'c_type': 'uint32_t'},
    'FLOAT':      {'qml': 'real',       'c_type': 'float'},
    'DOUBLE':     {'qml': 'double',     'c_type': 'double'},
}

# 地址区域 → 中文分组名
AREA_GROUP = {
    'I': '数字量输入', 'Q': '数字量输出', 'M': '内部存储',
    'DB': '数据块', 'AI': '模拟量输入', 'AQ': '模拟量输出',
    'T': '定时器', 'C': '计数器',
    'X': '输入继电器', 'Y': '输出继电器', 'D': '数据寄存器',
    'CIO': 'I/O通道', 'W': '工作字', 'H': '保持字',
    'A': '辅助继电器',
}

# ───────────────────────────────────────────────
#  品牌检测
# ───────────────────────────────────────────────

def detect_brand(headers, rows):
    """通过表头和地址内容自动检测 PLC 品牌"""
    hu = [h.upper().strip() for h in headers]

    # 列名检测
    if any('LOGICALADDRESS' in h for h in hu):
        return 'siemens'
    if 'ラベル名' in hu or 'デバイス' in hu or 'LABELNAME' in hu or 'DEVICE' in hu:
        return 'mitsubishi'
    if 'PLCNAME' in hu or 'PLC NAME' in hu:
        return 'omron'

    # 地址内容检测
    if rows:
        addr_col = next((i for i, h in enumerate(headers)
                        if h.upper().strip() in ('ADDRESS', 'ADDR', 'LOGICALADDRESS')), None)
        if addr_col is not None:
            samples = []
            for row in rows[:5]:
                if addr_col < len(row):
                    a = row[addr_col].strip().upper()
                    if a: samples.append(a)

            siemens = sum(1 for a in samples if re.match(r'%?[IEQAM]', a))
            mitsu = sum(1 for a in samples if re.match(r'^[XYMDLS]', a))
            omron = sum(1 for a in samples if re.match(r'^(CIO|W|H|A|DM)', a))

            if siemens >= 2: return 'siemens'
            if mitsu >= 2: return 'mitsubishi'
            if omron >= 2: return 'omron'

    return 'generic'


# ───────────────────────────────────────────────
#  地址归一化
# ───────────────────────────────────────────────

def normalize_addr(addr, brand='generic'):
    """归一化 PLC 地址为统一格式"""
    addr = addr.upper().strip()
    if addr.startswith('%'):
        addr = addr[1:]

    if brand == 'siemens':
        for p in [r'^(M|I|Q)(\d+)$', r'^(M|I|Q)(\d+\.\d+)$',
                  r'^(AIW|AQW|AI|AQ)(\d+)$']:
            m = re.match(p, addr)
            if m: return f'%{m.group(1)}{m.group(2)}'
        m = re.match(r'^DB(\d+)\.(DBX|DBB|DBW|DBD)(\d+)', addr)
        if m: return f'%DB{m.group(1)}.{m.group(2)}{m.group(3)}'
        m = re.match(r'^DB(\d+)\.(DBX|DBB|DBW|DBD)(\d+)\.(\d+)', addr)
        if m: return f'%DB{m.group(1)}.{m.group(2)}{m.group(3)}_{m.group(4)}'

    elif brand == 'mitsubishi':
        m = re.match(r'^([XY])(\d+)', addr)
        if m: return f'%{m.group(1)}{m.group(2)}'
        m = re.match(r'^[MLSBF](\\d+)', addr)
        if m: return f'%{m.group(1)}{m.group(2)}'
        m = re.match(r'^D(\d+)', addr)
        if m: return f'%D{m.group(1)}'

    elif brand == 'omron':
        m = re.match(r'^(CIO|W|H|A|D|DM|TIM|CNT)(\d+(?:\.\d+)?)', addr)
        if m: return f'%{m.group(1)}{m.group(2)}'

    return f'%{addr}' if not addr.startswith('%') else f'%{addr}'


def get_address_num(addr):
    """从归一化地址中提取数字部分"""
    m = re.search(r'(\d+)', addr)
    return int(m.group(1)) if m else 0


def get_area(addr):
    """从地址中提取区域前缀"""
    m = re.match(r'%?([A-Z]+)', addr.upper())
    return m.group(1) if m else 'Other'


def group_name(addr):
    """根据地址区域返回分组名"""
    area = get_area(addr)
    return AREA_GROUP.get(area, area)


# ───────────────────────────────────────────────
#  品牌解析器
# ───────────────────────────────────────────────

def parse_csv_rows(rows, brand='generic'):
    """解析 CSV 行为变量列表"""
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    col = {}
    for i, h in enumerate(headers):
        hu = h.upper().strip()
        if hu in ('NAME', 'VARIABLE', 'TAG', 'SYMBOL', 'LABELNAME', '变量名', 'ラベル名'):
            col['name'] = i
        elif hu in ('ADDRESS', 'ADDR', 'LOGICALADDRESS', 'DEVICE', '地址', 'デバイス'):
            col['addr'] = i
        elif hu in ('DATATYPE', 'DATA_TYPE', 'TYPE', '数据类型', 'データ型', '类型'):
            col['type'] = i
        elif hu in ('COMMENT', 'DESCRIPTION', 'DESC', '备注', '注释', 'コメント'):
            col['comment'] = i

    if 'name' not in col or 'addr' not in col:
        return []

    variables = []
    for row in rows[1:]:
        try:
            name = row[col['name']].strip() if col['name'] < len(row) else ''
            addr = row[col['addr']].strip() if col['addr'] < len(row) else ''
            if not name or not addr:
                continue
            dtype = row[col.get('type', 0)].strip().upper() if 'type' in col else 'BOOL'
            comment = row[col.get('comment', 0)].strip() if 'comment' in col else ''
            norm = normalize_addr(addr, brand)
            hmi = PLC_TO_HMI_TYPES.get(dtype, {'qml': 'var', 'c_type': 'auto'})
            variables.append({
                'name': name, 'address': norm, 'plc_type': dtype,
                'hmi_type': hmi, 'comment': comment,
                'group': group_name(norm), 'plc_brand': brand,
            })
        except Exception:
            continue

    return variables


def read_file(file_path):
    """读取 CSV 文件，自动检测编码和分隔符"""
    for enc in ('utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'gbk', 'latin-1'):
        try:
            with open(file_path, 'r', encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            if rows and len(rows) > 1:
                return rows
        except Exception:
            continue
    return None


def apply_offset(variables, offset):
    """对变量地址应用偏移"""
    result = []
    for v in variables:
        addr = v['address']
        m = re.search(r'(\d+)$', addr)
        if m:
            old_num = int(m.group(1))
            new_num = old_num + offset
            new_addr = addr[:m.start(1)] + str(new_num)
            v2 = dict(v)
            v2['address'] = new_addr
            v2['original_address'] = addr
            v2['comment'] = f'{v["comment"]} (offset +{offset})'.strip() if v.get('comment') else f'Offset from {addr}'
            result.append(v2)
        else:
            result.append(v)
    return result


# ───────────────────────────────────────────────
#  输出生成
# ───────────────────────────────────────────────

def to_qml(variables, path):
    """Qt QML 属性绑定"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('import QtQuick 2.15\n\n')
        f.write('// PLC Tag Bindings (auto-generated)\n')
        f.write(f'// Tags: {len(variables)} | Brand: {variables[0]["plc_brand"] if variables else "N/A"}\n')
        f.write(f'// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')
        f.write('QtObject {\n')
        for v in variables:
            c = f'  // {v["comment"]}' if v.get('comment') else ''
            orig = v.get('original_address', '')
            if orig: c += f' [was {orig}]'
            f.write(f'    property {v["hmi_type"]["qml"]} {v["name"]}: 0{c}\n')
        f.write('}\n')
    print(f'  [OK] Qt QML: {path} ({len(variables)} vars)')


def to_c_header(variables, path):
    """C++ 头文件"""
    base = os.path.splitext(os.path.basename(path))[0]
    guard = base.upper().replace('.', '_')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'#ifndef {guard}_H\n#define {guard}_H\n\n')
        f.write('// PLC Tag Definitions\n')
        f.write(f'// Tags: {len(variables)}\n')
        f.write(f'// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')
        f.write('#include <stdint.h>\n\n')
        # Group by C type
        by_type = defaultdict(list)
        for v in variables:
            by_type[v['hmi_type']['c_type']].append(v)
        for ct in ('bool', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t',
                   'uint64_t', 'float', 'double', 'char*', 'wchar_t*', 'auto'):
            if ct not in by_type: continue
            f.write(f'// {ct}\n')
            for v in sorted(by_type[ct], key=lambda x: x['name']):
                c = f'  // {v["comment"]}' if v.get('comment') else ''
                f.write(f'extern {ct} PLC_{v["name"]};{c}\n')
            f.write('\n')
        f.write(f'#endif // {guard}_H\n')
    print(f'  [OK] C++ Header: {path} ({len(variables)} vars)')


def to_csv(variables, path):
    """CSV 映射表"""
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Variable', 'Address', 'PLC Type', 'QML Type', 'C Type', 'Group', 'Comment'])
        for v in variables:
            orig = v.get('original_address', '')
            comment = v.get('comment', '')
            if orig: comment = f'{comment} [was {orig}]'.strip()
            w.writerow([v['name'], v['address'], v['plc_type'],
                       v['hmi_type']['qml'], v['hmi_type']['c_type'],
                       v['group'], comment])
    print(f'  [OK] CSV Table: {path} ({len(variables)} vars)')


def to_markdown(variables, path):
    """Markdown 报告"""
    groups = defaultdict(list)
    for v in variables:
        groups[v['group']].append(v)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    brand = variables[0]['plc_brand'] if variables else 'Unknown'

    lines = [
        '# PLC Variable Mapping Report',
        '',
        f'- **PLC Brand:** {brand}',
        f'- **Total Variables:** {len(variables)}',
        f'- **Generated:** {now}',
        '',
        '## Group Summary',
        '',
        '| Group | Count | Types |',
        '|-------|-------|-------|',
    ]
    for g in sorted(groups.keys()):
        pts = groups[g]
        types = set(v['plc_type'] for v in pts)
        lines.append(f'| {g} | {len(pts)} | {", ".join(sorted(types))} |')

    lines += ['', '## Variable List', '']
    for g in sorted(groups.keys()):
        pts = sorted(groups[g], key=lambda x: x['name'])
        lines += [f'### {g} ({len(pts)})', '',
                  '| # | Name | Address | Type | Comment |',
                  '|---|------|---------|------|---------|']
        for i, v in enumerate(pts, 1):
            lines.append(f'| {i} | {v["name"]} | {v["address"]} | {v["plc_type"]} | {v.get("comment", "")} |')
        lines.append('')

    lines += ['---', '', '*Generated by HMI Toolbox*', '']
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  [OK] Markdown Report: {path}')


# ───────────────────────────────────────────────
#  统计
# ───────────────────────────────────────────────

def print_stats(variables):
    types = defaultdict(int)
    groups = set()
    for v in variables:
        types[v['plc_type']] += 1
        groups.add(v['group'])
    print(f'  - Total: {len(variables)} | Groups: {len(groups)}')
    print(f'  - Types: {", ".join(f"{k}={v}" for k, v in sorted(types.items()))}')


# ───────────────────────────────────────────────
#  示例生成
# ───────────────────────────────────────────────

def generate_examples(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Siemens
    siemens = [
        ('Motor_Start', 'I0.0', 'BOOL', 'Motor Start'),
        ('Motor_Stop', 'I0.1', 'BOOL', 'Motor Stop'),
        ('Motor_Running', 'Q0.0', 'BOOL', 'Running Status'),
        ('Motor_Fault', 'Q0.1', 'BOOL', 'Fault Alarm'),
        ('Motor_Speed', 'MW100', 'INT', 'RPM'),
        ('Motor_Torque', 'MW102', 'INT', 'Torque %'),
        ('Motor_Temp', 'MD104', 'REAL', 'Temperature C'),
        ('Pump_Start', 'I1.0', 'BOOL', 'Pump Start'),
        ('Pump_Running', 'Q1.0', 'BOOL', 'Pump Running'),
        ('Pump_Pressure', 'MD200', 'REAL', 'Pressure Bar'),
        ('Valve_Open', 'Q2.0', 'BOOL', 'Valve Open'),
        ('Valve_Position', 'MW300', 'INT', '0-100%'),
        ('Temp_Sensor1', 'MD400', 'REAL', 'Temp C'),
        ('Temp_Sensor2', 'MD404', 'REAL', 'Temp C'),
        ('System_Mode', 'MW900', 'WORD', '0=Stop 1=Run'),
        ('Alarm_Code', 'MD800', 'DWORD', 'Fault Code'),
        ('Production_Count', 'MD1000', 'DINT', 'Total Count'),
    ]
    path = os.path.join(output_dir, 'siemens_export.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Name', 'DataType', 'LogicalAddress', 'Comment'])
        for n, a, t, c in siemens:
            w.writerow([n, t, a, c])

    # Mitsubishi
    mitsu = [
        ('Motor_Start', 'M0', 'BIT', 'Motor Start'),
        ('Motor_Stop', 'M1', 'BIT', 'Motor Stop'),
        ('Motor_Running', 'Y0', 'BIT', 'Motor Running'),
        ('Motor_Fault', 'Y1', 'BIT', 'Motor Fault'),
        ('Motor_Speed', 'D100', 'BIN16', 'RPM'),
        ('Motor_Torque', 'D102', 'BIN16', 'Torque %'),
        ('Motor_Temp', 'D200', 'FLOAT', 'Temp C'),
        ('Pump_Start', 'M10', 'BIT', 'Pump Start'),
        ('Pump_Running', 'Y10', 'BIT', 'Pump Running'),
        ('Pump_Pressure', 'D300', 'FLOAT', 'Pressure MPa'),
        ('Alarm_Active', 'Y40', 'BIT', 'Alarm Output'),
        ('System_Mode', 'D1000', 'BIN16', '0=Stop 1=Auto'),
    ]
    path = os.path.join(output_dir, 'mitsubishi_export.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['LabelName', 'Device', 'DataType', 'Comment'])
        for n, a, t, c in mitsu:
            w.writerow([n, a, t, c])

    # Omron
    omron = [
        ('Motor_Start', 'CIO100.00', 'BOOL', 'Motor Start'),
        ('Motor_Stop', 'CIO100.01', 'BOOL', 'Motor Stop'),
        ('Motor_Running', 'CIO200.00', 'BOOL', 'Running'),
        ('Motor_Fault', 'CIO200.01', 'BOOL', 'Fault'),
        ('Motor_Speed', 'W10', 'INT', 'RPM'),
        ('Motor_Temp', 'D100', 'REAL', 'Temp C'),
        ('Pump_Pressure', 'D200', 'REAL', 'Pressure'),
        ('Valve_Open', 'CIO200.20', 'BOOL', 'Valve Open'),
        ('System_Mode', 'H100', 'WORD', '0=Stop 1=Run'),
    ]
    path = os.path.join(output_dir, 'omron_export.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Name', 'Address', 'DataType', 'Comment'])
        for n, a, t, c in omron:
            w.writerow([n, a, t, c])

    return siemens, mitsu, omron


# ───────────────────────────────────────────────
#  Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='PLC Variable Auto-Mapping Tool v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python plc_to_hmi_mapper.py -i export.csv -o ./output/
  python plc_to_hmi_mapper.py -i export.csv -f qml
  python plc_to_hmi_mapper.py -i export.csv --offset 100
  python plc_to_hmi_mapper.py --example
''')
    parser.add_argument('-i', '--input', help='输入文件 (CSV)')
    parser.add_argument('-o', '--output', default='./output', help='输出目录')
    parser.add_argument('-f', '--format', choices=['all', 'qml', 'csv', 'c', 'md'],
                        default='all', help='输出格式')
    parser.add_argument('--offset', type=int, default=0, help='地址偏移量')
    parser.add_argument('--example', action='store_true', help='生成示例文件')

    args = parser.parse_args()
    output_dir = os.path.abspath(args.output)

    print('=' * 56)
    print('  PLC Variable Auto-Mapping v2.0')
    print('  Qt QML / C++ Header / CSV / Markdown')
    print('=' * 56)
    print()

    if args.example:
        print('[gen] Generating example files for all 3 brands...')
        os.makedirs(output_dir, exist_ok=True)
        generate_examples(output_dir)
        print()
        for brand, fname in [('Siemens', 'siemens_export.csv'),
                              ('Mitsubishi', 'mitsubishi_export.csv'),
                              ('Omron', 'omron_export.csv')]:
            rows = read_file(os.path.join(output_dir, fname))
            brand_detected = detect_brand(rows[0] if rows else [], rows[1:] if rows else [])
            vars = parse_csv_rows(rows, brand_detected)
            print(f'  {brand}: {len(vars)} vars (detected: {brand_detected})')
            if brand_detected == 'siemens':
                to_qml(vars, os.path.join(output_dir, 'qml_siemens.qml'))
                to_c_header(vars, os.path.join(output_dir, 'plc_siemens.h'))
                to_csv(vars, os.path.join(output_dir, 'table_siemens.csv'))
                to_markdown(vars, os.path.join(output_dir, 'report_siemens.md'))
            elif brand_detected == 'mitsubishi':
                to_qml(vars, os.path.join(output_dir, 'qml_mitsubishi.qml'))
                to_c_header(vars, os.path.join(output_dir, 'plc_mitsubishi.h'))
                to_csv(vars, os.path.join(output_dir, 'table_mitsubishi.csv'))
                to_markdown(vars, os.path.join(output_dir, 'report_mitsubishi.md'))
            elif brand_detected == 'omron':
                to_qml(vars, os.path.join(output_dir, 'qml_omron.qml'))
                to_c_header(vars, os.path.join(output_dir, 'plc_omron.h'))
                to_csv(vars, os.path.join(output_dir, 'table_omron.csv'))
                to_markdown(vars, os.path.join(output_dir, 'report_omron.md'))
        print(f'\n[DONE] All examples -> {output_dir}')
        return

    if not args.input:
        parser.print_help()
        print('\n  Tip: python plc_to_hmi_mapper.py --example')
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f'[ERROR] File not found: {args.input}')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    print(f'[INPUT] {args.input}')

    rows = read_file(args.input)
    if not rows:
        print('[ERROR] Unable to read file')
        sys.exit(1)

    brand = detect_brand(rows[0], rows[1:])
    variables = parse_csv_rows(rows, brand)
    if not variables:
        print('[ERROR] No variables parsed. Check column headers.')
        print('  Expected: Name, Address/Location, Type, Comment')
        sys.exit(1)

    print(f'  Detected: {brand} | Parsed: {len(variables)} vars')

    if args.offset:
        variables = apply_offset(variables, args.offset)
        print(f'  Offset: +{args.offset} applied')

    print()

    # 输出
    if args.format in ('all', 'qml'):
        to_qml(variables, os.path.join(output_dir, 'hmi_mapping_qt.qml'))
    if args.format in ('all', 'csv'):
        to_csv(variables, os.path.join(output_dir, 'hmi_mapping_table.csv'))
    if args.format in ('all', 'c'):
        to_c_header(variables, os.path.join(output_dir, 'plc_hmi_mapping.h'))
    if args.format in ('all', 'md'):
        to_markdown(variables, os.path.join(output_dir, 'mapping_report.md'))

    print()
    print_stats(variables)
    print(f'\n[DONE] -> {output_dir}')


if __name__ == '__main__':
    main()
