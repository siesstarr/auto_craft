"""
测试配置文件
设置测试环境，确保测试的独立性和隔离性
"""

import pytest
import shutil
import tempfile
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """创建测试数据目录"""
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def temp_config_dir():
    """创建临时配置目录"""
    temp_dir = tempfile.mkdtemp(prefix="auto_craft_test_")
    yield temp_dir
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def setup_test_environment(temp_config_dir, monkeypatch):
    """设置测试环境，确保配置文件的隔离"""
    # 设置环境变量，指向临时配置目录
    monkeypatch.setenv("AUTO_CRAFT_CONFIG_DIR", temp_config_dir)

    # 设置Tkinter模拟
    import tkinter as tk

    # 创建真实的Tk实例用于测试
    root = tk.Tk()
    root.withdraw()  # 隐藏窗口

    # 提供root给测试使用
    monkeypatch.setattr("tests.test_utils.test_root", root)

    # 统一打桩 messagebox，防止在无窗口环境下崩溃
    import tkinter.messagebox as mb

    monkeypatch.setattr(mb, "showinfo", lambda *args, **kwargs: None)
    monkeypatch.setattr(mb, "showerror", lambda *args, **kwargs: None)
    monkeypatch.setattr(mb, "showwarning", lambda *args, **kwargs: None)

    yield

    for config_file in [
        Path(temp_config_dir) / "fields_config.json",
        Path(temp_config_dir) / "hotkey_config.json",
    ]:
        if config_file.exists():
            config_file.unlink()

    # 销毁Tk实例
    root.destroy()
