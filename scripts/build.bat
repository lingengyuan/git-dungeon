@echo off
REM Git Dungeon Build Script - Windows

echo ========================================
echo Git Dungeon Build Script - Windows
echo ========================================

REM 检查 Python 版本
python --version

REM 安装构建依赖
echo [1/5] Installing build dependencies...
pip install -e . --quiet
pip install pyinstaller --quiet

REM 清理旧的构建文件
echo [2/5] Cleaning old build files...
rmdir /s /q build 2>nul
del /q dist\*.exe 2>nul
del /q *.spec 2>nul

REM 运行 PyInstaller
echo [3/5] Building with PyInstaller...
pyinstaller --onefile --windowed pyinstaller.spec

REM 创建目录结构
echo [4/5] Creating distribution package...
if not exist dist\assets mkdir dist\assets
if not exist dist\docs mkdir dist\docs
if not exist dist\src mkdir dist\src
xcopy /s /e /q src\* dist\src\ 2>nul
xcopy /s /e /q docs\* dist\docs\ 2>nul
copy README.md dist\ 2>nul
copy LICENSE dist\ 2>nul

echo [5/5] Build complete!
echo ========================================

echo.
echo Build output:
dir /b dist\

echo.
echo To run:
echo   dist\GitDungeon.exe
