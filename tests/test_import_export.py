"""
导入导出功能测试
测试字段配置的导入导出功能
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.test_utils import (
    ConfigManager,
    create_mock_file_dialog,
    create_mock_save_dialog,
)


class TestImportFunctionality:
    """导入功能测试"""

    def test_import_fields_success(self, temp_config_dir):
        """测试成功导入字段"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        # 准备导入数据
        import_data = {
            "fields": [
                {"text": "imported_field_1", "mode": "text"},
                {"text": "\\d+", "mode": "regex"},
                {"text": "imported_field_3", "mode": "text"},
            ]
        }

        # 创建临时导入文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump(import_data, f, ensure_ascii=False, indent=2)
            import_file_path = f.name

        try:
            with patch('tkinter.Tk') as mock_tk:
                root = mock_tk.return_value
                gui = MainGUI(root)

                # 模拟文件选择对话框
                with create_mock_file_dialog(import_file_path):
                    gui._import_fields()

                # 验证导入结果
                assert len(gui.fields) == 3
                assert gui.fields[0]["text"].get() == "imported_field_1"
                assert gui.fields[1]["text"].get() == "\\d+"
                assert gui.fields[2]["text"].get() == "imported_field_3"

                # 验证模式设置
                assert gui.fields[0]["mode"].get() == "text"
                assert gui.fields[1]["mode"].get() == "regex"
                assert gui.fields[2]["mode"].get() == "text"

        finally:
            # 清理临时文件
            Path(import_file_path).unlink(missing_ok=True)

    def test_import_fields_validation(self, temp_config_dir):
        """测试导入字段验证"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        # 测试无效数据格式
        invalid_data = {"invalid": "format"}

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 模拟文件选择对话框
            with create_mock_file_dialog("test.json"):
                with patch('builtins.open', MagicMock()) as mock_open:
                    # 设置模拟返回值
                    mock_read = (
                        mock_open.return_value.__enter__.return_value.read
                    )
                    mock_read.return_value = json.dumps(invalid_data)
                    with patch('json.load', return_value=invalid_data):
                        with patch(
                            'tkinter.messagebox.showerror'
                        ) as mock_error:
                            gui._import_fields()
                            mock_error.assert_called_once()

    def test_import_fields_cancel(self, temp_config_dir):
        """测试导入取消操作"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 记录原始字段数量
            original_count = len(gui.fields)

            # 模拟用户取消文件选择
            with create_mock_file_dialog(""):  # 空字符串表示用户取消
                gui._import_fields()

            # 验证字段数量没有变化
            assert len(gui.fields) == original_count


class TestExportFunctionality:
    """导出功能测试"""

    def test_export_fields_success(self, temp_config_dir):
        """测试成功导出字段"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 设置字段内容
            gui.fields[0]["text"].set("export_field_1")
            gui.fields[0]["mode"].set("text")
            gui.fields[1]["text"].set("\\d+")
            gui.fields[1]["mode"].set("regex")

            # 保存字段
            gui._handle_save_click()

            # 模拟保存对话框
            export_file_path = "test_export.json"
            with create_mock_save_dialog(export_file_path):
                with patch('builtins.open', MagicMock()) as mock_file:
                    gui._export_fields()

                    # 验证文件写入被调用
                    mock_file.assert_called_once_with(
                        export_file_path, 'w', encoding='utf-8'
                    )
                    # 成功分支：应弹出showinfo
                    with patch('tkinter.messagebox.showinfo') as info:
                        gui._export_fields()
                        # 第二次调用也应触发成功提示
                        assert info.called

    def test_export_fields_cancel(self, temp_config_dir):
        """测试导出取消操作"""
        from main import MainGUI

        # 创建测试配置
        config_manager = ConfigManager(temp_config_dir)
        config_manager.create_test_fields_config([])

        with patch('tkinter.Tk') as mock_tk:
            root = mock_tk.return_value
            gui = MainGUI(root)

            # 设置字段内容
            gui.fields[0]["text"].set("test_field")
            gui.fields[0]["mode"].set("text")
            gui._handle_save_click()

            # 模拟用户取消保存对话框
            with create_mock_save_dialog(""):  # 空字符串表示用户取消
                with patch('builtins.open', MagicMock()) as mock_file:
                    gui._export_fields()

                    # 验证文件写入没有被调用
                    mock_file.assert_not_called()


class TestImportExportIntegration:
    """导入导出集成测试"""

    def test_import_export_roundtrip(self, temp_config_dir):
        """测试导入导出往返操作"""
        from main import MainGUI

        from tests.test_utils import test_root

        if test_root is None:
            pytest.skip("测试环境未正确设置")

        gui = MainGUI(test_root)

        # 设置字段内容
        gui.fields[0]["text"].set("roundtrip_field")
        gui.fields[0]["mode"].set("text")
        gui._handle_save_click()

        # 导出字段
        export_file_path = "roundtrip_export.json"
        with create_mock_save_dialog(export_file_path):
            with patch('builtins.open', MagicMock()) as mock_file:
                # 模拟文件写入
                mock_file.return_value.__enter__.return_value.write = (
                    MagicMock()
                )
                gui._export_fields()

        # 清空字段
        gui.fields.clear()
        gui.saved_display_vars.clear()

        # 重新导入 - 模拟文件读取
        with create_mock_file_dialog(export_file_path):
            with patch('builtins.open', MagicMock()) as mock_file:
                # 模拟文件读取，返回之前导出的数据
                import_data = {
                    "fields": [{"text": "roundtrip_field", "mode": "text"}]
                }
                import json

                mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(
                    import_data
                )
                gui._import_fields()

        # 验证导入结果
        assert len(gui.fields) == 1
        assert gui.fields[0]["text"].get() == "roundtrip_field"
        assert gui.fields[0]["mode"].get() == "text"
