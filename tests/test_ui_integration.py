"""
UI集成测试
测试主应用程序和UI组件的基本初始化和集成
"""

import tkinter as tk
from main import ApplicationController


class TestApplicationIntegration:
    """应用程序集成测试"""

    def test_application_controller_init(self):
        """测试应用程序控制器初始化"""
        root = tk.Tk()
        try:
            app = ApplicationController(root)

            # 检查核心组件是否正确初始化
            assert app.field_manager is not None
            assert app.clipboard_manager is not None
            assert app.match_engine is not None
            assert app.hotkey_manager is not None
            assert app.notification_manager is not None

            # 检查UI组件是否正确初始化
            assert app.main_window is not None
            assert app.fields_panel is not None
            assert app.clipboard_panel is not None
            assert app.control_panel is not None

        finally:
            root.destroy()

    def test_application_basic_workflow(self):
        """测试应用程序基本工作流程"""
        root = tk.Tk()
        try:
            app = ApplicationController(root)

            # 通过控制器添加字段应该是可能的
            assert app.field_manager.can_add_field() is True
            assert app.match_engine is not None
            assert not app.clipboard_manager.is_listening()

        finally:
            root.destroy()

    def test_application_callbacks_setup(self):
        """测试应用程序回调设置"""
        root = tk.Tk()
        try:
            app = ApplicationController(root)

            # 检查回调是否正确设置
            # 这些方法应该存在并且可以调用（虽然可能不执行实际操作）
            assert hasattr(app, '_handle_start_listening')
            assert hasattr(app, '_handle_stop_listening')
            assert hasattr(app, '_handle_save_fields')
            assert hasattr(app, '_handle_clipboard_change')

        finally:
            root.destroy()

    def test_application_ui_integration(self):
        """测试应用程序UI集成"""
        root = tk.Tk()
        try:
            app = ApplicationController(root)

            assert app.main_window.root == root
            assert app.fields_panel.field_manager == app.field_manager

        finally:
            root.destroy()
