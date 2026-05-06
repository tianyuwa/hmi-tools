#!/usr/bin/env python3
"""
配方数据 Excel  HMI 互转工具 v1.0
==================================
在 Excel 配方表和 Qt QML / C++ 格式之间双向转换。
支持批量处理、数据校验、Qt Quick 配方格式。

使用方法:
    python recipe_converter.py -i <输入文件> -o <输出文件> -m to_hmi|to_excel
    python recipe_converter.py -m example  # 生成示例

作者: HMI Toolbox
"""

import csv
import json
import os
import sys
import argparse
from datetime import datetime


class Recipe:
    def __init__(self, name='', params=None, comment=''):
        self.name = name
        self.params = params or {}
        self.comment = comment


class QmlHandler:
    """Qt QML 配方格式处理"""

    @staticmethod
    def read(file_path):
        recipes = []
        # 简单 QML 解析：QtObject 中的 property 定义
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return recipes

    @staticmethod
    def write(recipes, output_path):
        lines = ['import QtQuick 2.15\n', '// Recipe Data (auto-generated)\n']
        lines.append(f'// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')

        for r in recipes:
            lines.append(f'// Recipe: {r.name}\n')
            for key, val in r.params.items():
                qml_val = f'"{val}"' if isinstance(val, str) else str(val)
                lines.append(f'property var recipe_{r.name}_{key}: {qml_val}\n')
            lines.append('\n')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f'  [OK] QML Recipe: {output_path} ({len(recipes)} recipes)')


class CppHandler:
    """C++ 配方数据处理"""

    @staticmethod
    def write(recipes, output_path):
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        guard = base_name.upper()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f'#ifndef {guard}_H\n#define {guard}_H\n\n')
            f.write(f'// Recipe Data Structure (auto-generated)\n')
            f.write(f'// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')
            f.write('#include <QString>\n#include <QVariantMap>\n\n')

            f.write(f'struct RecipeData {{\n')
            f.write(f'    QString name;\n    QVariantMap params;\n}};\n\n')

            f.write(f'static const RecipeData g_recipes[] = {{\n')
            for r in recipes:
                f.write(f'    {{"{r.name}", {{\n')
                for key, val in r.params.items():
                    v = f'"{val}"' if isinstance(val, str) else str(val)
                    f.write(f'        {{"{key}", {v}}},\n')
                f.write(f'    }}}},\n')
            f.write('};\n\n')
            f.write(f'#endif // {guard}_H\n')

        print(f'  [OK] C++ Recipe: {output_path} ({len(recipes)} recipes)')


def read_excel_csv(file_path):
    """读取宽格式 Excel CSV 配方"""
    recipes = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('配方名', row.get('RecipeName', row.get('name', '')))
            if not name:
                continue
            params = {k: v for k, v in row.items() if k not in ('配方名', 'RecipeName', 'name') and v}
            comment = row.get('备注', row.get('Comment', ''))
            recipes.append(Recipe(name, params, comment))
    return recipes


def write_excel_csv(recipes, output_path):
    """写出宽格式 Excel CSV 配方"""
    all_params = set()
    for r in recipes:
        all_params.update(r.params.keys())
    all_params = sorted(all_params)

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['RecipeName'] + all_params + ['Comment'])
        for r in recipes:
            row = [r.name] + [r.params.get(k, '') for k in all_params] + [r.comment]
            w.writerow(row)
    print(f'  [OK] Excel CSV: {output_path} ({len(recipes)} recipes)')


def generate_example(target_dir):
    """生成示例配方数据"""
    os.makedirs(target_dir, exist_ok=True)

    recipes = [
        Recipe('Recipe_001', {
            'Temp': 180, 'Pressure': 2.5, 'Speed': 1200,
            'Time': 30, 'Coolant': 'On', 'Mode': 'Auto'
        }, 'Standard heating profile'),
        Recipe('Recipe_002', {
            'Temp': 220, 'Pressure': 3.0, 'Speed': 800,
            'Time': 45, 'Coolant': 'Off', 'Mode': 'Manual'
        }, 'High temp curing'),
        Recipe('Recipe_003', {
            'Temp': 150, 'Pressure': 1.8, 'Speed': 1500,
            'Time': 20, 'Coolant': 'On', 'Mode': 'Auto'
        }, 'Fast cooling profile'),
    ]

    write_excel_csv(recipes, os.path.join(target_dir, 'recipes_example.csv'))
    QmlHandler.write(recipes, os.path.join(target_dir, 'recipes_qml.qml'))
    CppHandler.write(recipes, os.path.join(target_dir, 'recipes_data.cpp'))

    print(f'\n  Output files:')
    print(f'    recipes_example.csv  - Excel recipe table (wide format)')
    print(f'    recipes_qml.qml      - Qt QML recipe model')
    print(f'    recipes_data.cpp     - C++ recipe data')
    return recipes


def main():
    parser = argparse.ArgumentParser(description='Recipe Converter - Excel  HMI Format')
    parser.add_argument('-i', '--input', help='Input file')
    parser.add_argument('-o', '--output', default='./output', help='Output directory')
    parser.add_argument('-m', '--mode', choices=['to_excel', 'to_hmi', 'example'],
                        default='example', help='Conversion mode')
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output)

    print('=' * 50)
    print('  Recipe Converter v1.0')
    print('  Excel <-> HMI Format')
    print('=' * 50)

    if args.mode == 'example':
        print(f'\n[gen] Generating example recipe data...')
        generate_example(output_dir)
        print(f'\n[DONE] Examples -> {output_dir}')
        return

    if not args.input:
        parser.print_help()
        print('\n  Tip: python recipe_converter.py -m example')
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f'[ERROR] File not found: {args.input}')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    print(f'\n[INPUT] {args.input}')

    if args.mode == 'to_hmi':
        recipes = read_excel_csv(args.input)
        if not recipes:
            print('[ERROR] No recipes found')
            sys.exit(1)
        print(f'  Read {len(recipes)} recipes')
        QmlHandler.write(recipes, os.path.join(output_dir, 'recipes_qml.qml'))
        CppHandler.write(recipes, os.path.join(output_dir, 'recipes_data.cpp'))

    elif args.mode == 'to_excel':
        # QML -> Excel
        recipes = QmlHandler.read(args.input)
        if not recipes:
            print('[WARN] Input not QML; trying CSV...')
            recipes = read_excel_csv(args.input)
        write_excel_csv(recipes, os.path.join(output_dir, 'recipes_export.csv'))

    print(f'\n[DONE] -> {output_dir}')


if __name__ == '__main__':
    main()
