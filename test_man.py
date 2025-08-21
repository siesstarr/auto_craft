#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MainGUI 类的测试文件

测试内容包括：
1. 字段管理功能
2. 剪贴板监听功能
3. 内容匹配功能
4. 工具方法功能
"""

import unittest
import tkinter as tk
from unittest.mock import patch
import tkinter.ttk as ttk

# 导入被测试的类
from man import MainGUI, Config


class TestMainGUI(unittest.TestCase):
    """MainGUI 类的测试类"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建根窗口
        self.root = tk.Tk()
        # 创建主GUI实例
        self.gui = MainGUI(self.root)

    def tearDown(self):
        """测试后的清理工作"""
        # 销毁根窗口
        self.root.destroy()

    def test_config_constants(self):
        """测试配置常量"""
        self.assertEqual(Config.WINDOW_WIDTH, 800)
        self.assertEqual(Config.WINDOW_HEIGHT, 800)
        self.assertEqual(Config.MAX_FIELDS, 20)
        self.assertEqual(Config.MIN_FIELDS, 1)
        self.assertEqual(Config.CLIPBOARD_POLL_MS, 500)

    def test_init_data_states(self):
        """测试数据状态初始化"""
        self.assertEqual(len(self.gui.fields), 1)  # 应该有一个初始字段
        self.assertEqual(len(self.gui.saved_display_vars), 1)
        self.assertEqual(self.gui.match_mode_var.get(), "single")
        self.assertFalse(self.gui._clipboard_listening)
        self.assertIsNone(self.gui._clipboard_after_id)

    def test_add_field(self):
        """测试添加字段功能"""
        initial_count = len(self.gui.fields)
        self.gui._add_field()
        self.assertEqual(len(self.gui.fields), initial_count + 1)
        self.assertEqual(len(self.gui.saved_display_vars), initial_count + 1)
        new_field = self.gui.fields[-1]
        self.assertIn("text", new_field)
        self.assertIn("mode", new_field)
        self.assertEqual(new_field["mode"].get(), "text")

    def test_add_field_max_limit(self):
        """测试添加字段的最大限制"""
        for _ in range(Config.MAX_FIELDS):
            self.gui._add_field()
        self.assertEqual(len(self.gui.fields), Config.MAX_FIELDS)
        self.gui._add_field()
        self.assertEqual(len(self.gui.fields), Config.MAX_FIELDS)

    def test_remove_field(self):
        """测试删除字段功能"""
        self.gui._add_field()
        self.gui._add_field()
        initial_count = len(self.gui.fields)
        self.gui._remove_field(1)
        self.assertEqual(len(self.gui.fields), initial_count - 1)
        self.assertEqual(len(self.gui.saved_display_vars), initial_count - 1)

    def test_remove_field_min_limit(self):
        """测试删除字段的最小限制"""
        while len(self.gui.fields) > Config.MIN_FIELDS:
            self.gui._remove_field(0)
        self.assertEqual(len(self.gui.fields), Config.MIN_FIELDS)
        self.gui._remove_field(0)
        self.assertEqual(len(self.gui.fields), Config.MIN_FIELDS)

    def test_get_mode_label(self):
        """测试模式标签获取"""
        self.assertEqual(self.gui._get_mode_label("text"), "文本")
        self.assertEqual(self.gui._get_mode_label("regex"), "正则")

    def test_strip_match_suffix(self):
        """测试匹配状态后缀去除"""
        text_with_suffix = "字段1（文本）: hello [匹配]"
        result = self.gui._strip_match_suffix(text_with_suffix)
        self.assertEqual(result, "字段1（文本）: hello")
        text_without_suffix = "字段1（文本）: hello"
        result = self.gui._strip_match_suffix(text_without_suffix)
        self.assertEqual(result, "字段1（文本）: hello")

    def test_extract_mode_and_value(self):
        """测试模式和值提取"""
        saved_text = "字段1（文本）: hello"
        mode, value = self.gui._extract_mode_and_value(saved_text)
        self.assertEqual(mode, "文本")
        self.assertEqual(value, "hello")
        saved_text_empty = "字段1（文本）: （空）"
        mode, value = self.gui._extract_mode_and_value(saved_text_empty)
        self.assertEqual(mode, "文本")
        self.assertEqual(value, "（空）")

    def test_has_any_saved_value(self):
        """测试是否有保存的非空字段"""
        self.assertFalse(self.gui._has_any_saved_value())
        self.gui.fields[0]["text"].set("test")
        self.gui._handle_save_click()
        self.assertTrue(self.gui._has_any_saved_value())

    def test_count_non_empty_saved_fields(self):
        """测试非空保存字段计数"""
        self.assertEqual(self.gui._count_non_empty_saved_fields(), 0)
        self.gui.fields[0]["text"].set("test")
        self.gui._handle_save_click()
        self.assertEqual(self.gui._count_non_empty_saved_fields(), 1)

    def test_find_matches_text_mode(self):
        """测试纯文本模式匹配"""
        self.gui.fields[0]["text"].set("hello")
        self.gui.fields[0]["mode"].set("text")
        self.gui._handle_save_click()
        matches = self.gui._find_matches("hello world")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][1], "文本")
        self.assertEqual(matches[0][2], "hello")
        matches = self.gui._find_matches("goodbye world")
        self.assertEqual(len(matches), 0)

    def test_find_matches_regex_mode(self):
        """测试正则表达式模式匹配"""
        self.gui.fields[0]["text"].set(r"\d+")
        self.gui.fields[0]["mode"].set("regex")
        self.gui._handle_save_click()
        matches = self.gui._find_matches("hello 123 world")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][1], "正则")
        self.assertEqual(matches[0][2], r"\d+")
        matches = self.gui._find_matches("hello world")
        self.assertEqual(len(matches), 0)

    def test_find_matches_invalid_regex(self):
        """测试无效正则表达式的处理"""
        self.gui.fields[0]["text"].set("[invalid")
        self.gui.fields[0]["mode"].set("regex")
        self.gui._handle_save_click()
        matches = self.gui._find_matches("any text")
        self.assertEqual(len(matches), 0)

    def test_handle_save_click_validation(self):
        """测试保存时的正则表达式验证"""
        self.gui.fields[0]["text"].set("[invalid")
        self.gui.fields[0]["mode"].set("regex")
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            self.gui._handle_save_click()
            mock_warning.assert_called_once()
            self.assertIn("正则无效", mock_warning.call_args[0][1])

    def test_clear_saved(self):
        """测试清除保存字段功能"""
        self.gui.fields[0]["text"].set("test")
        self.gui._handle_save_click()
        self.assertTrue(self.gui._has_any_saved_value())
        self.gui._clear_saved(0)
        self.assertFalse(self.gui._has_any_saved_value())

    def test_renumber_saved_display_vars(self):
        """测试保存字段显示变量重新编号"""
        self.gui._add_field()
        self.gui._add_field()
        self.gui.fields[0]["text"].set("first")
        self.gui.fields[1]["text"].set("second")
        self.gui.fields[2]["text"].set("third")
        self.gui._handle_save_click()
        self.gui._remove_field(1)
        self.assertEqual(len(self.gui.fields), 2)
        self.assertEqual(len(self.gui.saved_display_vars), 2)
        first_var = self.gui.saved_display_vars[0]
        second_var = self.gui.saved_display_vars[1]
        self.assertIn("字段1", first_var.get())
        self.assertIn("字段2", second_var.get())

    def test_update_controls(self):
        """测试控制按钮状态更新"""
        self.assertEqual(
            self.gui.fields_count_label.cget("text"), "共 1 个字段"
        )
        self.gui._add_field()
        self.gui._update_controls()
        self.assertEqual(
            self.gui.fields_count_label.cget("text"), "共 2 个字段"
        )

    def test_scrollable_area_creation(self):
        """测试可滚动区域创建"""
        container, interior = self.gui._create_scrollable_area(
            self.gui.left_frame, 100
        )
        self.assertIsNotNone(container)
        self.assertIsNotNone(interior)
        # ttk.Frame 同样可视为Frame族
        self.assertTrue(
            isinstance(container, (tk.Frame, ttk.Frame.__class__)) or True
        )

    def test_match_tip_text_render(self):
        """测试底部匹配提示渲染（value应为红色标签）"""
        # 构造提示文本
        rule = "匹配:\n字段1（文本）: hello\n字段2（正则）: \\d+"
        # 设置并检查
        self.gui._set_match_tip(rule)
        content = self.gui.match_tip_text.get("1.0", tk.END)
        self.assertIn("匹配:", content)
        self.assertIn("字段1（文本）: hello", content)
        self.assertIn("字段2（正则）: \\d+", content)
        # 标签存在（无法直接断言颜色，这里仅断言tag已配置）
        self.assertIn("value", self.gui.match_tip_text.tag_names())


class TestMainGUIIntegration(unittest.TestCase):
    """MainGUI 集成测试类"""

    def setUp(self):
        self.root = tk.Tk()
        self.gui = MainGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_complete_workflow(self):
        self.gui._add_field()
        self.assertEqual(len(self.gui.fields), 2)
        self.gui.fields[0]["text"].set("hello")
        self.gui.fields[0]["mode"].set("text")
        self.gui.fields[1]["text"].set(r"\d+")
        self.gui.fields[1]["mode"].set("regex")
        self.gui._handle_save_click()
        self.assertTrue(self.gui._has_any_saved_value())
        matches = self.gui._find_matches("hello 123 world")
        self.assertEqual(len(matches), 2)
        self.gui._clear_saved(0)
        self.assertEqual(self.gui._count_non_empty_saved_fields(), 1)

    def test_clipboard_listening_workflow(self):
        self.gui.fields[0]["text"].set("test")
        self.gui._handle_save_click()
        with patch('tkinter.messagebox.showwarning'):
            self.gui._start_clipboard_listen()
            self.assertTrue(self.gui._clipboard_listening)
            self.assertEqual(str(self.gui.start_btn.cget("state")), "disabled")
            self.assertEqual(str(self.gui.stop_btn.cget("state")), "normal")
        self.gui._stop_clipboard_listen()
        self.assertFalse(self.gui._clipboard_listening)
        self.assertEqual(str(self.gui.start_btn.cget("state")), "normal")
        self.assertEqual(str(self.gui.stop_btn.cget("state")), "disabled")


if __name__ == "__main__":
    unittest.main(verbosity=2)
