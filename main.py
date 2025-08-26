#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板内容匹配检测器 - 主程序入口

重构说明：
- 将原有的单一文件拆分为模块化架构
- core.py: 核心业务逻辑（剪贴板监听、字段匹配、配置管理等）
- ui.py: UI界面组件（字段面板、剪贴板面板、控制面板等）
- main.py: 应用控制器和程序入口

设计原则：
- 业务逻辑与UI完全分离
- 模块间通过清晰的接口交互
- 保持原有功能不变，仅优化代码结构
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import json
import re
import logging

# 导入核心模块
from core import (
    DebugSystem,
    FieldManager,
    ClipboardManager,
    MatchEngine,
    ConfigManager,
    HotkeyManager,
    NotificationManager,
)

# 导入UI模块
from ui import MainWindow, FieldsPanel, ClipboardPanel, ControlPanel


class ApplicationController:
    """应用程序控制器

    设计说明：
    - 作为各个模块间的协调者
    - 处理业务逻辑与UI的连接
    - 管理应用程序的生命周期
    """

    def __init__(self, root):
        """初始化应用程序控制器"""
        self.root = root

        # 初始化调试系统
        DebugSystem.setup_debug_system()

        # 创建核心业务对象
        self.field_manager = FieldManager()
        self.clipboard_manager = ClipboardManager(root)
        self.match_engine = MatchEngine(self.field_manager)
        self.hotkey_manager = HotkeyManager(root)
        self.notification_manager = NotificationManager(root)

        # 创建UI对象
        self.main_window = MainWindow(root)
        self.fields_panel = FieldsPanel(root, self.field_manager)
        self.clipboard_panel = ClipboardPanel(root)
        self.control_panel = ControlPanel(root, self.hotkey_manager)

        # 初始化应用程序
        self._initialize_application()

    def _initialize_application(self):
        """初始化应用程序"""
        # 设置UI回调
        self._setup_ui_callbacks()

        # 创建界面
        self._create_interface()

        # 加载配置
        self._load_configurations()

        # 初始化热键
        self._initialize_hotkeys()

        # 初始化剪贴板显示
        self._initialize_clipboard_display()

    def _setup_ui_callbacks(self):
        """设置UI回调函数"""
        # 字段面板回调
        self.fields_panel.on_save_fields = self._handle_save_fields
        self.fields_panel.on_import_fields = self._handle_import_fields
        self.fields_panel.on_export_fields = self._handle_export_fields

        # 控制面板回调
        self.control_panel.on_start_listening = self._handle_start_listening
        self.control_panel.on_stop_listening = self._handle_stop_listening

        # 剪贴板管理器回调
        self.clipboard_manager.set_content_change_callback(
            self._handle_clipboard_change
        )

    def _create_interface(self):
        """创建主界面"""
        # 创建主框架
        main_frame = self.main_window.create_main_frame()

        # 创建各个面板
        self.fields_panel.create_panel(main_frame)
        self.clipboard_panel.create_panel(main_frame)
        self.control_panel.create_panel(main_frame)

        # 设置布局
        self.main_window.setup_layout()

    def _load_configurations(self):
        """加载配置"""
        # 加载字段配置
        self._load_field_configuration()

        # 加载热键配置
        self.hotkey_manager.load_config()

        # 更新UI显示
        self.control_panel.update_button_hotkey_display()

    def _load_field_configuration(self):
        """加载字段配置"""
        fields_data = ConfigManager.load_fields_config()

        if fields_data:
            # 清空现有字段
            self.field_manager.fields.clear()
            self.field_manager.saved_display_vars.clear()

            # 加载字段数据
            for field_data in fields_data:
                if (
                    isinstance(field_data, dict)
                    and 'text' in field_data
                    and 'mode' in field_data
                ):
                    text_var = tk.StringVar(value=field_data['text'])
                    mode_var = tk.StringVar(value=field_data['mode'])
                    self.field_manager.fields.append(
                        {"text": text_var, "mode": mode_var}
                    )

                    # 创建对应的保存显示变量
                    mode_label = self._get_mode_label(mode_var.get())
                    display_text = (
                        field_data['text'] if field_data['text'] else '（空）'
                    )
                    self.field_manager.saved_display_vars.append(
                        tk.StringVar(
                            value=f"字段{len(self.field_manager.fields)}（{mode_label}）: {display_text}"  # noqa: E501
                        )
                    )

        # 如果没有字段，至少添加一个
        if not self.field_manager.fields:
            self._add_default_field()

        # 重新渲染界面
        self.fields_panel.reflow_fields()
        self.fields_panel.reflow_saved_display()
        self.fields_panel.update_controls()

    def _add_default_field(self):
        """添加默认字段"""
        text_var = tk.StringVar()
        mode_var = tk.StringVar(value="text")
        self.field_manager.add_field(text_var, mode_var)

    def _initialize_hotkeys(self):
        """初始化热键"""
        self.hotkey_manager.start_listening(
            self._handle_start_listening, self._handle_stop_listening
        )

    def _initialize_clipboard_display(self):
        """初始化剪贴板显示"""
        initial_text = self.clipboard_manager._get_clipboard_text()
        self.clipboard_panel.set_display_text(initial_text)
        self.clipboard_manager._last_clipboard_text = initial_text

    def _handle_save_fields(self):
        """处理保存字段"""
        DebugSystem.debug_print("开始保存字段配置", logging.INFO)

        # 保存前校验正则表达式有效性
        for i, field in enumerate(self.field_manager.fields, start=1):
            value = field["text"].get().strip()
            mode_label = self._get_mode_label(field["mode"].get())

            if mode_label == "正则" and value:
                try:
                    re.compile(value)
                    DebugSystem.debug_print(
                        f"字段{i}正则表达式验证通过: {value}", logging.DEBUG
                    )
                except re.error as e:
                    DebugSystem.debug_print(
                        f"字段{i}正则表达式验证失败: {value}, 错误: {e}",
                        logging.ERROR,
                    )
                    messagebox.showwarning("提示", f"字段{i} 的正则无效: {e}")
                    return

        # 确保保存显示变量数量正确
        if len(self.field_manager.saved_display_vars) != len(
            self.field_manager.fields
        ):
            DebugSystem.debug_print(
                f"调整保存显示变量数量: {len(self.field_manager.saved_display_vars)} -> {len(self.field_manager.fields)}",  # noqa: E501
                logging.DEBUG,
            )
            self.field_manager.saved_display_vars = [
                tk.StringVar() for _ in range(len(self.field_manager.fields))
            ]

        # 保存所有字段
        saved_count = 0
        for idx, field in enumerate(self.field_manager.fields, start=1):
            value = field["text"].get().strip()
            mode_label = self._get_mode_label(field["mode"].get())
            text = value if value else "（空）"

            self.field_manager.saved_display_vars[idx - 1].set(
                f"字段{idx}（{mode_label}）: {text}"
            )
            if value:
                saved_count += 1

        DebugSystem.debug_print(
            f"字段保存完成，共 {len(self.field_manager.fields)} 个字段，其中 {saved_count} 个有内容",  # noqa: E501
            logging.INFO,
        )

        # 重新渲染保存显示区域
        self.fields_panel.reflow_saved_display()

        # 保存配置到文件
        ConfigManager.save_fields_config(self.field_manager.fields)

    def _handle_import_fields(self):
        """处理导入字段"""
        try:
            DebugSystem.debug_print("开始导入字段配置", logging.INFO)

            # 打开文件选择对话框
            filename = filedialog.askopenfilename(
                title="选择要导入的字段配置文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            )

            if not filename:
                DebugSystem.debug_print("用户取消导入操作", logging.INFO)
                return

            DebugSystem.debug_print(f"选择导入文件: {filename}", logging.INFO)

            # 读取JSON文件
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 验证数据格式
            if not isinstance(data, dict) or 'fields' not in data:
                DebugSystem.debug_print(
                    "文件格式不正确，缺少fields字段", logging.ERROR
                )
                messagebox.showerror("错误", "文件格式不正确，缺少fields字段")
                return

            fields_data = data['fields']
            if not isinstance(fields_data, list):
                DebugSystem.debug_print(
                    "fields字段必须是数组格式", logging.ERROR
                )
                messagebox.showerror("错误", "fields字段必须是数组格式")
                return

            DebugSystem.debug_print(
                f"文件验证通过，包含 {len(fields_data)} 个字段", logging.INFO
            )

            # 清空现有字段
            old_count = len(self.field_manager.fields)
            self.field_manager.fields.clear()
            self.field_manager.saved_display_vars.clear()
            DebugSystem.debug_print(
                f"清空现有字段: {old_count} -> 0", logging.INFO
            )

            # 导入字段数据
            imported_count = 0
            for field_data in fields_data:
                if (
                    isinstance(field_data, dict)
                    and 'text' in field_data
                    and 'mode' in field_data
                ):
                    text_var = tk.StringVar(value=field_data['text'])
                    mode_var = tk.StringVar(value=field_data['mode'])
                    self.field_manager.fields.append(
                        {"text": text_var, "mode": mode_var}
                    )

                    # 创建对应的保存显示变量
                    mode_label = self._get_mode_label(mode_var.get())
                    display_text = (
                        field_data['text'] if field_data['text'] else '（空）'
                    )
                    self.field_manager.saved_display_vars.append(
                        tk.StringVar(
                            value=f"字段{len(self.field_manager.fields)}（{mode_label}）: {display_text}"  # noqa: E501
                        )
                    )
                    imported_count += 1

            DebugSystem.debug_print(
                f"成功导入 {imported_count} 个字段", logging.INFO
            )

            # 如果没有字段，至少添加一个
            if not self.field_manager.fields:
                DebugSystem.debug_print(
                    "导入后无字段，添加默认字段", logging.INFO
                )
                self._add_default_field()

            # 重新渲染界面
            self.fields_panel.reflow_fields()
            self.fields_panel.reflow_saved_display()
            self.fields_panel.update_controls()

            messagebox.showinfo(
                "成功", f"成功导入 {len(self.field_manager.fields)} 个字段"
            )

        except Exception as e:
            DebugSystem.debug_print(f"导入失败: {str(e)}", logging.ERROR)
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _handle_export_fields(self):
        """处理导出字段"""
        try:
            # 打开文件保存对话框
            filename = filedialog.asksaveasfilename(
                title="保存字段配置文件",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            )

            if not filename:
                return

            # 准备导出数据
            export_data = {"fields": []}

            for field in self.field_manager.fields:
                export_data["fields"].append(
                    {"text": field["text"].get(), "mode": field["mode"].get()}
                )

            # 写入JSON文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo(
                "成功",
                f"成功导出 {len(self.field_manager.fields)} 个字段到 {filename}",
            )

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def _handle_start_listening(self):
        """处理开始监听"""
        # 验证是否有保存的字段
        if not self.match_engine.has_any_saved_value():
            DebugSystem.debug_print(
                "没有保存的非空字段，无法开始监听", logging.WARNING
            )
            messagebox.showwarning("提示", "请先在左侧保存至少一个非空字段。")
            return

        # 开始剪贴板监听
        if self.clipboard_manager.start_listening():
            # 清空匹配提示
            self.control_panel.clear_match_tip()

            # 清空右侧显示内容
            self.clipboard_panel.set_display_text("（等待剪贴板内容...）")

            # 更新按钮状态
            self.control_panel.set_listening_state(True)

    def _handle_stop_listening(self):
        """处理停止监听"""
        if self.clipboard_manager.stop_listening():
            # 更新按钮状态
            self.control_panel.set_listening_state(False)

    def _handle_clipboard_change(self, clipboard_text):
        """处理剪贴板内容变化"""
        # 更新显示
        self.clipboard_panel.set_display_text(clipboard_text)

        # 进行匹配检测
        match_mode = self.fields_panel.match_mode_var.get()
        is_match, match_text = self.match_engine.process_matches(
            clipboard_text, match_mode
        )

        if is_match:
            # 显示匹配提示
            self.control_panel.set_match_tip(match_text)

            # 发送通知
            self.notification_manager.notify_match(match_text)

            # 停止监听
            self._handle_stop_listening()

    def _get_mode_label(self, mode_value):
        """获取模式的中文标签"""
        return "文本" if mode_value == "text" else "正则"


def main():
    """主函数"""
    root = tk.Tk()
    ApplicationController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
