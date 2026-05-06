@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================
echo  Recipe Converter - Excel  HMI Format
echo ============================================
echo.
echo  Generating example recipe data...
echo.
mkdir output 2>nul
python recipe_converter.py -m example -o output 2>nul
echo.
echo  Output files:
echo    output\recipes_example.csv  - Excel recipe table
echo    output\recipes_qml.qml      - Qt QML format
echo    output\recipes_data.cpp     - C++ data
echo.
echo  Done! Press any key to exit...
pause >nul
