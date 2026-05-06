#!/usr/bin/env python3
"""
标签批量导入/导出工具 v2.0
==========================
原生解析 Siemens TIA Portal / Mitsubishi GX Works / Omron CX-Programmer 标签格式。
自动检测格式、品牌感知的地址转换、智能归类、差分对比，
输出 Qt QML / C Header / CSV 等 HMI 工程格式。

使用方法:
    python tag_manager.py --example                      # 生成示例
    python tag_manager.py -i tags.csv                    # 自动检测格式
    python tag_manager.py -i tags.csv --format siemens   # 强制指定
    python tag_manager.py --diff old.csv new.csv         # 差分对比

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

# ───────────────────────────────────────────────────────────
#  数据模型
# ───────────────────────────────────────────────────────────

class Tag:
    """单个标签变量"""
    def __init__(self, name='', address='', data_type='BOOL', comment='',
                 group='', source_plc='', original_name=''):
        self.name = name
        self.address = address
        self.data_type = data_type
        self.comment = comment
        self.group = group
        self.source_plc = source_plc
        self.original_name = original_name or name

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}


# ───────────────────────────────────────────────────────────
#  品牌地址常量
# ───────────────────────────────────────────────────────────

# 地址区域 → 中文说明
AREA_CN = {
    # Siemens
    'I': '数字量输入', 'Q': '数字量输出', 'M': '内部存储',
    'DB': '数据块', 'DI': '数字量输入(双字)',
    'AI': '模拟量输入', 'AQ': '模拟量输出',
    'T': '定时器', 'C': '计数器',
    # Mitsubishi
    'X': '输入继电器', 'Y': '输出继电器', 'M': '内部继电器',
    'D': '数据寄存器', 'R': '文件寄存器', 'L': '锁存继电器',
    'S': '状态继电器', 'B': '链接继电器', 'F': '报警器',
    'V': '变址寄存器', 'Z': '变址寄存器',
    # Omron
    'CIO': 'I/O通道', 'W': '工作字', 'H': '保持字',
    'D': '数据存储器', 'A': '辅助继电器', 'C': '计数器',
    'T': '定时器', 'E': '扩展数据', 'DM': '数据内存',
}

# 地址容量估算 (地址单位)
AREA_CAPACITY = {
    'I': 65536, 'Q': 65536, 'M': 65536, 'DB': 65536,
    'AI': 1024, 'AQ': 1024,
    'X': 1024, 'Y': 1024, 'D': 32768,
    'CIO': 6144, 'W': 512, 'H': 512,
    'A': 448, 'DM': 32768, 'E': 32768,
    'F': 2048, 'B': 2048, 'L': 2048, 'S': 2048,
}

# Siemens 数据类型宽度 (字节)
SIEMENS_TYPE_SIZE = {
    'BOOL': 1, 'BYTE': 1, 'WORD': 2, 'DWORD': 4,
    'INT': 2, 'DINT': 4, 'REAL': 4, 'TIME': 4,
    'S5TIME': 2, 'DATE': 2, 'CHAR': 1,
    'ARRAY': 0, 'STRUCT': 0, 'STRING': 256,
}

# 数据类型映射 (品牌通用型 → HMI 常用型)
TYPE_MAP = {
    'BOOL': 'BOOL', 'BIT': 'BOOL',
    'BYTE': 'BYTE', 'WORD': 'WORD', 'DWORD': 'DWORD',
    'INT': 'INT', 'DINT': 'DINT', 'LINT': 'DINT',
    'UINT': 'DINT', 'UDINT': 'DINT',
    'REAL': 'REAL', 'FLOAT': 'REAL', 'LREAL': 'REAL',
    'TIME': 'DINT', 'DATE': 'DINT',
    'BIN16': 'INT', 'BIN32': 'DINT', 'BIN': 'INT',
    'STRING': 'STRING', 'CHAR': 'BYTE',
}


# ───────────────────────────────────────────────────────────
#  格式检测
# ───────────────────────────────────────────────────────────

def detect_tag_format(rows):
    """通过表头 + 地址模式自动检测标签文件格式"""
    if not rows:
        return 'unknown'

    header = [h.upper().strip() for h in rows[0]]

    # --- Column-based detection ---

    # Mitsubishi GX Works (Japanese)
    if any('\u30e9\u30d9\u30eb\u540d' in h for h in header):
        return 'mitsubishi'
    if 'デバイス' in header:
        return 'mitsubishi'
    if 'LABELNAME' in header or 'LABEL NAME' in header:
        return 'mitsubishi'
    if 'DEVICE' in header:
        return 'mitsubishi'

    # Siemens: LOGICALADDRESS is unique to Siemens
    if any('LOGICALADDRESS' in h or 'LOGICAL ADDRESS' in h for h in header):
        return 'siemens'
    if {'NAME', 'DATATYPE'}.issubset(set(header)) and \
       any('LOGICAL' in h for h in header):
        return 'siemens'

    # Omron: PLCNAME
    if any('PLCNAME' in h or 'PLC NAME' in h for h in header):
        return 'omron'

    # --- Content-based detection for {Name, Address} pairs ---
    # Siemens and Omron both commonly export as Name, Address, DataType, Comment
    if {'NAME', 'ADDRESS'}.issubset(set(header)):
        # Extract first 5 data row addresses
        addr_col = None
        for i, h in enumerate(header):
            if h == 'ADDRESS':
                addr_col = i
                break

        if addr_col is not None:
            addr_samples = []
            for row in rows[1:min(6, len(rows))]:
                if addr_col < len(row):
                    a = row[addr_col].strip().upper()
                    if a:
                        addr_samples.append(a)

            siemens = sum(1 for a in addr_samples
                         if re.match(r'%?[IEQAM]', a))
            omron = sum(1 for a in addr_samples
                       if re.match(r'(CIO|W|H|A|D|TIM|CNT)\d', a))

            if omron > 0 and omron >= siemens:
                return 'omron'
            if siemens >= 2:
                return 'siemens'
            if omron >= 1:
                return 'omron'

        return 'generic'

    return 'generic'


# ───────────────────────────────────────────────────────────
#  Siemens TIA Portal 解析器
# ───────────────────────────────────────────────────────────

def parse_siemens(rows):
    """解析 Siemens TIA Portal CSV 导出"""
    tags = []
    header = rows[0]
    # Build column index
    col = {}
    for i, h in enumerate(header):
        hu = h.upper().strip()
        if hu in ('NAME', 'TAG', 'SYMBOL'):
            col['name'] = i
        elif hu in ('DATATYPE', 'DATA_TYPE', 'TYPE'):
            col['type'] = i
        elif hu in ('LOGICALADDRESS', 'LOGICAL ADDRESS', 'ADDRESS', 'ADDR'):
            col['addr'] = i
        elif hu in ('COMMENT', 'DESCRIPTION', 'DESC', '备注', '注释'):
            col['comment'] = i
        elif hu in ('GROUP', 'GROUP', 'FOLDER', '文件夹'):
            col['group'] = i

    if 'name' not in col or 'addr' not in col:
        return tags

    for row in rows[1:]:
        if len(row) <= max(col.values()):
            continue
        name = row[col['name']].strip()
        addr = row[col['addr']].strip()
        if not name or not addr:
            continue
        dtype = row[col.get('type', 0)].strip().upper() if 'type' in col and col['type'] < len(row) else 'BOOL'
        comment = row[col.get('comment', 0)].strip() if 'comment' in col else ''
        group = row[col.get('group', 0)].strip() if 'group' in col else ''

        # Normalize address
        addr_norm = normalize_siemens_address(addr)
        tags.append(Tag(name, addr_norm, dtype, comment, group, 'Siemens'))

    return tags


def normalize_siemens_address(addr):
    """归一化 Siemens 地址格式: I0.0, Q1.0, MW100, DB10.DBX0.0"""
    addr = addr.upper().strip()
    # Remove leading % if present
    if addr.startswith('%'):
        addr = addr[1:]
    # Standard forms like MW100 → %MW100
    match = re.match(r'^(M|I|Q|DB)(\d+)', addr)
    if match:
        area, num = match.groups()
        return f'%{area}{num}'
    # Bit-level: I0.0 → %I0.0
    match = re.match(r'^(I|Q|M)(\d+\.\d+)', addr)
    if match:
        return f'%{match.group(1)}{match.group(2)}'
    # AI/AQ: AIW0, AQW2
    match = re.match(r'^(AIW|AQW|AI|AQ)(\d+)', addr)
    if match:
        return f'%{match.group(1)}{match.group(2)}'
    # DB access: DB10.DBX0.0 or DB10.DBD0
    match = re.match(r'^DB(\d+)\.(DBX|DBB|DBW|DBD)(\d+(?:\.\d+)?)', addr)
    if match:
        return f'%DB{match.group(1)}.{match.group(2)}{match.group(3)}'
    return addr


def format_siemens_address(address):
    """将归一化地址转回 Siemens TIA 格式"""
    addr = address.upper().replace('%', '')
    # DB access
    match = re.match(r'DB(\d+)\.(DBX|DBB|DBW|DBD)(\d+)', addr)
    if match:
        return f'DB{match.group(1)}.{match.group(2)}{match.group(3)}'
    return addr


# ───────────────────────────────────────────────────────────
#  Mitsubishi GX Works 解析器
# ───────────────────────────────────────────────────────────

def parse_mitsubishi(rows):
    """解析 Mitsubishi GX Works CSV 导出 (日文/英文)"""
    tags = []
    header = rows[0]
    col = {}
    for i, h in enumerate(header):
        hu = h.upper().strip()
        if hu in ('ラベル名', 'LABELNAME', 'LABEL NAME', 'TAG', 'NAME'):
            col['name'] = i
        elif hu in ('デバイス', 'DEVICE', 'ADDRESS', 'ADDR'):
            col['addr'] = i
        elif hu in ('データ型', 'DATATYPE', 'DATA_TYPE', 'TYPE'):
            col['type'] = i
        elif hu in ('コメント', 'COMMENT', 'DESCRIPTION', '备注'):
            col['comment'] = i

    if 'name' not in col or 'addr' not in col:
        return tags

    for row in rows[1:]:
        if len(row) <= max(col.values()):
            continue
        name = row[col['name']].strip()
        addr = row[col['addr']].strip()
        if not name or not addr:
            continue
        dtype = row[col.get('type', 0)].strip().upper() if 'type' in col else 'BIT'
        comment = row[col.get('comment', 0)].strip() if 'comment' in col else ''

        # Normalize address
        addr_norm = normalize_mitsubishi_address(addr)
        # Map Mitsubishi type to generic
        generic_type = TYPE_MAP.get(dtype, 'BOOL')
        tags.append(Tag(name, addr_norm, generic_type, comment, '', 'Mitsubishi'))

    return tags


def normalize_mitsubishi_address(addr):
    """归一化三菱地址: X0, Y10, M100, D0"""
    addr = addr.upper().strip()
    # X/Y bit: X0, Y10
    match = re.match(r'^([XY])(\d+)', addr)
    if match:
        return f'%{match.group(1)}{match.group(2)}'
    # M internal relay: M0-M1023 (bit) but can also be word
    match = re.match(r'^M(\d+)', addr)
    if match:
        return f'%M{match.group(1)}'
    # D data register: D0-D7999
    match = re.match(r'^D(\d+)', addr)
    if match:
        return f'%D{match.group(1)}'
    # L / R / S / B / F
    match = re.match(r'^([LSRBF])(\d+)', addr)
    if match:
        return f'%{match.group(1)}{match.group(2)}'
    return addr


def format_mitsubishi_address(address):
    """将归一化地址转回三菱格式"""
    addr = address.replace('%', '')
    match = re.match(r'^([XYMLSBD])(\d+)', addr)
    if match:
        return f'{match.group(1)}{match.group(2)}'
    return addr


# ───────────────────────────────────────────────────────────
#  Omron CX-Programmer 解析器
# ───────────────────────────────────────────────────────────

def parse_omron(rows):
    """解析 Omron CX-Programmer CSV 导出"""
    tags = []
    header = rows[0]
    col = {}
    for i, h in enumerate(header):
        hu = h.upper().strip()
        if hu in ('NAME', 'TAG', 'SYMBOL', '変数名'):
            col['name'] = i
        elif hu in ('ADDRESS', 'ADDR', 'PLC ADDRESS'):
            col['addr'] = i
        elif hu in ('DATATYPE', 'DATA_TYPE', 'TYPE'):
            col['type'] = i
        elif hu in ('COMMENT', 'DESCRIPTION', '备注', 'コメント'):
            col['comment'] = i

    if 'name' not in col or 'addr' not in col:
        return tags

    for row in rows[1:]:
        if len(row) <= max(col.values()):
            continue
        name = row[col['name']].strip()
        addr = row[col['addr']].strip()
        if not name or not addr:
            continue
        dtype = row[col.get('type', 0)].strip().upper() if 'type' in col else 'BOOL'
        comment = row[col.get('comment', 0)].strip() if 'comment' in col else ''

        addr_norm = normalize_omron_address(addr)
        generic_type = TYPE_MAP.get(dtype, 'BOOL')
        tags.append(Tag(name, addr_norm, generic_type, comment, '', 'Omron'))

    return tags


def normalize_omron_address(addr):
    """归一化欧姆龙地址: CIO100, W0, D100, H0, A0"""
    addr = addr.upper().strip()
    # CIO channels: CIO100, CIO200.00
    match = re.match(r'^CIO(\d+(?:\.\d+)?)', addr)
    if match:
        return f'%CIO{match.group(1)}'
    # Work words: W0-W511
    match = re.match(r'^W(\d+(?:\.\d+)?)', addr)
    if match:
        return f'%W{match.group(1)}'
    # Data memory: D0-D32767
    match = re.match(r'^D(\d+(?:\.\d+)?)', addr)
    if match:
        return f'%D{match.group(1)}'
    # Holding relay: H0-H511
    match = re.match(r'^H(\d+(?:\.\d+)?)', addr)
    if match:
        return f'%H{match.group(1)}'
    # Auxiliary: A0-A447
    match = re.match(r'^A(\d+(?:\.\d+)?)', addr)
    if match:
        return f'%A{match.group(1)}'
    # Timer/Counter: TIM0, CNT0
    match = re.match(r'^(TIM|CNT)(\d+)', addr)
    if match:
        return f'%{match.group(1)}{match.group(2)}'
    # DM (Data Memory old style)
    match = re.match(r'^DM(\d+)', addr)
    if match:
        return f'%DM{match.group(1)}'
    return addr


def format_omron_address(address):
    """将归一化地址转回欧姆龙格式"""
    addr = address.replace('%', '')
    return addr


# ───────────────────────────────────────────────────────────
#  通用 CSV 解析（fallback）
# ───────────────────────────────────────────────────────────

def parse_generic(rows):
    """通用 CSV 标签解析，含智能列名映射"""
    tags = []
    header = rows[0]
    col = {}
    for i, h in enumerate(header):
        hu = h.upper().strip()
        if hu in ('NAME', 'TAG', 'SYMBOL', '变量名', '标记', 'VARIABLE'):
            col['name'] = i
        elif hu in ('ADDRESS', 'ADDR', 'PLCADDRESS', '地址', 'LOGICALADDRESS', 'LOGICAL ADDRESS'):
            col['addr'] = i
        elif hu in ('DATATYPE', 'DATA_TYPE', 'TYPE', '数据类型', '类型'):
            col['type'] = i
        elif hu in ('COMMENT', 'DESCRIPTION', 'DESC', '备注', '注释', '说明'):
            col['comment'] = i
        elif hu in ('GROUP', 'GROUP', 'FOLDER', '分组'):
            col['group'] = i

    if 'name' not in col or 'addr' not in col:
        return tags

    for row in rows[1:]:
        if len(row) <= max(col.values()):
            continue
        name = row[col['name']].strip()
        addr = row[col['addr']].strip()
        if not name or not addr:
            continue
        dtype = row[col.get('type', 0)].strip().upper() if 'type' in col else 'BOOL'
        comment = row[col.get('comment', 0)].strip() if 'comment' in col else ''
        group = row[col.get('group', 0)].strip() if 'group' in col else ''
        tags.append(Tag(name, addr, dtype, comment, group, 'Generic'))
    return tags


# ───────────────────────────────────────────────────────────
#  品牌感知的地址分组
# ───────────────────────────────────────────────────────────

def auto_group(tags, plc_brand='Generic'):
    """按地址区域自动分组（品牌感知）"""
    for t in tags:
        if t.group and t.group != 'Default':
            continue
        addr = t.address.upper()
        area_map = {
            # Siemens
            'I': '数字量输入', 'Q': '数字量输出', 'M': '内部存储',
            'DB': '数据块', 'AI': '模拟量输入', 'AQ': '模拟量输出',
            'T': '定时器', 'C': '计数器',
            # Mitsubishi
            'X': '输入继电器', 'Y': '输出继电器',
            'D': '数据寄存器',
            # Omron
            'CIO': 'I/O通道', 'W': '工作字', 'H': '保持字',
            'A': '辅助继电器', 'DM': '数据内存',
        }
        found = False
        for prefix, group_name in area_map.items():
            if addr.startswith(f'%{prefix}') or addr.startswith(prefix):
                t.group = group_name
                found = True
                break
        if not found:
            # Try first letter
            m = re.match(r'%?([A-Z]+)', addr)
            if m:
                first = m.group(1)
                t.group = AREA_CN.get(first, first)
            else:
                t.group = '未分配'


# ───────────────────────────────────────────────────────────
#  品牌检测 + 文件读取
# ───────────────────────────────────────────────────────────

def read_tag_file(file_path, force_format=None):
    """读取标签文件，自动检测品牌并解析"""
    if not os.path.exists(file_path):
        print(f'  ERROR: File not found: {file_path}')
        return []

    # Try UTF-8 with BOM, UTF-8, Shift-JIS (for Mitsubishi Japanese), GBK
    encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'gbk', 'latin-1']
    rows = None
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            if rows and len(rows) > 0:
                break
        except Exception:
            continue

    if not rows or len(rows) < 2:
        print(f'  ERROR: Unable to read file or insufficient data')
        return []

    # Auto-detect or force format
    fmt = force_format if force_format else detect_tag_format(rows)

    parsers = {
        'siemens': ('Siemens TIA Portal', parse_siemens),
        'mitsubishi': ('Mitsubishi GX Works', parse_mitsubishi),
        'omron': ('Omron CX-Programmer', parse_omron),
        'generic': ('Generic CSV', parse_generic),
    }

    brand_name, parser = parsers.get(fmt, ('Unknown', parse_generic))
    print(f'  [detected] {brand_name} ({fmt})')

    tags = parser(rows)
    if not tags:
        print(f'  WARNING: 0 tags parsed. Check column headers.')
        return []

    # Auto-group
    auto_group(tags, fmt)
    return tags


# ───────────────────────────────────────────────────────────
#  写入/导出函数
# ───────────────────────────────────────────────────────────

def write_csv(tags, csv_path):
    """写出统一格式标签 CSV"""
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['变量名', '地址', '数据类型', '备注', '分组', '源PLC'])
        for t in tags:
            w.writerow([t.name, t.address, t.data_type, t.comment, t.group, t.source_plc])
    print(f'  [OK] CSV: {csv_path} ({len(tags)} tags)')


def export_native_format(tags, output_path, fmt='siemens'):
    """导出为原生 PLC 工程格式"""
    if fmt == 'siemens':
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['Name', 'DataType', 'LogicalAddress', 'Comment', 'Group'])
            for t in tags:
                addr = format_siemens_address(t.address)
                w.writerow([t.name, t.data_type, addr, t.comment, t.group])
        print(f'  [OK] Siemens TIA: {output_path}')

    elif fmt == 'mitsubishi':
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['LabelName', 'Device', 'DataType', 'Comment'])
            for t in tags:
                addr = format_mitsubishi_address(t.address)
                mtype = {'BOOL': 'BIT'}.get(t.data_type, t.data_type)
                w.writerow([t.name, addr, mtype, t.comment])
        print(f'  [OK] Mitsubishi GXW: {output_path}')

    elif fmt == 'omron':
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['Name', 'Address', 'DataType', 'Comment'])
            for t in tags:
                addr = format_omron_address(t.address)
                w.writerow([t.name, addr, t.data_type, t.comment])
        print(f'  [OK] Omron CX-P: {output_path}')

def generate_qt_qml(tags, output_path):
    """生成 Qt QML 标签绑定"""
    type_map = {'BOOL': 'bool', 'INT': 'int', 'DINT': 'int', 'REAL': 'real',
                'WORD': 'int', 'DWORD': 'int', 'BYTE': 'int', 'STRING': 'string',
                'TIME': 'int'}

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('import QtQuick 2.15\n\n')
        f.write('// PLC Tag Bindings (auto-generated)\n')
        src = ', '.join(sorted({t.source_plc for t in tags}))
        f.write(f'// Source: {src}\n')
        f.write(f'// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')
        f.write('QtObject {\n')

        for t in sorted(tags, key=lambda x: x.name):
            qml_type = type_map.get(t.data_type, 'var')
            comment = f'  // {t.comment}' if t.comment else ''
            f.write(f'    property {qml_type} {t.name}: 0{comment}\n')

        f.write('}\n')
    print(f'  [OK] Qt QML: {output_path}')


def generate_c_header(tags, output_path):
    """生成 C/C++ 头文件"""
    base_name = os.path.splitext(os.path.basename(output_path))[0]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'#ifndef {base_name.upper()}_H\n')
        f.write(f'#define {base_name.upper()}_H\n\n')
        f.write(f'// PLC Tag Definitions (auto-generated)\n')
        f.write(f'// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')
        f.write(f'#include <stdint.h>\n\n')

        # Group by type
        types = defaultdict(list)
        for t in tags:
            types[t.data_type].append(t)

        type_c = {
            'BOOL': 'bool', 'BYTE': 'uint8_t', 'WORD': 'uint16_t',
            'DWORD': 'uint32_t', 'INT': 'int16_t', 'DINT': 'int32_t',
            'REAL': 'float', 'STRING': 'char*',
        }

        for c_type in ['BOOL', 'BYTE', 'WORD', 'DWORD', 'INT', 'DINT', 'REAL']:
            if c_type not in types:
                continue
            ct = type_c.get(c_type, 'int')
            f.write(f'// {c_type} Tags\n')
            for t in sorted(types[c_type], key=lambda x: x.name):
                comment = f'  // {t.comment}' if t.comment else ''
                f.write(f'extern {ct} PLC_{t.name};{comment}\n')
            f.write('\n')

        f.write(f'#endif // {base_name.upper()}_H\n')
    print(f'  [OK] C Header: {output_path}')


def generate_markdown(tags, output_path):
    """生成 Markdown 标签清单报告"""
    groups = defaultdict(list)
    for t in tags:
        groups[t.group].append(t)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    src = ', '.join(sorted({t.source_plc for t in tags}))
    lines = [
        '# Tag List Report',
        '',
        f'- **Source:** {src}',
        f'- **Total Tags:** {len(tags)}',
        f'- **Generated:** {now}',
        '',
        '---',
        '',
        '## Statistics',
        '',
        '| Group | Count |',
        '|-------|-------|',
    ]

    for gname in sorted(groups.keys()):
        lines.append(f'| {gname} | {len(groups[gname])} |')

    lines += ['', '---', '', '## Detail', '']

    for gname in sorted(groups.keys()):
        pts = sorted(groups[gname], key=lambda x: x.name)
        lines += [f'### {gname} ({len(pts)})', '',
                  '| # | Name | Address | Type | Comment |',
                  '|---|------|---------|------|---------|']
        for i, t in enumerate(pts, 1):
            lines.append(f'| {i} | {t.name} | {t.address} | {t.data_type} | {t.comment} |')
        lines.append('')

    lines += ['---', '', '*Auto-generated by HMI Toolbox*', '']

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  [OK] Markdown: {output_path}')


# ───────────────────────────────────────────────────────────
#  差分对比
# ───────────────────────────────────────────────────────────

def diff_tags(old_tags, new_tags):
    """差分对比两组标签"""
    old_map = {t.name: t for t in old_tags}
    new_map = {t.name: t for t in new_tags}

    added = [t for t in new_tags if t.name not in old_map]
    removed = [t for t in old_tags if t.name not in new_map]
    modified = []
    for name, ot in old_map.items():
        if name in new_map:
            nt = new_map[name]
            if (ot.address != nt.address or ot.data_type != nt.data_type):
                modified.append((ot, nt))

    unchanged = len(old_tags) - len(removed) - len(modified)
    return {'added': added, 'removed': removed, 'modified': modified,
            'unchanged': unchanged}


def write_diff_report(diff, output_path):
    """写出差分对比报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        '# Tag Comparison Report',
        f'**Generated:** {now}',
        '',
        '## Summary',
        f'- Added: {len(diff["added"])}',
        f'- Removed: {len(diff["removed"])}',
        f'- Modified: {len(diff["modified"])}',
        f'- Unchanged: {diff["unchanged"]}',
    ]

    if diff['added']:
        lines += ['', '## Added Tags', '',
                  '| Name | Address | Type | Comment |',
                  '|------|---------|------|---------|']
        for t in diff['added']:
            lines.append(f'| {t.name} | {t.address} | {t.data_type} | {t.comment} |')

    if diff['removed']:
        lines += ['', '## Removed Tags', '',
                  '| Name | Address | Type | Comment |',
                  '|------|---------|------|---------|']
        for t in diff['removed']:
            lines.append(f'| {t.name} | {t.address} | {t.data_type} | {t.comment} |')

    if diff['modified']:
        lines += ['', '## Modified Tags', '']
        for old, new in diff['modified']:
            lines += [
                f'### {old.name}',
                f'- Address: {old.address} → {new.address}',
                f'- Type: {old.data_type} → {new.data_type}',
                '',
            ]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'  [OK] Diff Report: {output_path}')


# ───────────────────────────────────────────────────────────
#  Batch Rename
# ───────────────────────────────────────────────────────────

def batch_rename(tags, **kwargs):
    """批量重命名标签"""
    result = []
    for t in tags:
        new_name = t.name
        if kwargs.get('find') and kwargs.get('replace'):
            new_name = new_name.replace(kwargs['find'], kwargs['replace'])
        if kwargs.get('prefix'):
            new_name = kwargs['prefix'] + '_' + new_name
        if kwargs.get('suffix'):
            new_name = new_name + '_' + kwargs['suffix']
        if kwargs.get('strip_prefix'):
            new_name = re.sub(r'^[A-Za-z]+_\d+_', '', new_name)
        if kwargs.get('uppercase'):
            new_name = new_name.upper()
        if kwargs.get('lowercase'):
            new_name = new_name.lower()

        t.original_name = t.name
        t.name = new_name
        result.append(t)
    return result


# ───────────────────────────────────────────────────────────
#  示例生成
# ───────────────────────────────────────────────────────────

def generate_examples(output_dir):
    """生成各品牌示例文件"""
    os.makedirs(output_dir, exist_ok=True)

    # Siemens 示例
    siemens_tags = [
        Tag('Motor_Start', '%I0.0', 'BOOL', 'Motor Start', 'DI', 'Siemens'),
        Tag('Motor_Stop', '%I0.1', 'BOOL', 'Motor Stop', 'DI', 'Siemens'),
        Tag('Motor_Running', '%Q0.0', 'BOOL', 'Running Status', 'DO', 'Siemens'),
        Tag('Motor_Fault', '%Q0.1', 'BOOL', 'Fault Alarm', 'DO', 'Siemens'),
        Tag('Motor_Speed', '%MW100', 'INT', 'RPM', 'AI', 'Siemens'),
        Tag('Motor_Torque', '%MW102', 'INT', 'Torque %', 'AI', 'Siemens'),
        Tag('Motor_Temp', '%MD104', 'REAL', 'Temperature C', 'AI', 'Siemens'),
        Tag('Motor_Current', '%MD108', 'REAL', 'Current A', 'AI', 'Siemens'),
        Tag('Pump_Start', '%I1.0', 'BOOL', 'Pump Start', 'DI', 'Siemens'),
        Tag('Pump_Running', '%Q1.0', 'BOOL', 'Pump Running', 'DO', 'Siemens'),
        Tag('Pump_Pressure', '%MD200', 'REAL', 'Pressure Bar', 'AI', 'Siemens'),
        Tag('Valve_Open', '%Q2.0', 'BOOL', 'Valve Open', 'DO', 'Siemens'),
        Tag('Valve_Close', '%Q2.1', 'BOOL', 'Valve Close', 'DO', 'Siemens'),
        Tag('Valve_Position', '%MW300', 'INT', 'Position 0-100%', 'AO', 'Siemens'),
        Tag('Temp_Sensor1', '%MD400', 'REAL', 'Temp Sensor 1', 'AI', 'Siemens'),
        Tag('Temp_Sensor2', '%MD404', 'REAL', 'Temp Sensor 2', 'AI', 'Siemens'),
        Tag('System_Mode', '%MW900', 'WORD', '0=Stop 1=Run 2=Auto', 'Status', 'Siemens'),
        Tag('Alarm_Active', '%Q10.0', 'BOOL', 'Alarm Indicator', 'DO', 'Siemens'),
        Tag('Alarm_Code', '%MD800', 'DWORD', 'Fault Code', 'Status', 'Siemens'),
        Tag('Production_Count', '%MD1000', 'DINT', 'Total Count', 'Counter', 'Siemens'),
        Tag('Production_Yield', '%MD1004', 'REAL', 'Yield %', 'Counter', 'Siemens'),
    ]

    siemens_path = os.path.join(output_dir, 'siemens_export.csv')
    with open(siemens_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Name', 'DataType', 'LogicalAddress', 'Comment'])
        for t in siemens_tags:
            addr = format_siemens_address(t.address)
            w.writerow([t.name, t.data_type, addr, t.comment])
    print(f'  [OK] Siemens example: {siemens_path}')

    # Mitsubishi 示例
    mitsubishi_tags = [
        Tag('Motor_Start', '%M0', 'BOOL', 'Motor Start', 'DI', 'Mitsubishi'),
        Tag('Motor_Stop', '%M1', 'BOOL', 'Motor Stop', 'DI', 'Mitsubishi'),
        Tag('Motor_Running', '%Y0', 'BOOL', 'Motor Running', 'DO', 'Mitsubishi'),
        Tag('Motor_Fault', '%Y1', 'BOOL', 'Motor Fault', 'DO', 'Mitsubishi'),
        Tag('Motor_Speed', '%D100', 'INT', 'Motor RPM', 'AI', 'Mitsubishi'),
        Tag('Motor_Torque', '%D102', 'INT', 'Torque %', 'AI', 'Mitsubishi'),
        Tag('Motor_Temp', '%D200', 'REAL', 'Temp C', 'AI', 'Mitsubishi'),
        Tag('Pump_Start', '%M10', 'BOOL', 'Pump Start', 'DI', 'Mitsubishi'),
        Tag('Pump_Running', '%Y10', 'BOOL', 'Pump Running', 'DO', 'Mitsubishi'),
        Tag('Pump_Pressure', '%D300', 'REAL', 'Pressure MPa', 'AI', 'Mitsubishi'),
        Tag('Valve_Open', '%Y20', 'BOOL', 'Valve Open', 'DO', 'Mitsubishi'),
        Tag('Valve_Pos', '%D400', 'INT', 'Valve %', 'AO', 'Mitsubishi'),
        Tag('Temp_Sensor1', '%D500', 'REAL', 'Temp C', 'AI', 'Mitsubishi'),
        Tag('Conveyor_Speed', '%D800', 'INT', 'm/min', 'AI', 'Mitsubishi'),
        Tag('Alarm_Active', '%Y40', 'BOOL', 'Alarm', 'DO', 'Mitsubishi'),
        Tag('System_Mode', '%D1000', 'INT', '0=Stop 1=Manual 2=Auto', 'Status', 'Mitsubishi'),
    ]

    mitsubishi_path = os.path.join(output_dir, 'mitsubishi_export.csv')
    with open(mitsubishi_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['\u30e9\u30d9\u30eb\u540d', '\u30c7\u30d0\u30a4\u30b9',
                    '\u30c7\u30fc\u30bf\u578b', '\u30b3\u30e1\u30f3\u30c8'])
        for t in mitsubishi_tags:
            addr = format_mitsubishi_address(t.address)
            mtype = 'BIT' if t.data_type == 'BOOL' else t.data_type
            w.writerow([t.name, addr, mtype, t.comment])
    print(f'  [OK] Mitsubishi example: {mitsubishi_path}')

    # Omron 示例
    omron_tags = [
        Tag('Motor_Start', '%CIO100.00', 'BOOL', 'Motor Start', 'DI', 'Omron'),
        Tag('Motor_Stop', '%CIO100.01', 'BOOL', 'Motor Stop', 'DI', 'Omron'),
        Tag('Motor_Running', '%CIO200.00', 'BOOL', 'Motor Running', 'DO', 'Omron'),
        Tag('Motor_Fault', '%CIO200.01', 'BOOL', 'Motor Fault', 'DO', 'Omron'),
        Tag('Motor_Speed', '%W10', 'INT', 'Motor RPM', 'AI', 'Omron'),
        Tag('Motor_Temp', '%D100', 'REAL', 'Temp C', 'AI', 'Omron'),
        Tag('Pump_Start', '%CIO100.02', 'BOOL', 'Pump Start', 'DI', 'Omron'),
        Tag('Pump_Running', '%CIO200.10', 'BOOL', 'Pump Running', 'DO', 'Omron'),
        Tag('Pump_Pressure', '%D200', 'REAL', 'Pressure', 'AI', 'Omron'),
        Tag('Valve_Open', '%CIO200.20', 'BOOL', 'Valve Open', 'DO', 'Omron'),
        Tag('Valve_Position', '%D300', 'INT', 'Position %', 'AO', 'Omron'),
        Tag('Temp_Sensor1', '%D500', 'REAL', 'Temp C', 'AI', 'Omron'),
        Tag('Alarm_Active', '%CIO210.00', 'BOOL', 'Alarm', 'DO', 'Omron'),
        Tag('Alarm_Code', '%D1000', 'DWORD', 'Fault Code', 'Status', 'Omron'),
        Tag('System_Mode', '%H100', 'WORD', '0=Stop 1=Run', 'Status', 'Omron'),
    ]

    omron_path = os.path.join(output_dir, 'omron_export.csv')
    with open(omron_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Name', 'Address', 'DataType', 'Comment'])
        for t in omron_tags:
            addr = format_omron_address(t.address)
            w.writerow([t.name, addr, t.data_type, t.comment])
    print(f'  [OK] Omron example: {omron_path}')

    return siemens_tags, mitsubishi_tags, omron_tags


# ───────────────────────────────────────────────────────────
#  Main
# ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Tag Manager v2 - PLC Tag Import/Export with Native Format Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python tag_manager.py --example
  python tag_manager.py -i tags.csv
  python tag_manager.py -i tags.csv --export-native siemens
  python tag_manager.py --diff old.csv new.csv
  python tag_manager.py -i tags.csv --rename find=_old,replace=_new --uppercase
''')

    parser.add_argument('-i', '--input', help='Input tag file (auto-detect format)')
    parser.add_argument('-o', '--output', default='./output', help='Output directory')
    parser.add_argument('--format', choices=['siemens', 'mitsubishi', 'omron', 'generic'],
                        help='Force file format (default: auto-detect)')
    parser.add_argument('--rename', help='Rename rules: find=old,replace=new,prefix=HMI,suffix=v2')
    parser.add_argument('--export-native', choices=['siemens', 'mitsubishi', 'omron'],
                        help='Export back to native PLC format')
    parser.add_argument('--skip-qml', action='store_true', help='Skip QML export')
    parser.add_argument('--skip-c', action='store_true', help='Skip C header export')
    parser.add_argument('--diff', nargs=2, metavar=('OLD', 'NEW'),
                        help='Diff comparison between two tag files')
    parser.add_argument('--example', action='store_true', help='Generate example files')
    parser.add_argument('--uppercase', action='store_true', help='Convert names to UPPERCASE')
    parser.add_argument('--lowercase', action='store_true', help='Convert names to lowercase')

    args = parser.parse_args()
    output_dir = os.path.abspath(args.output)

    print('=' * 56)
    print('  Tag Manager v2 - PLC Tag Import/Export')
    print('  Siemens TIA / Mitsubishi GXW / Omron CX-P')
    print('=' * 56)
    print()

    if args.example:
        print('[gen] Generating example files...')
        os.makedirs(output_dir, exist_ok=True)
        siemens, mitsubishi, omron = generate_examples(output_dir)

        # Also process and output all three
        for brand, tags, fmt in [
            ('Siemens', siemens, 'siemens'),
            ('Mitsubishi', mitsubishi, 'mitsubishi'),
            ('Omron', omron, 'omron'),
        ]:
            print(f'\n  Processing {brand} ({len(tags)} tags)...')
            auto_group(tags, brand)
            write_csv(tags, os.path.join(output_dir, f'tags_{fmt}.csv'))
            generate_qt_qml(tags, os.path.join(output_dir, f'qml_{fmt}.qml'))
            generate_c_header(tags, os.path.join(output_dir, f'plc_{fmt}.h'))
            generate_markdown(tags, os.path.join(output_dir, f'report_{fmt}.md'))

        print(f'\n[OK] All examples -> {output_dir}')
        return

    if args.diff:
        print(f'[diff] {args.diff[0]}  vs  {args.diff[1]}')
        old_tags = read_tag_file(args.diff[0])
        new_tags = read_tag_file(args.diff[1])
        if not old_tags or not new_tags:
            print('  ERROR: Could not read one or both files')
            sys.exit(1)
        diff = diff_tags(old_tags, new_tags)
        os.makedirs(output_dir, exist_ok=True)
        write_diff_report(diff, os.path.join(output_dir, 'diff_report.md'))
        summary = f'+{len(diff["added"])} -{len(diff["removed"])} ~{len(diff["modified"])} ={diff["unchanged"]}'
        print(f'  Summary: {summary}')
        return

    if not args.input:
        parser.print_help()
        print()
        print('  Tip: python tag_manager.py --example')
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f'  ERROR: File not found: {args.input}')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    print(f'  Input: {args.input}')
    tags = read_tag_file(args.input, force_format=args.format)
    if not tags:
        print('  ERROR: 0 tags parsed. Check column headers.')
        print('  Expected columns: Name/Address/Type/Comment (or native format)')
        sys.exit(1)

    print(f'  Parsed: {len(tags)} tags')

    # Rename
    if args.rename:
        opts = {}
        for kv in args.rename.split(','):
            if '=' in kv:
                k, v = kv.split('=', 1)
                opts[k.strip()] = v.strip()
        if args.uppercase:
            opts['uppercase'] = True
        if args.lowercase:
            opts['lowercase'] = True
        tags = batch_rename(tags, **opts)
        print(f'  Renamed with: {args.rename}')

    # Adjust names
    if args.uppercase and not args.rename:
        tags = batch_rename(tags, uppercase=True)
        print(f'  Converted to UPPERCASE')
    if args.lowercase and not args.rename:
        tags = batch_rename(tags, lowercase=True)
        print(f'  Converted to lowercase')

    # Export
    print()
    write_csv(tags, os.path.join(output_dir, 'tags_export.csv'))


    if not args.skip_qml:
        generate_qt_qml(tags, os.path.join(output_dir, 'tag_bindings.qml'))
    if not args.skip_c:
        generate_c_header(tags, os.path.join(output_dir, 'plc_tags.h'))

    generate_markdown(tags, os.path.join(output_dir, 'tag_report.md'))

    if args.export_native:
        export_native_format(tags, os.path.join(output_dir, f'export_{args.export_native}.csv'),
                             fmt=args.export_native)

    print(f'\n[OK] All outputs -> {output_dir}')


if __name__ == '__main__':
    main()

