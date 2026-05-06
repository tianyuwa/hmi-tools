@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================
echo  IO I/O Point Table Report - Example Run
echo ============================================
echo.
echo  Input: tags_input.csv (auto-generated)
echo  Output: .docx / .pdf / .md / .csv
echo.
mkdir output 2>nul
python io_report_generator.py --example -o output 2>nul
echo.
echo  Output files:
echo    output\IO_DI.csv            - Digital Input
echo    output\IO_DO.csv            - Digital Output
echo    output\IO_AI.csv            - Analog Input
echo    output\IO_AO.csv            - Analog Output
echo    output\IO_IOTableFull.csv  - Full I/O table
echo    output\IOReport.md         - Markdown report
echo    output\IOReport.docx       - Word report
echo    output\IOReport.pdf        - PDF report
echo.
echo  Done! Press any key to exit...
pause >nul
