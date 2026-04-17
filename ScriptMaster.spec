# -*- mode: python ; coding: utf-8 -*-
"""
AI分镜生成器 - PyInstaller 打包配置
使用方法: pyinstaller ScriptMaster.spec
"""
import os
import shutil
from pathlib import Path
import importlib.util

PROJECT_ROOT = Path(SPECPATH)

def find_package_dir(name):
    spec = importlib.util.find_spec(name)
    if spec and spec.origin:
        return Path(spec.origin).parent
    return None

streamlit_dir = find_package_dir("streamlit")
tui_editor_dir = find_package_dir("st_tui_editor")

# ── 数据文件 ─────────────────────────────────────────────────────
datas = []

# 1. 项目自身代码
datas.append((str(PROJECT_ROOT / "config"), "app/config"))
datas.append((str(PROJECT_ROOT / "core"), "app/core"))
datas.append((str(PROJECT_ROOT / "ui"), "app/ui"))
datas.append((str(PROJECT_ROOT / "utils"), "app/utils"))
datas.append((str(PROJECT_ROOT / "main.py"), "app"))

# 2. st_tui_editor 插件资源 (修复打包后缺少 pyproject.toml 报错)
if tui_editor_dir:
    if (tui_editor_dir / "pyproject.toml").exists():
        datas.append((str(tui_editor_dir / "pyproject.toml"), "st_tui_editor"))
    if (tui_editor_dir / "frontend").exists():
        datas.append((str(tui_editor_dir / "frontend"), "st_tui_editor/frontend"))

# 3. Streamlit 静态资源（JS/CSS/HTML）
if streamlit_dir:
    static_dir = streamlit_dir / "static"
    if static_dir.exists():
        datas.append((str(static_dir), "streamlit/static"))

# 4. Streamlit 其他数据子目录（runtime、web 等）
if streamlit_dir:
    for item in streamlit_dir.iterdir():
        if item.is_dir() and item.name not in ('static', '__pycache__', 'tests'):
            if item.name in ('components', 'cors', 'crypto', 'elements', 'error',
                             'handlers', 'hashing', 'legacy_caching', 'proto',
                             'runtime', 'testing', 'vendor', 'web'):
                continue
            datas.append((str(item), f"streamlit/{item.name}"))

# ── 隐式导入 ────────────────────────────────────────────────────
hiddenimports = [
    'streamlit',
    'streamlit.web',
    'streamlit.web.bootstrap',
    'streamlit.runtime',
    'streamlit.runtime.scriptrunner',
    'streamlit.runtime.scriptrunner.magic_funcs',
    'streamlit.runtime.scriptrunner.script_runner',
    'streamlit.runtime.caching',
    'streamlit.runtime.caching.cache_data_api',
    'streamlit.runtime.caching.cache_resource_api',
    'streamlit.components',
    'streamlit.components.v1',
    'streamlit.web.server',
    'streamlit.web.server.server',
    'streamlit.web.cli',
    'streamlit.web.server.starlette',
    'streamlit.web.server.starlette.starlette_server',
    'streamlit.web.server.routes',
    'streamlit.web.server.app_discovery',
    'altair',
    'pydeck',
    'pyarrow',
    'openpyxl',
    'pandas',
    'numpy',
    'openai',
    'docx',
    'lxml',
    'lxml._elementpath',
    'lxml.etree',
    'PIL',
    'click',
    'tornado',
    'tornado.platform',
    'tornado.platform.asyncio',
    'watchdog',
    'watchdog.observers',
    'watchdog.observers.read_directory_changes',
    'yaml',
    'jsonschema',
    'pydantic',
    'pydantic_core',
    'httpx',
    'anyio',
    'sniffio',
    'h11',
    'httpcore',
    'starlette',
    'jinja2',
    'importlib.metadata',
    'importlib_resources',
    'email.mime.multipart',
    'email.mime.text',
    'st_tui_editor',
    'st_tui_editor.editor',
    'st_tui_editor.components',
]

excludes = [
    'matplotlib', 'tkinter', 'scipy', 'IPython', 'notebook',
    'pytest', 'sphinx', 'unittest', 'lib2to3',
]

# ── Analysis ────────────────────────────────────────────────────
a = Analysis(
    [str(PROJECT_ROOT / 'launcher.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI分镜工坊',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(PROJECT_ROOT / 'ScriptMaster.ico'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI分镜工坊',
)

# 📦 打包完成后，将使用说明.md 复制到 dist 目录
if (PROJECT_ROOT / "dist_readme" / "使用说明.md").exists():
    dist_path = PROJECT_ROOT / "dist" / "AI分镜工坊"
    dist_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(PROJECT_ROOT / "dist_readme" / "使用说明.md"),
                str(dist_path / "使用说明.md"))
    print("✅ 已将 使用说明.md 复制到 dist/AI分镜工坊 目录")
