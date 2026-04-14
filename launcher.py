"""
AI分镜生成器 - EXE启动器
双击运行后自动启动Streamlit服务并打开浏览器
"""
import os
import sys
import time
import socket
import webbrowser
import threading
from pathlib import Path


# ══════════════════════════════════════════════════════════════════
# ★ PyInstaller 兼容层：patch importlib.metadata
# ══════════════════════════════════════════════════════════════════
def _patch_importlib_metadata():
    import importlib.metadata as _md

    _KNOWN_VERSIONS = {
        'streamlit': '1.56.0',
        'altair': '5.5.0',
        'pandas': '2.3.0',
        'numpy': '2.2.6',
        'pyarrow': '23.0.1',
        'pydeck': '0.9.1',
        'openpyxl': '3.1.5',
        'tornado': '6.5.1',
        'click': '8.2.1',
        'pillow': '11.3.0',
        'python-dateutil': '2.9.0.post0',
        'pytz': '2025.2',
        'requests': '2.32.4',
        'urllib3': '2.4.0',
        'certifi': '2025.4.26',
        'charset-normalizer': '3.4.2',
        'idna': '3.10',
        'jinja2': '3.1.6',
        'markupsafe': '3.0.2',
        'packaging': '25.0',
        'pydantic': '2.12.5',
        'pydantic-core': '2.33.2',
        'openai': '2.30.0',
        'httpx': '0.28.1',
        'httpcore': '1.0.9',
        'anyio': '4.9.0',
        'sniffio': '1.3.1',
        'h11': '0.16.0',
        'starlette': '0.47.1',
        'jsonschema': '4.24.0',
        'lxml': '5.4.0',
        'python-docx': '1.1.2',
        'tenacity': '9.1.2',
        'watchdog': '6.0.0',
        'tqdm': '4.67.1',
        'blinker': '1.9.0',
        'rich': '14.0.0',
        'pygments': '2.19.1',
        'typing-extensions': '4.14.0',
        'narwhals': '1.40.0',
        'protobuf': '6.31.0',
        'fsspec': '2025.3.2',
        'referencing': '0.36.2',
        'rpds-py': '0.25.1',
        'jsonschema-specifications': '2025.4.1',
        'cachetools': '5.5.2',
        'annotated-types': '0.7.0',
        'gitdb': '4.0.12',
        'gitpython': '3.1.44',
        'smmap': '5.0.2',
        'pydantic-extra-types': '2.10.2',
        'setuptools': '80.0.0',
        'wheel': '0.45.1',
    }

    def _norm(name):
        return name.replace('_', '-').lower()

    _version_map = {_norm(k): v for k, v in _KNOWN_VERSIONS.items()}
    _orig_version = _md.version
    _orig_distribution = getattr(_md, 'distribution', None)
    _orig_metadata_fn = getattr(_md, 'metadata', None)

    def _patched_version(name):
        try:
            return _orig_version(name)
        except _md.PackageNotFoundError:
            key = _norm(name)
            if key in _version_map:
                return _version_map[key]
            raise

    def _patched_distribution(name):
        try:
            if _orig_distribution:
                return _orig_distribution(name)
        except (_md.PackageNotFoundError, Exception):
            pass
        key = _norm(name)
        if key in _version_map:
            return _FakeDistribution(name, _version_map[key])
        raise _md.PackageNotFoundError(name)

    def _patched_metadata(name):
        try:
            if _orig_metadata_fn:
                return _orig_metadata_fn(name)
        except (_md.PackageNotFoundError, Exception):
            pass
        key = _norm(name)
        if key in _version_map:
            return _FakeMetadata(name, _version_map[key])
        raise _md.PackageNotFoundError(name)

    _md.version = _patched_version
    if _orig_distribution:
        _md.distribution = _patched_distribution
    if _orig_metadata_fn:
        _md.metadata = _patched_metadata


class _FakeDistribution:
    def __init__(self, name, version):
        self.metadata = _FakeMetadata(name, version)
        self.version = version
        self.name = name


class _FakeMetadata(dict):
    def __init__(self, name, version):
        super().__init__()
        self._name = name
        self._version = version

    def get(self, key, default=None):
        if key == 'Name': return self._name
        if key == 'Version': return self._version
        return default

    def __getitem__(self, key):
        if key == 'Name': return self._name
        if key == 'Version': return self._version
        return super().__getitem__(key)


_patch_importlib_metadata()


# ══════════════════════════════════════════════════════════════════
# 启动逻辑
# ══════════════════════════════════════════════════════════════════

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_for_server(port, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    # ── 确定路径 ────────────────────────────────────────────────
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys._MEIPASS)
        project_root = app_dir / "app"
    else:
        project_root = Path(__file__).parent

    # ── 找到入口脚本 ────────────────────────────────────────────
    main_script = project_root / "main.py"
    if not main_script.exists():
        print("[X] Cannot find main.py: %s" % main_script)
        input("Press Enter to exit...")
        sys.exit(1)

    # ── 写入 Streamlit 配置 ──────────────────────────────────────
    config_dir = project_root / ".streamlit"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.toml").write_text(
        "[browser]\n"
        "gatherUsageStats = false\n"
        "serverAddress = 'localhost'\n"
        "\n"
        "[server]\n"
        "headless = true\n"
        "enableCORS = true\n"
        "enableXsrfProtection = false\n"
        "maxUploadSize = 200\n"
        "\n"
        "[client]\n"
        "showErrorDetails = false\n"
        "toolbarMode = 'minimal'\n",
        encoding='utf-8'
    )

    # ── 寻找可用端口 ────────────────────────────────────────────
    port = find_free_port()
    url = "http://localhost:%d" % port

    print("=" * 56)
    print("   AI Fenjing Generator  Starting...")
    print("=" * 56)
    print("   URL: %s" % url)
    print("   Close this window to exit")
    print("=" * 56)

    # ── 延迟打开浏览器 ──────────────────────────────────────────
    def open_browser():
        if wait_for_server(port, timeout=30):
            webbrowser.open(url)
        else:
            print("[!] Server timeout, open browser manually")

    threading.Thread(target=open_browser, daemon=True).start()

    # ── 启动 Streamlit ─────────────────────────────────────────
    try:
        # 通过 streamlit config API 设置端口，确保生效
        from streamlit import config as st_config
        st_config.set_option("server.port", port)
        st_config.set_option("server.headless", True)
        st_config.set_option("browser.gatherUsageStats", False)
        st_config.set_option("global.developmentMode", False)

        from streamlit.web import bootstrap

        os.chdir(str(project_root))

        # bootstrap.run: args 是传给用户脚本的, flag_options 是 streamlit 配置
        bootstrap.run(str(main_script), False, [], {})

    except Exception as e:
        print("\n[X] Startup failed: %s" % e)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
