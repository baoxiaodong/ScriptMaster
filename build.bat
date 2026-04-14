@echo off
chcp 936 >nul
echo ========================================
echo   清理打包缓存文件
echo ========================================
echo.

echo [1/3] 正在删除 build 目录内容...
if exist "build\" (
    for /d %%p in ("build\*") do rmdir /s /q "%%p" 2>nul
    del /q "build\*" 2>nul
    echo [完成] build 目录已清理
) else (
    echo [提示] build 目录不存在，跳过
)

echo.
echo [2/3] 正在清理 dist 目录...
if exist "dist\*" (
    del /q "dist\*" 2>nul
    for /d %%p in ("dist\*") do rmdir /s /q "%%p" 2>nul
    echo [完成] dist 目录已清理
) else (
    echo [提示] dist 目录已是空的
)

echo.
echo [3/3] 正在清理 Python 缓存...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
    )
)
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
)
echo [完成] 所有 __pycache__ 已清理

echo.
echo ========================================
echo   清理完成！可以重新打包了
echo ========================================
echo.
echo 提示: 运行 pyinstaller ScriptMaster.spec 开始打包
echo.
pause
