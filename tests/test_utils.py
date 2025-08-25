"""
测试工具模块
提供通用的测试辅助函数和类
"""

import tkinter as tk
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class MockTkinter:
    """模拟Tkinter环境，避免创建真实窗口"""
    
    @staticmethod
    def mock_tkinter():
        """模拟Tkinter的patch装饰器"""
        return patch.multiple(
            'tkinter',
            Tk=MagicMock(spec=tk.Tk),
            Frame=MagicMock(spec=tk.Frame),
            Label=MagicMock(spec=tk.Label),
            Button=MagicMock(spec=tk.Button),
            Entry=MagicMock(spec=tk.Entry),
            StringVar=MagicMock(spec=tk.StringVar),
            BooleanVar=MagicMock(spec=tk.BooleanVar),
            Text=MagicMock(spec=tk.Text),
            Canvas=MagicMock(spec=tk.Canvas),
            Scrollbar=MagicMock(spec=tk.Scrollbar),
        )


class ConfigManager:
    """配置管理器，用于测试中的配置文件操作"""
    
    def __init__(self, temp_dir):
        self.temp_dir = Path(temp_dir)
        self.fields_config_path = self.temp_dir / "fields_config.json"
        self.hotkey_config_path = self.temp_dir / "hotkey_config.json"
    
    def create_test_fields_config(self, fields_data):
        """创建测试用的字段配置文件"""
        config = {"fields": fields_data}
        with open(self.fields_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def create_test_hotkey_config(self, start_key="F8", stop_key="F9"):
        """创建测试用的热键配置文件"""
        config = {
            "start_hotkey": start_key,
            "stop_hotkey": stop_key
        }
        with open(self.hotkey_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def cleanup(self):
        """清理配置文件"""
        for config_file in [self.fields_config_path, self.hotkey_config_path]:
            if config_file.exists():
                config_file.unlink()


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def create_field_data(text="", mode="text"):
        """创建字段数据"""
        return {"text": text, "mode": mode}
    
    @staticmethod
    def create_fields_list(count=3, include_empty=True):
        """创建字段列表"""
        fields = []
        for i in range(count):
            if include_empty or i % 2 == 0:
                fields.append({
                    "text": f"test_field_{i}",
                    "mode": "text" if i % 2 == 0 else "regex"
                })
            else:
                fields.append({
                    "text": "",
                    "mode": "text"
                })
        return fields
    
    @staticmethod
    def create_clipboard_content():
        """创建测试用的剪贴板内容"""
        return "hello world 123 test content"


def create_mock_event(keysym="F8"):
    """创建模拟的键盘事件"""
    event = MagicMock()
    event.keysym = keysym
    event.char = keysym if len(keysym) == 1 else ""
    event.state = 0
    return event


def create_mock_file_dialog(return_value="test_file.json"):
    """创建模拟的文件对话框"""
    return patch(
        'tkinter.filedialog.askopenfilename', 
        return_value=return_value
    )


def create_mock_save_dialog(return_value="test_save.json"):
    """创建模拟的保存对话框"""
    return patch(
        'tkinter.filedialog.asksaveasfilename', 
        return_value=return_value
    )


# 全局测试root实例
test_root = None
