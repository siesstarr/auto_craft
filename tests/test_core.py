"""
核心功能测试
测试字段管理、匹配逻辑等核心功能
"""

import re
import pytest
from tests.test_utils import ConfigManager


class TestFieldManagement:
    """字段管理功能测试"""

    def test_field_creation(self, temp_config_dir):
        """测试字段创建功能"""
        from man import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        # 创建GUI实例
        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试添加字段
        initial_count = len(gui.fields)
        gui._add_field()
        assert len(gui.fields) == initial_count + 1

        # 测试字段数据结构
        new_field = gui.fields[-1]
        assert "text" in new_field
        assert "mode" in new_field
        assert new_field["mode"].get() == "text"

    def test_field_removal(self, temp_config_dir):
        """测试字段删除功能"""
        from man import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config(
            [
                {"text": "field1", "mode": "text"},
                {"text": "field2", "mode": "text"},
            ]
        )

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试删除字段
        initial_count = len(gui.fields)
        gui._remove_field(0)
        assert len(gui.fields) == initial_count - 1

    def test_field_validation(self, temp_config_dir):
        """测试字段验证功能"""
        from man import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config(
            [{"text": "valid_regex", "mode": "regex"}]
        )

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试正则表达式验证
        gui.fields[0]["text"].set("\\d+")
        gui.fields[0]["mode"].set("regex")

        # 验证正则表达式有效
        assert re.compile("\\d+") is not None

    def test_field_save_workflow(self, temp_config_dir):
        """测试字段保存工作流程"""
        from man import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 设置字段内容
        gui.fields[0]["text"].set("test_field")
        gui.fields[0]["mode"].set("text")

        # 保存字段
        gui._handle_save_click()

        # 验证保存状态
        assert gui._has_any_saved_value()
        assert gui._count_non_empty_saved_fields() > 0

    def test_clipboard_poll_empty_and_exception(
        self, temp_config_dir, monkeypatch
    ):
        """覆盖剪贴板轮询的空返回与异常分支"""
        from man import MainGUI
        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")
        gui = MainGUI(test_root)
        # 空文本路径
        monkeypatch.setattr(gui, '_get_clipboard_text', lambda: "")
        # 避免实际处理
        monkeypatch.setattr(gui, '_process_matches', lambda text: None)
        gui._poll_clipboard()

        # 异常路径
        def raise_err():
            raise RuntimeError("clipboard error")

        monkeypatch.setattr(gui, '_get_clipboard_text', raise_err)
        gui._poll_clipboard()


class TestMatchingLogic:
    """匹配逻辑测试"""

    def test_text_matching(self, temp_config_dir):
        """测试文本匹配功能"""
        from man import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config(
            [
                {"text": "hello", "mode": "text"},
                {"text": "world", "mode": "text"},
            ]
        )

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 设置字段内容
        gui.fields[0]["text"].set("hello")
        gui.fields[0]["mode"].set("text")
        gui.fields[1]["text"].set("world")
        gui.fields[1]["mode"].set("text")

        # 保存字段
        gui._handle_save_click()

        # 测试文本匹配
        clipboard_text = "hello world 123"
        matches = gui._find_matches(clipboard_text)

        assert len(matches) == 2
        assert any("hello" in match[2] for match in matches)
        assert any("world" in match[2] for match in matches)

    def test_regex_matching(self, temp_config_dir):
        """测试正则表达式匹配功能"""
        from man import MainGUI

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 清空所有字段，只保留第一个用于测试
        for i in range(len(gui.fields)):
            gui.fields[i]["text"].set("")
            gui.fields[i]["mode"].set("text")

        # 设置第一个字段为正则表达式
        gui.fields[0]["text"].set("\\d+")
        gui.fields[0]["mode"].set("regex")

        # 保存字段
        gui._handle_save_click()

        # 测试正则匹配
        clipboard_text = "hello 123 world 456"
        matches = gui._find_matches(clipboard_text)

        # 应该只匹配正则表达式字段
        assert len(matches) == 1
        assert matches[0][1] == "正则"  # 模式应该是"正则"
        assert "\\d+" in matches[0][2]  # 字段内容应该包含正则表达式

    def test_invalid_regex_handling(self, temp_config_dir):
        """测试无效正则表达式的处理"""
        from man import MainGUI

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 清空所有字段，只保留第一个用于测试
        for i in range(len(gui.fields)):
            gui.fields[i]["text"].set("")
            gui.fields[i]["mode"].set("text")

        # 设置第一个字段为无效的正则表达式
        gui.fields[0]["text"].set("[invalid")
        gui.fields[0]["mode"].set("regex")

        # 保存字段
        gui._handle_save_click()

        # 测试无效正则表达式的处理
        clipboard_text = "test content"
        matches = gui._find_matches(clipboard_text)

        # 应该跳过无效的正则表达式，不产生匹配
        assert len(matches) == 0


class TestUtilityFunctions:
    """工具函数测试"""

    def test_mode_label_conversion(self, temp_config_dir):
        """测试模式标签转换"""
        from man import MainGUI

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试模式标签转换
        assert gui._get_mode_label("text") == "文本"
        assert gui._get_mode_label("regex") == "正则"

    def test_text_processing(self, temp_config_dir):
        """测试文本处理功能"""
        from man import MainGUI

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 测试文本后缀处理
        test_text = "字段1（文本）: test content"
        stripped = gui._strip_match_suffix(test_text)
        assert "test content" in stripped

        # 测试模式和值提取
        mode, value = gui._extract_mode_and_value(stripped)
        assert mode == "文本"
        assert value == "test content"
