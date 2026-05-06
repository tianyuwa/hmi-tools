@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================
echo  PLC Variable Mapping Tool v2.0
echo  Qt QML / C++ Header / CSV output
echo ============================================
echo.
echo  Input file: ..\examples\siemens_export.csv (Siemens TIA Portal)
echo.
mkdir output 2>nul
python plc_to_hmi_mapper.py -i "..\examples\siemens_export.csv" -o output 2>nul
echo.
echo  Output files:
echo    output\hmi_mapping_qt.qml      - Qt QML format
echo    output\hmi_mapping_table.csv   - CSV mapping table
echo    output\plc_hmi_mapping.h       - C++ header
echo.
echo  Done! Press any key to exit...
pause >nul
