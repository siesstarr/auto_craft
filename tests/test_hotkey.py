"""
热键功能测试
测试热键配置、录制等功能
"""

import pytest
from unittest.mock import MagicMock, patch
from tests.test_utils import ConfigManager, create_mock_event


class TestHotkeyConfiguration:
    """热键配置功能测试"""

    def test_hotkey_validation(self, temp_config_dir):
        """测试热键验证功能"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config("F8", "F9")

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试有效热键
        assert gui._is_valid_hotkey("F8")
        assert gui._is_valid_hotkey("A")
        assert gui._is_valid_hotkey("1")
        assert gui._is_valid_hotkey("Space")

        # 测试无效热键
        assert not gui._is_valid_hotkey("我")
        assert not gui._is_valid_hotkey("")
        assert not gui._is_valid_hotkey("无效键")

    def test_default_hotkeys_setting(self, temp_config_dir):
        """测试默认热键设置"""
        from main import MainGUI, Config

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config("无效键", "无效键")

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 保存原始热键值
        original_start = gui.start_hotkey
        original_stop = gui.stop_hotkey

        # 设置无效热键
        gui.start_hotkey = "我"
        gui.stop_hotkey = "无效键"

        # 调用设置默认热键方法
        gui._set_default_hotkeys()

        # 验证是否设置为默认值
        assert gui.start_hotkey == Config.DEFAULT_START_HOTKEY
        assert gui.stop_hotkey == Config.DEFAULT_STOP_HOTKEY

        # 恢复原始值
        gui.start_hotkey = original_start
        gui.stop_hotkey = original_stop

    def test_hotkey_config_loading(self, temp_config_dir):
        """测试热键配置加载"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config("F5", "F6")

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 验证热键是否正确加载
        assert gui.start_hotkey == "F5"
        assert gui.stop_hotkey == "F6"

    def test_hotkey_config_saving(self, temp_config_dir):
        """测试热键配置保存"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config("F8", "F9")

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 修改热键
        gui.start_hotkey = "F10"
        gui.stop_hotkey = "F11"

        # 保存配置
        gui._save_hotkey_config()

        # 验证配置文件是否更新
        import json

        with open(
            config_manager.hotkey_config_path, 'r', encoding='utf-8'
        ) as f:
            saved_config = json.load(f)

        assert saved_config["start_hotkey"] == "F10"
        assert saved_config["stop_hotkey"] == "F11"


class TestHotkeyRecording:
    """热键录制功能测试"""

    def test_hotkey_recording_start(self, temp_config_dir):
        """测试热键录制开始"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config()

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 创建模拟的Entry对象
        mock_entry = MagicMock()
        mock_var = MagicMock()

        # 开始录制
        gui._start_hotkey_recording(mock_entry, mock_var, "开始")

        # 验证录制状态
        assert hasattr(gui, '_recording_entry')
        assert hasattr(gui, '_recording_var')
        assert hasattr(gui, '_recording_action')
        assert gui._recording_action == "开始"

    def test_hotkey_recording_cancel(self, temp_config_dir):
        """测试热键录制取消"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config()

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 创建模拟的Entry对象
        mock_entry = MagicMock()
        mock_var = MagicMock()

        # 开始录制
        gui._start_hotkey_recording(mock_entry, mock_var, "开始")

        # 测试ESC键取消
        mock_event = create_mock_event("Escape")
        result = gui._on_key_pressed(mock_event)

        # 验证录制状态已清理
        assert result == "break"
        assert not hasattr(gui, '_recording_entry')

    def test_hotkey_recording_finish(self, temp_config_dir):
        """测试热键录制完成"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config()

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 创建模拟的Entry对象
        mock_entry = MagicMock()
        mock_entry.configure = MagicMock()
        mock_entry.delete = MagicMock()
        mock_entry.insert = MagicMock()
        mock_entry.focus_force = MagicMock()

        # 开始录制
        gui._start_hotkey_recording(mock_entry, gui.start_hotkey_var, "开始")

        # 测试按键处理
        mock_event = create_mock_event("F10")
        result = gui._on_key_pressed(mock_event)

        # 验证录制完成
        assert result == "break"
        # 验证开始热键变量是否被设置
        assert gui.start_hotkey_var.get() == "F10"

    def test_hotkey_recording_cleanup(self, temp_config_dir):
        """测试热键录制清理"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config()

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 创建模拟的Entry对象
        mock_entry = MagicMock()
        mock_var = MagicMock()

        # 开始录制
        gui._start_hotkey_recording(mock_entry, mock_var, "开始")

        # 清理录制状态
        gui._cleanup_recording()

        # 验证录制状态已清理
        assert not hasattr(gui, '_recording_entry')
        assert not hasattr(gui, '_recording_var')
        assert not hasattr(gui, '_recording_action')


class TestHotkeyIntegration:
    """热键集成功能测试"""

    def test_hotkey_workflow(self, temp_config_dir):
        """测试热键完整工作流程"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_hotkey_config()

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试热键设置和应用
        original_start = gui.start_hotkey
        original_stop = gui.stop_hotkey

        # 模拟用户设置新的热键
        gui.start_hotkey_var.set("F5")
        gui.stop_hotkey_var.set("F6")

        # 应用热键设置 - 模拟消息框
        with patch('tkinter.messagebox.showinfo'):
            gui._apply_hotkey_settings()

        # 验证热键是否被更新
        assert gui.start_hotkey == "F5"
        assert gui.stop_hotkey == "F6"

        # 恢复原始值
        gui.start_hotkey = original_start
        gui.stop_hotkey = original_stop
        gui.start_hotkey_var.set(original_start)
        gui.stop_hotkey_var.set(original_stop)

        # 再次应用设置 - 模拟消息框
        with patch('tkinter.messagebox.showinfo'):
            gui._apply_hotkey_settings()


class TestHotkeyValidationEdge:
    """热键设置边界校验"""

    def test_hotkey_conflict_same_keys(self, temp_config_dir):
        from main import MainGUI
        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)
        gui.start_hotkey_var.set("F8")
        gui.stop_hotkey_var.set("F8")

        # 执行应用设置（冲突应被拒绝）
        with patch('tkinter.messagebox.showwarning'):
            gui._apply_hotkey_settings()
        # 内部热键不应被更新为冲突值
        assert not (gui.start_hotkey == "F8" and gui.stop_hotkey == "F8")

    def test_hotkey_empty_invalid(self, temp_config_dir):
        from main import MainGUI
        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)
        original_start, original_stop = gui.start_hotkey, gui.stop_hotkey
        gui.start_hotkey_var.set("")
        gui.stop_hotkey_var.set("")

        with patch('tkinter.messagebox.showwarning'):
            gui._apply_hotkey_settings()
        # 未通过校验，应保持原值
        assert gui.start_hotkey == original_start
        assert gui.stop_hotkey == original_stop


class TestGlobalHotkeyListener:
    """覆盖pynput监听启动/停止和异常路径"""

    def test_start_and_stop_listener(self, temp_config_dir, monkeypatch):
        from main import MainGUI
        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")
        gui = MainGUI(test_root)

        # 模拟pynput Listener
        class DummyListener:
            def __init__(self, *args, **kwargs):
                self.started = False

            def start(self):
                self.started = True

            def stop(self):
                self.started = False

        import pynput.keyboard as pk

        monkeypatch.setattr(pk, 'Listener', DummyListener)

        gui._start_hotkey_listening()
        assert gui._hotkey_listening

        gui._stop_hotkey_listening()
        assert not gui._hotkey_listening

    def test_listener_exception_path(self, temp_config_dir, monkeypatch):
        from main import MainGUI
        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")
        gui = MainGUI(test_root)

        # 使Listener构造抛异常
        import pynput.keyboard as pk

        def raise_err(*args, **kwargs):
            raise RuntimeError('boom')

        monkeypatch.setattr(pk, 'Listener', raise_err)

        # 启动不应抛出到测试层
        gui._start_hotkey_listening()
