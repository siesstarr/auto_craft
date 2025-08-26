"""
核心功能测试 - 重构后版本
测试字段管理、匹配逻辑等核心功能
"""

import pytest
import tkinter as tk
from core import (
    FieldManager,
    MatchEngine,
    ConfigManager,
    DebugSystem,
    Config,
    ClipboardManager,
    HotkeyManager,
    NotificationManager,
)


class TestFieldManager:
    """字段管理器测试"""

    def test_field_creation(self):
        """测试字段创建功能"""
        field_manager = FieldManager()

        initial_count = field_manager.get_field_count()
        text_var = tk.StringVar()
        mode_var = tk.StringVar(value="text")

        result = field_manager.add_field(text_var, mode_var)
        assert result is True
        assert field_manager.get_field_count() == initial_count + 1

    def test_field_removal(self):
        """测试字段删除功能"""
        field_manager = FieldManager()

        # 添加多个字段
        for i in range(3):
            text_var = tk.StringVar()
            mode_var = tk.StringVar(value="text")
            field_manager.add_field(text_var, mode_var)

        initial_count = field_manager.get_field_count()

        # 删除字段
        result = field_manager.remove_field(0)
        assert result is True
        assert field_manager.get_field_count() == initial_count - 1

    def test_field_limits(self):
        """测试字段数量限制"""
        field_manager = FieldManager()

        # 测试字段添加（无上限限制）
        assert field_manager.can_add_field() is True

        # 添加多个字段验证无上限
        for i in range(25):  # 添加超过原来20个限制的字段
            text_var = tk.StringVar()
            mode_var = tk.StringVar(value="text")
            field_manager.add_field(text_var, mode_var)

        # 验证仍然可以添加
        assert field_manager.can_add_field() is True
        assert field_manager.get_field_count() == 25

        # 测试最小字段限制
        # 当只有一个字段时不能删除
        field_manager_min = FieldManager()
        text_var = tk.StringVar()
        mode_var = tk.StringVar(value="text")
        field_manager_min.add_field(text_var, mode_var)

        assert field_manager_min.can_remove_field() is False


class TestMatchEngine:
    """匹配引擎测试"""

    def test_text_matching(self):
        """测试纯文本匹配"""
        field_manager = FieldManager()
        match_engine = MatchEngine(field_manager)

        # 创建测试字段
        text_var = tk.StringVar(value="test")
        mode_var = tk.StringVar(value="text")
        field_manager.add_field(text_var, mode_var)

        # 创建保存显示变量
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段1（文本）: test")
        )

        # 测试匹配
        matches = match_engine.find_matches("this is a test string")
        assert len(matches) == 1
        assert matches[0][2] == "test"

    def test_regex_matching(self):
        """测试正则表达式匹配"""
        field_manager = FieldManager()
        match_engine = MatchEngine(field_manager)

        # 创建测试字段
        text_var = tk.StringVar(value=r"\d+")
        mode_var = tk.StringVar(value="regex")
        field_manager.add_field(text_var, mode_var)

        # 创建保存显示变量
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段1（正则）: \\d+")
        )

        # 测试匹配
        matches = match_engine.find_matches("test 123 string")
        assert len(matches) == 1

    def test_process_single_match(self):
        """测试单条匹配模式"""
        field_manager = FieldManager()
        match_engine = MatchEngine(field_manager)

        # 创建测试字段
        text_var = tk.StringVar(value="hello")
        mode_var = tk.StringVar(value="text")
        field_manager.add_field(text_var, mode_var)

        # 创建保存显示变量
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段1（文本）: hello")
        )

        # 测试单条匹配
        is_match, match_text = match_engine.process_matches(
            "hello world", "single"
        )
        assert is_match is True
        assert "hello" in match_text

    def test_process_all_match(self):
        """测试全部匹配模式"""
        field_manager = FieldManager()
        match_engine = MatchEngine(field_manager)

        # 创建两个测试字段
        text_var1 = tk.StringVar(value="hello")
        mode_var1 = tk.StringVar(value="text")
        field_manager.add_field(text_var1, mode_var1)

        text_var2 = tk.StringVar(value="world")
        mode_var2 = tk.StringVar(value="text")
        field_manager.add_field(text_var2, mode_var2)

        # 创建保存显示变量
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段1（文本）: hello")
        )
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段2（文本）: world")
        )

        # 测试全部匹配
        is_match, match_text = match_engine.process_matches(
            "hello world", "all"
        )
        assert is_match is True
        assert "hello" in match_text and "world" in match_text


class TestConfigManager:
    """配置管理器测试"""

    def test_load_empty_config(self):
        """测试加载空配置"""
        fields_data = ConfigManager.load_fields_config()
        # 当配置文件不存在时应返回空列表
        assert isinstance(fields_data, list)

    def test_save_fields_config(self):
        """测试保存字段配置"""
        # 创建测试字段数据
        test_fields = [
            {
                "text": tk.StringVar(value="test1"),
                "mode": tk.StringVar(value="text"),
            },
            {
                "text": tk.StringVar(value="test2"),
                "mode": tk.StringVar(value="regex"),
            },
        ]

        # 测试保存
        result = ConfigManager.save_fields_config(test_fields)
        assert result is True


class TestDebugSystem:
    """调试系统测试"""

    def test_debug_system_setup(self):
        """测试调试系统设置"""
        # 测试调试系统设置不抛出异常
        try:
            DebugSystem.setup_debug_system()
            assert True
        except Exception:
            pytest.fail("调试系统设置失败")

    def test_debug_print(self):
        """测试调试输出"""
        # 测试调试输出不抛出异常
        try:
            DebugSystem.debug_print("测试消息")
            assert True
        except Exception:
            pytest.fail("调试输出失败")


class TestConfig:
    """配置类测试"""

    def test_config_constants(self):
        """测试配置常量"""
        assert Config.WINDOW_WIDTH > 0
        assert Config.WINDOW_HEIGHT > 0
        assert Config.MIN_FIELDS >= 1
        assert Config.CLIPBOARD_POLL_MS > 0

    def test_config_paths(self):
        """测试配置路径方法"""
        config_dir = Config.get_config_dir()
        assert isinstance(config_dir, str)

        config_file_path = Config.get_config_file_path("test.json")
        assert "test.json" in config_file_path


class TestClipboardManager:
    """剪贴板管理器测试"""

    def test_clipboard_manager_init(self):
        """测试剪贴板管理器初始化"""
        root = tk.Tk()
        try:
            clipboard_manager = ClipboardManager(root)
            assert clipboard_manager.root == root
            assert not clipboard_manager.is_listening()
        finally:
            root.destroy()

    def test_clipboard_listening_states(self):
        """测试剪贴板监听状态"""
        root = tk.Tk()
        try:
            clipboard_manager = ClipboardManager(root)

            # 初始状态
            assert not clipboard_manager.is_listening()

            # 开始监听
            result = clipboard_manager.start_listening()
            assert result is True
            assert clipboard_manager.is_listening()

            # 停止监听
            result = clipboard_manager.stop_listening()
            assert result is True
            assert not clipboard_manager.is_listening()
        finally:
            root.destroy()


class TestHotkeyManager:
    """热键管理器测试"""

    def test_hotkey_manager_init(self):
        """测试热键管理器初始化"""
        root = tk.Tk()
        try:
            hotkey_manager = HotkeyManager(root)
            assert hotkey_manager.root == root
            assert hotkey_manager.start_hotkey == Config.DEFAULT_START_HOTKEY
            assert hotkey_manager.stop_hotkey == Config.DEFAULT_STOP_HOTKEY
        finally:
            root.destroy()

    def test_hotkey_validation(self):
        """测试热键验证"""
        root = tk.Tk()
        try:
            hotkey_manager = HotkeyManager(root)

            # 测试有效热键
            assert hotkey_manager._is_valid_hotkey("F8") is True
            assert hotkey_manager._is_valid_hotkey("F9") is True
            assert hotkey_manager._is_valid_hotkey("A") is True

            # 测试无效热键
            assert hotkey_manager._is_valid_hotkey("") is False
            assert hotkey_manager._is_valid_hotkey(None) is False
            assert hotkey_manager._is_valid_hotkey("INVALID") is False
        finally:
            root.destroy()

    def test_hotkey_config_loading(self):
        """测试热键配置加载"""
        root = tk.Tk()
        try:
            hotkey_manager = HotkeyManager(root)
            # 测试加载配置不抛异常
            hotkey_manager.load_config()
            assert True
        finally:
            root.destroy()


class TestNotificationManager:
    """通知管理器测试"""

    def test_notification_manager_init(self):
        """测试通知管理器初始化"""
        root = tk.Tk()
        try:
            notification_manager = NotificationManager(root)
            assert notification_manager.root == root
        finally:
            root.destroy()

    def test_notify_match(self):
        """测试匹配通知"""
        root = tk.Tk()
        try:
            notification_manager = NotificationManager(root)
            # 测试通知不抛异常
            notification_manager.notify_match("测试匹配")
            assert True
        finally:
            root.destroy()


class TestIntegration:
    """集成测试"""

    def test_field_manager_with_match_engine_integration(self):
        """测试字段管理器与匹配引擎集成"""
        field_manager = FieldManager()
        match_engine = MatchEngine(field_manager)

        # 添加测试字段
        text_var = tk.StringVar(value="hello")
        mode_var = tk.StringVar(value="text")
        field_manager.add_field(text_var, mode_var)

        # 创建保存显示变量
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段1（文本）: hello")
        )

        # 测试集成匹配
        assert match_engine.has_any_saved_value() is True
        matches = match_engine.find_matches("hello world")
        assert len(matches) == 1

    def test_match_engine_edge_cases(self):
        """测试匹配引擎边界情况"""
        field_manager = FieldManager()
        match_engine = MatchEngine(field_manager)

        # 测试空字段列表
        assert match_engine.has_any_saved_value() is False
        matches = match_engine.find_matches("test")
        assert len(matches) == 0

        # 测试无效正则表达式
        field_manager.saved_display_vars.append(
            tk.StringVar(value="字段1（正则）: [invalid")
        )
        matches = match_engine.find_matches("test content")
        assert len(matches) == 0  # 无效正则应该被跳过

        # 测试匹配后缀处理
        test_text = "字段1（文本）: test [匹配]"
        stripped = match_engine._strip_match_suffix(test_text)
        assert "[匹配]" not in stripped

    def test_config_manager_error_handling(self):
        """测试配置管理器错误处理"""
        # 测试加载不存在的配置文件
        fields_data = ConfigManager.load_fields_config()
        assert isinstance(fields_data, list)

        # 测试加载热键配置
        hotkey_config = ConfigManager.load_hotkey_config()
        assert isinstance(hotkey_config, dict)

        # 测试保存热键配置
        result = ConfigManager.save_hotkey_config("F10", "F11")
        assert result is True

    def test_debug_system_with_different_levels(self):
        """测试不同级别的调试输出"""
        import logging

        # 测试不同级别的调试输出
        DebugSystem.debug_print("INFO消息", logging.INFO)
        DebugSystem.debug_print("WARNING消息", logging.WARNING)
        DebugSystem.debug_print("ERROR消息", logging.ERROR)
        DebugSystem.debug_print("DEBUG消息", logging.DEBUG)

        # 所有调用都应该正常执行
        assert True
