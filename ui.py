#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板内容匹配检测器 - UI界面模块

功能说明：
- 主窗口界面创建和管理
- 字段输入和显示界面
- 剪贴板内容显示界面
- 控制按钮和热键设置界面
- 滚动区域和交互处理

设计原则：
- UI与业务逻辑完全分离
- 组件化设计，便于维护
- 统一的界面风格和布局
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import re
from core import Config, DebugSystem


class ScrollableFrame:
    """可滚动框架工具类"""

    @staticmethod
    def create_scrollable_area(parent, height):
        """创建可滚动区域

        设计说明：
        - 使用Canvas + Scrollbar实现真正的滚动功能
        - 支持鼠标滚轮滚动
        - 确保内容正确显示和滚动

        Args:
            parent: 父容器
            height: 区域高度

        Returns:
            tuple: (容器框架, 内部框架) 元组
        """
        # 创建容器框架
        container = ttk.Frame(parent)

        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(container, height=height, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=canvas.yview
        )

        # 创建内部框架
        interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(
            (0, 0), window=interior, anchor="nw"
        )

        # 配置Canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # 配置滚动区域
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        interior.bind("<Configure>", _on_frame_configure)

        def _on_canvas_configure(event):
            canvas.itemconfigure(interior_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)

        # 布局
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        container.columnconfigure(0, weight=1)

        # 启用鼠标滚轮支持
        ScrollableFrame._enable_mousewheel(canvas, interior)

        return container, interior

    @staticmethod
    def _enable_mousewheel(canvas, interior):
        """为滚动区域启用鼠标滚轮支持

        设计说明：
        - 绑定滚轮事件到Canvas对象
        - 支持跨平台滚轮事件
        - 确保滚动功能正常工作

        Args:
            canvas: Canvas对象
            interior: 内部框架
        """

        def _on_mousewheel(event):
            """鼠标滚轮事件处理"""
            # 计算滚动步长
            if sys.platform == "darwin":
                # macOS
                delta = event.delta
                step = -1 if delta > 0 else 1
            else:
                # Windows/Linux
                if hasattr(event, 'num'):
                    step = -1 if event.num == 4 else 1
                else:
                    step = -int(event.delta / 120) if event.delta else 0
                    if step == 0:
                        step = -1 if event.delta > 0 else 1

            # 执行滚动
            if step:
                canvas.yview_scroll(step * 3, "units")

        # 绑定滚轮事件到Canvas
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)


class FieldsPanel:
    """左侧字段管理面板"""

    def __init__(self, parent, field_manager):
        self.parent = parent
        self.field_manager = field_manager
        self.fields_container = None
        self.saved_container = None
        self._delete_buttons = []
        # UI变量
        self.match_mode_var = tk.StringVar(value="single")
        # 回调函数
        self.on_save_fields = None
        self.on_import_fields = None
        self.on_export_fields = None

    def create_panel(self, main_frame):
        """创建左侧字段管理面板"""
        # 左侧主框架
        self.left_frame = ttk.LabelFrame(
            main_frame, text="检测字段管理", padding="10"
        )
        self.left_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10)
        )

        # 创建各个区域
        self._create_fields_title()
        self._create_fields_input_section()
        self._create_field_controls()
        self._create_match_mode_selection()
        self._create_save_button()
        self._create_separator()
        self._create_saved_fields_section()

    def _create_fields_title(self):
        """创建字段管理标题"""
        ttk.Label(self.left_frame, text="检测字段（无上限）").grid(
            row=0, column=0, sticky=tk.W
        )

    def _create_fields_input_section(self):
        """创建检测字段输入区域"""
        # 动态字段输入区域（可滚动）
        fields_section, self.fields_container = (
            ScrollableFrame.create_scrollable_area(
                self.left_frame, height=Config.LEFT_INPUT_SECTION_HEIGHT
            )
        )
        fields_section.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.fields_container.columnconfigure(1, weight=1)

    def _create_field_controls(self):
        """创建字段控制区域"""
        controls = ttk.Frame(self.left_frame)
        controls.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(6, 6))

        # 新增字段按钮
        self.add_field_btn = ttk.Button(
            controls, text="新增字段", command=self._handle_add_field
        )
        self.add_field_btn.grid(row=0, column=0, sticky=tk.W)

        # 字段计数标签
        self.fields_count_label = ttk.Label(controls, text="共 0 个字段")
        self.fields_count_label.grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )

        # 导入导出按钮区域
        import_export_frame = ttk.Frame(self.left_frame)
        import_export_frame.grid(
            row=3, column=0, sticky=(tk.W, tk.E), pady=(6, 6)
        )

        # 导入字段按钮
        self.import_btn = ttk.Button(
            import_export_frame,
            text="导入字段",
            command=self._handle_import_fields,
        )
        self.import_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        # 导出字段按钮
        self.export_btn = ttk.Button(
            import_export_frame,
            text="导出字段",
            command=self._handle_export_fields,
        )
        self.export_btn.grid(row=0, column=1, sticky=tk.W)

    def _create_match_mode_selection(self):
        """创建匹配模式选择区域"""
        match_mode_frame = ttk.Frame(self.left_frame)
        match_mode_frame.grid(row=4, column=0, sticky=tk.W, pady=(6, 6))

        ttk.Label(match_mode_frame, text="匹配策略：").grid(
            row=0, column=0, sticky=tk.W
        )

        # 单条匹配模式
        ttk.Radiobutton(
            match_mode_frame,
            text="匹配单条",
            value="single",
            variable=self.match_mode_var,
        ).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))

        # 全部匹配模式
        ttk.Radiobutton(
            match_mode_frame,
            text="匹配全部",
            value="all",
            variable=self.match_mode_var,
        ).grid(row=0, column=2, sticky=tk.W)

    def _create_save_button(self):
        """创建保存按钮"""
        self.submit_button = ttk.Button(
            self.left_frame, text="保存字段", command=self._handle_save_fields
        )
        self.submit_button.grid(row=5, column=0, sticky=tk.W)

    def _create_separator(self):
        """创建分隔线"""
        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).grid(
            row=6, column=0, sticky=(tk.E, tk.W), pady=(10, 10)
        )

    def _create_saved_fields_section(self):
        """创建保存字段显示区域"""
        # 标题
        ttk.Label(self.left_frame, text="当前保存的字段").grid(
            row=7, column=0, sticky=tk.W, pady=(0, 6)
        )

        # 保存字段显示区域（可滚动）
        saved_section, self.saved_container = (
            ScrollableFrame.create_scrollable_area(
                self.left_frame, height=Config.LEFT_SAVED_SECTION_HEIGHT
            )
        )
        saved_section.grid(row=8, column=0, sticky=(tk.W, tk.E))
        self.saved_container.columnconfigure(0, weight=1)

    def reflow_fields(self):
        """重新渲染动态字段输入界面"""
        # 清空现有内容
        for child in self.fields_container.winfo_children():
            child.destroy()

        self._delete_buttons = []

        # 为每个字段创建输入界面
        for idx, field in enumerate(self.field_manager.fields):
            row_base = idx * 2

            # 字段标签
            ttk.Label(self.fields_container, text=f"字段{idx + 1}:").grid(
                row=row_base, column=0, sticky=tk.W, pady=(0, 2)
            )

            # 输入框
            entry = ttk.Entry(
                self.fields_container, textvariable=field["text"], width=28
            )
            entry.grid(
                row=row_base, column=1, sticky=(tk.W, tk.E), padx=(6, 6)
            )

            # 删除按钮
            del_btn = ttk.Button(
                self.fields_container,
                text="删除",
                command=lambda i=idx: self._handle_remove_field(i),
            )
            del_btn.grid(row=row_base, column=2, sticky=tk.W)
            self._delete_buttons.append(del_btn)

            # 模式选择区域
            mode_frame = ttk.Frame(self.fields_container)
            mode_frame.grid(
                row=row_base + 1,
                column=0,
                columnspan=3,
                sticky=tk.W,
                pady=(0, 8),
            )

            ttk.Label(mode_frame, text="模式：").grid(
                row=0, column=0, sticky=tk.W
            )

            # 纯文本模式
            ttk.Radiobutton(
                mode_frame,
                text="纯文本",
                value="text",
                variable=field["mode"],
            ).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))

            # 正则表达式模式
            ttk.Radiobutton(
                mode_frame,
                text="正则表达式",
                value="regex",
                variable=field["mode"],
            ).grid(row=0, column=2, sticky=tk.W)

    def reflow_saved_display(self):
        """重新渲染保存字段显示界面"""
        # 清空现有内容
        for child in self.saved_container.winfo_children():
            child.destroy()

        # 为每个保存项创建显示标签（只读显示）
        for idx, var in enumerate(self.field_manager.saved_display_vars):
            ttk.Label(self.saved_container, textvariable=var).grid(
                row=idx, column=0, sticky=(tk.W, tk.E), padx=(0, 8)
            )

    def update_controls(self):
        """更新控制按钮状态"""
        count = self.field_manager.get_field_count()

        # 更新字段计数
        self.fields_count_label.configure(text=f"共 {count} 个字段")

        # 新增按钮始终可用（无上限限制）
        self.add_field_btn.configure(state=tk.NORMAL)

        # 更新删除按钮状态
        del_state = (
            tk.DISABLED
            if not self.field_manager.can_remove_field()
            else tk.NORMAL
        )
        for btn in self._delete_buttons:
            btn.configure(state=del_state)

    def _handle_add_field(self):
        """处理新增字段"""
        # 创建新字段的变量
        text_var = tk.StringVar()
        mode_var = tk.StringVar(value="text")

        # 添加到字段管理器
        if self.field_manager.add_field(text_var, mode_var):
            self.reflow_fields()
            self.reflow_saved_display()
            self.update_controls()

    def _handle_remove_field(self, index):
        """处理删除字段"""
        if self.field_manager.remove_field(index):
            self.reflow_fields()
            self.reflow_saved_display()
            self.update_controls()

    def _handle_save_fields(self):
        """处理保存字段"""
        if self.on_save_fields:
            self.on_save_fields()

    def _handle_import_fields(self):
        """处理导入字段"""
        if self.on_import_fields:
            self.on_import_fields()

    def _handle_export_fields(self):
        """处理导出字段"""
        if self.on_export_fields:
            self.on_export_fields()

        # 调整数组长度
        if len(self.field_manager.saved_display_vars) > len(
            self.field_manager.fields
        ):
            self.field_manager.saved_display_vars = (
                self.field_manager.saved_display_vars[
                    : len(self.field_manager.fields)
                ]
            )
        elif len(self.field_manager.saved_display_vars) < len(
            self.field_manager.fields
        ):
            for i in range(
                len(self.field_manager.saved_display_vars),
                len(self.field_manager.fields),
            ):
                mode_label = self._get_mode_label(
                    self.field_manager.fields[i]["mode"].get()
                )
                self.field_manager.saved_display_vars.append(
                    tk.StringVar(value=f"字段{i + 1}（{mode_label}）: （空）")
                )

    def _get_mode_label(self, mode_value):
        """获取模式的中文标签"""
        return "文本" if mode_value == "text" else "正则"

    def _strip_match_suffix(self, text):
        """去除文本中的匹配状态后缀"""
        return re.sub(r" \[(匹配|不匹配|无效正则)\]$", "", text)


class ClipboardPanel:
    """右侧剪贴板显示面板"""

    def __init__(self, parent):
        self.parent = parent
        self.display_text = None

    def create_panel(self, main_frame):
        """创建右侧剪贴板显示面板"""
        right_frame = ttk.LabelFrame(
            main_frame, text="剪贴板内容显示", padding="10"
        )
        right_frame.grid(
            row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0)
        )

        # 文本显示区域（只读，支持滚动）
        self.display_text = scrolledtext.ScrolledText(
            right_frame,
            width=50,  # 固定宽度50个字符
            height=20,  # 固定高度20行
            wrap=tk.WORD,  # 按单词换行
            state=tk.DISABLED,  # 只读状态
        )
        self.display_text.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        # 设置布局权重 - 文本区域填充整个框架
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

    def set_display_text(self, text):
        """在右侧显示区域设置文本内容"""
        self.display_text.configure(state=tk.NORMAL)
        self.display_text.delete("1.0", tk.END)
        self.display_text.insert(tk.END, text)
        self.display_text.configure(state=tk.DISABLED)


class ControlPanel:
    """底部控制面板"""

    def __init__(self, parent, hotkey_manager):
        self.parent = parent
        self.hotkey_manager = hotkey_manager
        self.match_tip_text = None

        # UI变量
        self.start_hotkey_var = None
        self.stop_hotkey_var = None
        self.debug_var = None

        # 按钮控件
        self.start_btn = None
        self.stop_btn = None

        # 回调函数
        self.on_start_listening = None
        self.on_stop_listening = None

        # 热键录制相关
        self._recording_entry = None
        self._recording_var = None
        self._recording_action = None

    def create_panel(self, main_frame):
        """创建底部执行控制面板"""
        bottom_frame = ttk.LabelFrame(
            main_frame, text="执行控制", padding="10"
        )
        bottom_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        # 设置按钮样式
        self._setup_button_styles()

        # 开始监听按钮
        self.start_btn = self._create_action_button(
            bottom_frame,
            f"开始监听 ({self.hotkey_manager.start_hotkey})",
            self._handle_start_listening,
            0,
        )

        # 停止监听按钮
        self.stop_btn = self._create_action_button(
            bottom_frame,
            f"停止监听 ({self.hotkey_manager.stop_hotkey})",
            self._handle_stop_listening,
            1,
        )
        self.stop_btn.configure(state=tk.DISABLED)

        # 热键设置区域
        self._create_hotkey_settings(bottom_frame)

        # 匹配结果提示（Text，支持局部高亮）
        self.match_tip_text = tk.Text(
            bottom_frame, width=40, height=5, wrap=tk.WORD
        )
        self.match_tip_text.grid(
            row=0, column=2, sticky=(tk.W, tk.E), padx=(20, 0)
        )
        self.match_tip_text.configure(state=tk.DISABLED)
        self.match_tip_text.tag_configure("value", foreground="red")

        # 设置列权重
        bottom_frame.columnconfigure(0, weight=0)
        bottom_frame.columnconfigure(1, weight=0)
        bottom_frame.columnconfigure(2, weight=1)

    def _create_hotkey_settings(self, bottom_frame):
        """创建热键设置区域"""
        hotkey_frame = ttk.Frame(bottom_frame)
        hotkey_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0)
        )

        # 热键说明
        ttk.Label(
            hotkey_frame, text="热键设置:", font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT)

        # 开始监听热键设置
        start_hotkey_frame = ttk.Frame(hotkey_frame)
        start_hotkey_frame.pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(start_hotkey_frame, text="开始:").pack(side=tk.LEFT)
        self.start_hotkey_var = tk.StringVar(
            value=self.hotkey_manager.start_hotkey
        )

        # 使用只读输入框显示热键，点击后进入录制模式
        start_hotkey_entry = ttk.Entry(
            start_hotkey_frame,
            textvariable=self.start_hotkey_var,
            width=8,
            state="readonly",
        )
        start_hotkey_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 绑定点击事件，进入热键录制模式
        start_hotkey_entry.bind(
            '<Button-1>',
            lambda e: self._start_hotkey_recording(
                start_hotkey_entry, self.start_hotkey_var, "开始"
            ),
        )

        # 停止监听热键设置
        stop_hotkey_frame = ttk.Frame(hotkey_frame)
        stop_hotkey_frame.pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(stop_hotkey_frame, text="停止:").pack(side=tk.LEFT)
        self.stop_hotkey_var = tk.StringVar(
            value=self.hotkey_manager.stop_hotkey
        )

        # 使用只读输入框显示热键，点击后进入录制模式
        stop_hotkey_entry = ttk.Entry(
            stop_hotkey_frame,
            textvariable=self.stop_hotkey_var,
            width=8,
            state="readonly",
        )
        stop_hotkey_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 绑定点击事件，进入热键录制模式
        stop_hotkey_entry.bind(
            '<Button-1>',
            lambda e: self._start_hotkey_recording(
                stop_hotkey_entry, self.stop_hotkey_var, "停止"
            ),
        )

        # 应用热键设置按钮
        apply_hotkey_btn = ttk.Button(
            hotkey_frame, text="应用设置", command=self._apply_hotkey_settings
        )
        apply_hotkey_btn.pack(side=tk.LEFT, padx=(20, 0))

        # 调试开关（仅在开发环境显示）
        if Config.DEBUG_MODE:
            self.debug_var = tk.BooleanVar(value=Config.DEBUG_MODE)
            debug_check = ttk.Checkbutton(
                hotkey_frame,
                text="调试模式",
                variable=self.debug_var,
                command=self._toggle_debug_mode,
            )
            debug_check.pack(side=tk.LEFT, padx=(20, 0))

    def _setup_button_styles(self):
        """设置按钮样式"""
        style = ttk.Style()
        style.configure("Start.TButton", font=("Helvetica", 14))
        style.configure("Stop.TButton", font=("Helvetica", 14))

    def _create_action_button(self, parent, text, command, column):
        """创建操作按钮"""
        # 按钮容器（固定尺寸）
        holder = ttk.Frame(
            parent,
            width=Config.START_STOP_BUTTON_WIDTH,
            height=Config.START_STOP_BUTTON_HEIGHT,
        )
        holder.grid(row=0, column=column, sticky=tk.W)
        holder.grid_propagate(False)

        # 按钮
        button = ttk.Button(
            holder,
            text=text,
            command=command,
            takefocus=False,
        )
        button.pack(fill="both", expand=True)

        return button

    def update_button_hotkey_display(self):
        """更新按钮上的热键显示和输入框中的值"""
        # 更新按钮文本
        start_text = f"开始监听 ({self.hotkey_manager.start_hotkey})"
        stop_text = f"停止监听 ({self.hotkey_manager.stop_hotkey})"
        self.start_btn.configure(text=start_text)
        self.stop_btn.configure(text=stop_text)

        # 同时更新输入框中的值
        if self.start_hotkey_var:
            self.start_hotkey_var.set(self.hotkey_manager.start_hotkey)
        if self.stop_hotkey_var:
            self.stop_hotkey_var.set(self.hotkey_manager.stop_hotkey)

    def set_listening_state(self, is_listening):
        """设置监听状态"""
        if is_listening:
            self.start_btn.configure(state=tk.DISABLED)
            self.stop_btn.configure(state=tk.NORMAL)
        else:
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)

    def clear_match_tip(self):
        """清空匹配提示区域"""
        try:
            self.match_tip_text.configure(state=tk.NORMAL)
            self.match_tip_text.delete("1.0", tk.END)
            self.match_tip_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    def set_match_tip(self, rule_text: str):
        """设置匹配提示文本，并将 value（冒号后的部分）渲染为红色"""
        try:
            self.match_tip_text.configure(state=tk.NORMAL)
            self.match_tip_text.delete("1.0", tk.END)
            lines = rule_text.splitlines()
            for i, line in enumerate(lines):
                # 标题行（例如："匹配:" 或 "全部匹配:") 不做高亮
                if line.endswith(":") and ("匹配" in line):
                    self.match_tip_text.insert(
                        tk.END, line + ("\n" if i < len(lines) - 1 else "")
                    )
                    continue
                if ": " in line:
                    left, right = line.split(": ", 1)
                    # 插入左侧与分隔符
                    self.match_tip_text.insert(tk.END, f"{left}: ")
                    # 插入右侧并加红色高亮
                    self.match_tip_text.insert(
                        tk.END,
                        right + ("\n" if i < len(lines) - 1 else ""),
                        "value",
                    )
                else:
                    self.match_tip_text.insert(
                        tk.END, line + ("\n" if i < len(lines) - 1 else "")
                    )
            self.match_tip_text.configure(state=tk.DISABLED)
        except Exception:
            # 退化为普通文本
            try:
                self.match_tip_text.configure(state=tk.NORMAL)
                self.match_tip_text.delete("1.0", tk.END)
                self.match_tip_text.insert(tk.END, rule_text)
                self.match_tip_text.configure(state=tk.DISABLED)
            except Exception:
                pass

    def _handle_start_listening(self):
        """处理开始监听"""
        if self.on_start_listening:
            self.on_start_listening()

    def _handle_stop_listening(self):
        """处理停止监听"""
        if self.on_stop_listening:
            self.on_stop_listening()

    def _apply_hotkey_settings(self):
        """应用热键设置"""
        new_start = self.start_hotkey_var.get().strip()
        new_stop = self.stop_hotkey_var.get().strip()

        if not new_start or not new_stop:
            messagebox.showerror("错误", "热键不能为空")
            return

        if new_start == new_stop:
            messagebox.showerror("错误", "开始和停止热键不能相同")
            return

        # 更新热键管理器
        self.hotkey_manager.update_hotkeys(new_start, new_stop)

        # 更新按钮显示
        self.update_button_hotkey_display()

        messagebox.showinfo("成功", "热键设置已应用")

    def _start_hotkey_recording(self, entry, var, action_name):
        """开始录制热键"""
        # 显示录制提示
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, "请按键...")
        entry.configure(state="readonly")

        # 绑定键盘事件
        self._recording_entry = entry
        self._recording_var = var
        self._recording_action = action_name

        # 绑定全局键盘事件
        self.parent.bind_all("<Key>", self._on_key_pressed)

        # 设置焦点到输入框
        entry.focus_force()

    def _on_key_pressed(self, event):
        """处理按键事件"""
        if self._recording_entry:
            # 获取按键名称
            key_name = event.keysym

            # 处理特殊按键
            if key_name == "Escape":
                # ESC键取消录制
                self._cancel_hotkey_recording()
                return "break"

            # 更新热键显示
            self._recording_entry.configure(state="normal")
            self._recording_entry.delete(0, tk.END)
            self._recording_entry.insert(0, key_name)
            self._recording_entry.configure(state="readonly")

            # 停止录制
            self._finish_hotkey_recording(key_name)
            return "break"

        return None

    def _cancel_hotkey_recording(self):
        """取消热键录制"""
        if self._recording_entry:
            # 恢复原来的值
            if self._recording_action == "开始":
                self._recording_entry.configure(state="normal")
                self._recording_entry.delete(0, tk.END)
                self._recording_entry.insert(
                    0, self.hotkey_manager.start_hotkey
                )
                self._recording_entry.configure(state="readonly")
            else:
                self._recording_entry.configure(state="normal")
                self._recording_entry.delete(0, tk.END)
                self._recording_entry.insert(
                    0, self.hotkey_manager.stop_hotkey
                )
                self._recording_entry.configure(state="readonly")

        # 清理录制状态
        self._cleanup_recording()

    def _finish_hotkey_recording(self, key_name):
        """完成热键录制"""
        if self._recording_entry:
            # 仅更新显示变量，不更新内部热键变量
            if self._recording_action == "开始":
                self.start_hotkey_var.set(key_name)
            else:
                self.stop_hotkey_var.set(key_name)

        # 清理录制状态
        self._cleanup_recording()

    def _cleanup_recording(self):
        """清理录制状态"""
        # 解绑键盘事件
        self.parent.unbind_all("<Key>")

        # 清理录制变量
        self._recording_entry = None
        self._recording_var = None
        self._recording_action = None

    def _toggle_debug_mode(self):
        """切换调试模式"""
        if self.debug_var:
            Config.DEBUG_MODE = self.debug_var.get()
            if Config.DEBUG_MODE:
                DebugSystem.debug_print("调试模式已开启")
            else:
                DebugSystem.debug_print("调试模式已关闭")


class MainWindow:
    """主窗口类"""

    def __init__(self, root):
        self.root = root
        self._setup_window()

    def _setup_window(self):
        """设置窗口基本属性"""
        self.root.title("剪贴板内容匹配检测器")
        geometry = f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}"
        self.root.geometry(geometry)
        self.root.resizable(False, False)

    def create_main_frame(self):
        """创建主框架"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        return main_frame

    def setup_layout(self):
        """设置布局权重"""
        main_frame = self.root.winfo_children()[0]
        main_frame.columnconfigure(1, weight=0)  # 右侧面板固定宽度
        main_frame.rowconfigure(0, weight=0)  # 第一行固定高度
        main_frame.rowconfigure(1, weight=0)  # 底部面板固定高度
