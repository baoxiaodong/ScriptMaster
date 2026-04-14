"""
AI分镜生成器 - 运行时钩子
修复 PyInstaller 打包后 importlib.metadata 找不到包元数据的问题
"""
import sys
import os

def _patch_metadata_paths():
    """让 importlib.metadata 能找到打包进来的 dist-info"""
    try:
        import importlib.metadata as _md
        
        # 在 PyInstaller 打包环境中，_MEIPASS 是 _internal 目录
        base = getattr(sys, '_MEIPASS', '')
        if not base:
            return
        
        # 获取原有的 search_paths
        try:
            original_distributions = _md.packages_distributions
        except AttributeError:
            pass
        
        # Monkey-patch distribution() 使其能搜索 _internal 下的 dist-info
        _original_distribution = _md.distribution
        
        def _patched_distribution(name):
            try:
                return _original_distribution(name)
            except _md.PackageNotFoundError:
                # 在 _internal 目录下搜索
                name_norm = name.replace('_', '-').lower()
                for entry in os.listdir(base):
                    entry_lower = entry.lower()
                    if entry_lower.endswith('.dist-info') and entry_lower.startswith(name_norm):
                        dist_info_path = os.path.join(base, entry)
                        # 创建一个简单的 Distribution 对象
                        try:
                            from email.parser import Parser
                            metadata_file = os.path.join(dist_info_path, 'METADATA')
                            if os.path.exists(metadata_file):
                                return _PatchDistribution(name, dist_info_path)
                        except Exception:
                            pass
                raise _md.PackageNotFoundError(name)
        
        _md.distribution = _patched_distribution
        
        # 同样 patch metadata() 函数
        _original_metadata = _md.metadata
        
        def _patched_metadata(name):
            try:
                return _original_metadata(name)
            except _md.PackageNotFoundError:
                dist = _patched_distribution(name)
                return dist.metadata
        
        _md.metadata = _patched_metadata
        
        # patch version() 函数
        _original_version = _md.version
        
        def _patched_version(name):
            try:
                return _original_version(name)
            except _md.PackageNotFoundError:
                dist = _patched_distribution(name)
                return dist.version
        
        _md.version = _patched_version
        
    except Exception:
        pass


class _PatchDistribution:
    """简易 Distribution 替代，从 dist-info 目录读取元数据"""
    def __init__(self, name, dist_info_path):
        self.name = name
        self._path = dist_info_path
        self._metadata = None
        self._version = None
    
    @property
    def metadata(self):
        if self._metadata is None:
            from email.parser import Parser
            meta_file = os.path.join(self._path, 'METADATA')
            if os.path.exists(meta_file):
                with open(meta_file, 'r', encoding='utf-8') as f:
                    self._metadata = Parser().parse(f)
            else:
                self._metadata = {}
        return self._metadata
    
    @property
    def version(self):
        if self._version is None:
            if isinstance(self.metadata, dict):
                self._version = self.metadata.get('Version', '0.0.0')
            else:
                self._version = self.metadata.get('Version', '0.0.0')
        return self._version


_patch_metadata_paths()
