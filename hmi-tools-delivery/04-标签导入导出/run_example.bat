@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================
echo  PLC Tag Import/Export Tool v2.0 - Example
echo  Siemens TIA / Mitsubishi GXW / Omron CX-P
echo ============================================
echo.
echo  Generating examples for all 3 PLC brands...
echo.
mkdir output 2>nul
python tag_manager.py --example -o output 2>nul
echo.
echo  Output files:
echo    output/siemens_export.csv       - Siemens TIA input example
echo    output/mitsubishi_export.csv    - Mitsubishi GXW input example
echo    output/omron_export.csv         - Omron CX-P input example
echo    output/tags_siemens.csv         - Unified CSV (Siemens)
echo    output/tags_mitsubishi.csv      - Unified CSV (Mitsubishi)
echo    output/tags_omron.csv           - Unified CSV (Omron)
echo    output/qml_*.qml                - Qt QML binding format
echo    output/plc_*.h                  - C/C++ header format
echo    output/report_*.md              - Tag list report
echo.
echo  Try parsing your own file:
echo    python tag_manager.py -i my_tags.csv -o output_my
echo.
echo  Done! Press any key to exit...
pause >nul
