"""
调试系统测试
测试调试输出功能
"""

import logging
from unittest.mock import patch
from tests.test_utils import ConfigManager


class TestDebugSystem:
    """调试系统功能测试"""

    def test_debug_system_initialization(self, temp_config_dir):
        """测试调试系统初始化"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 测试调试系统是否正确初始化
            assert hasattr(gui, '_debug_print')
            assert callable(gui._debug_print)

    def test_debug_system_in_frozen_mode(self, temp_config_dir, monkeypatch):
        """测试打包态(sys.frozen)下的初始化分支"""
        from main import MainGUI
        from tests.test_utils import test_root

        if test_root is None:
            return
        # 模拟打包态
        import sys

        monkeypatch.setattr(sys, 'frozen', True, raising=False)
        gui = MainGUI(test_root)
        assert hasattr(gui, '_debug_print')

    def test_debug_print_functionality(self, temp_config_dir):
        """测试调试输出功能"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 测试不同级别的调试输出
            gui._debug_print("测试信息", logging.INFO)
            gui._debug_print("测试警告", logging.WARNING)
            gui._debug_print("测试错误", logging.ERROR)
            gui._debug_print("测试调试", logging.DEBUG)

    def test_debug_mode_toggle(self, temp_config_dir):
        """测试调试模式切换功能"""
        from main import MainGUI, Config

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 测试调试模式切换（如果存在debug_var）
            if hasattr(gui, 'debug_var'):
                # 关闭调试模式
                gui.debug_var.set(False)
                gui._toggle_debug_mode()
                assert not Config.DEBUG_MODE

                # 重新开启调试模式
                gui.debug_var.set(True)
                gui._toggle_debug_mode()
                assert Config.DEBUG_MODE


class TestDebugLogging:
    """调试日志功能测试"""

    def test_debug_logging_levels(self, temp_config_dir):
        """测试不同级别的调试日志"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 测试各种日志级别
            test_messages = [
                ("信息级别", logging.INFO),
                ("警告级别", logging.WARNING),
                ("错误级别", logging.ERROR),
                ("调试级别", logging.DEBUG),
            ]

            for message, level in test_messages:
                gui._debug_print(message, level)

    def test_debug_logging_integration(self, temp_config_dir):
        """测试调试日志与业务逻辑的集成"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 测试字段操作时的调试输出
            gui._add_field()
            gui._remove_field(0)

            # 测试保存操作时的调试输出
            gui.fields[0]["text"].set("test_field")
            gui._handle_save_click()
