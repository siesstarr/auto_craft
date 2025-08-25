#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板内容匹配检测器

功能说明：
- 左侧：可动态增删的检测字段输入区，支持纯文本和正则表达式两种模式
- 右侧：实时显示剪贴板内容
- 底部：开始/停止监听剪贴板，支持单条匹配和全部匹配两种模式
- 支持鼠标滚轮滚动左侧区域
- 支持热键控制开始/停止监听

设计原则：
- 保持代码简洁，避免过度设计
- 单一职责原则：每个方法只做一件事
- 配置与逻辑分离，便于维护
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
import re
import json
import os
import logging


# ============================== 常量配置 ==============================
class Config:
    """程序配置常量

    设计说明：
    - 所有配置项集中管理，便于维护
    - 使用有意义的常量名，避免魔法数字
    - 窗口尺寸和UI元素尺寸统一配置
    """

    # 窗口尺寸配置
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 900

    # 左侧面板区域高度配置
    LEFT_INPUT_SECTION_HEIGHT = 210  # 检测字段输入区域高度
    LEFT_SAVED_SECTION_HEIGHT = 210  # 保存字段显示区域高度

    # 按钮尺寸配置
    START_STOP_BUTTON_WIDTH = 120  # 开始/停止按钮宽度
    START_STOP_BUTTON_HEIGHT = 60  # 开始/停止按钮高度

    # 功能配置
    CLIPBOARD_POLL_MS = 500  # 剪贴板轮询间隔（毫秒）
    MAX_FIELDS = 20  # 最大字段数量
    MIN_FIELDS = 1  # 最小字段数量

    # 配置文件路径
    CONFIG_FILE = "fields_config.json"  # 字段配置文件
    HOTKEY_CONFIG_FILE = "hotkey_config.json"  # 热键配置文件

    @classmethod
    def get_config_dir(cls):
        """获取配置目录路径"""
        import os

        return os.environ.get("AUTO_CRAFT_CONFIG_DIR", ".")

    @classmethod
    def get_config_file_path(cls, filename):
        """获取配置文件的完整路径"""
        return os.path.join(cls.get_config_dir(), filename)

    # 热键配置
    DEFAULT_START_HOTKEY = "F8"  # 默认开始监听热键
    DEFAULT_STOP_HOTKEY = "F9"  # 默认停止监听热键

    # 调试配置
    DEBUG_MODE = True  # 开发环境显示调试信息
    DEBUG_LEVEL = logging.DEBUG  # 调试级别


class MainGUI:
    """主窗口应用类

    主要功能：
    1. 动态字段管理：支持1-20个检测字段的增删
    2. 剪贴板监听：实时监听剪贴板内容变化
    3. 内容匹配：支持纯文本和正则表达式两种匹配模式
    4. 匹配策略：支持单条匹配和全部匹配两种策略

    设计原则：
    - 界面创建与业务逻辑分离
    - 配置管理统一化
    - 错误处理友好化
    """

    def __init__(self, root):
        """初始化主窗口

        Args:
            root: Tkinter根窗口对象
        """
        self.root = root
        self._setup_debug_system()
        self._setup_window()
        self._init_data_states()
        self._create_interface()
        self._setup_layout()

    def _setup_debug_system(self):
        """设置调试系统

        设计说明：
        - 开发环境：显示详细调试信息
        - 打包环境：自动隐藏调试信息
        - 支持运行时配置
        """
        # 检测运行环境
        if getattr(sys, 'frozen', False):
            # 打包后的应用程序
            Config.DEBUG_MODE = False
            Config.DEBUG_LEVEL = logging.WARNING

        # 配置日志系统
        if Config.DEBUG_MODE:
            # 开发环境：详细日志 + 文件输出
            logger = logging.getLogger()
            logger.setLevel(Config.DEBUG_LEVEL)

            # 清除现有处理器
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(Config.DEBUG_LEVEL)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # 文件处理器
            file_handler = logging.FileHandler('debug.log', encoding='utf-8')
            file_handler.setLevel(Config.DEBUG_LEVEL)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            self._debug_print(
                "调试系统已初始化，日志将同时输出到控制台和debug.log文件",
                logging.INFO,
            )
        else:
            # 生产环境：只记录警告和错误
            logging.basicConfig(
                level=logging.WARNING,
                format='%(asctime)s - %(levelname)s - %(message)s',
            )

    def _setup_window(self):
        """设置窗口基本属性"""
        self.root.title("剪贴板内容匹配检测器")
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.resizable(False, False)

    def _init_data_states(self):
        """初始化数据状态变量

        设计说明：
        - 所有状态变量集中初始化，便于管理
        - 使用有意义的变量名，提高代码可读性
        - 避免在方法中重复创建变量
        """
        # 动态字段数据：每个字段包含输入文本和模式选择
        self.fields = []

        # 保存的字段显示变量
        self.saved_display_vars = []

        # 匹配模式选择：single=单条匹配, all=全部匹配
        self.match_mode_var = tk.StringVar(value="single")

        # 剪贴板监听状态
        self._clipboard_listening = False
        self._clipboard_after_id = None
        self._last_clipboard_text = ""

        # 热键配置
        self.start_hotkey = Config.DEFAULT_START_HOTKEY
        self.stop_hotkey = Config.DEFAULT_STOP_HOTKEY
        self._hotkey_listening = False

    def _create_interface(self):
        """创建主界面

        设计说明：
        - 界面创建顺序：左侧面板 -> 右侧面板 -> 底部面板
        - 热键初始化在所有界面创建完成后进行
        - 使用网格布局，便于响应式设计
        """
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 创建各个面板
        self._create_left_panel(main_frame)
        self._create_right_panel(main_frame)
        self._create_bottom_panel(main_frame)

        # 在所有界面创建完成后初始化热键
        self._start_hotkey_on_init()

    def _setup_layout(self):
        """设置布局权重

        设计说明：
        - 主框架：所有区域都固定大小，保持布局稳定
        - 右侧面板：固定宽度，内容过多时显示滚动条
        - 底部面板：固定高度，不参与扩展
        """
        main_frame = self.root.winfo_children()[0]
        main_frame.columnconfigure(1, weight=0)  # 右侧面板固定宽度
        main_frame.rowconfigure(0, weight=0)  # 第一行固定高度
        main_frame.rowconfigure(1, weight=0)  # 底部面板固定高度

    # ======================== 左侧面板：字段管理 ========================
    def _create_left_panel(self, main_frame):
        """创建左侧字段管理面板

        设计说明：
        - 将复杂的界面创建逻辑拆分为多个小方法
        - 每个方法负责一个特定的UI区域
        - 使用统一的布局管理，便于维护
        """
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

        # 初始化至少一个字段
        self._add_field()

        # 加载保存的配置
        self._load_saved_config()

    def _create_fields_title(self):
        """创建字段管理标题"""
        ttk.Label(self.left_frame, text="检测字段（1-20）").grid(
            row=0, column=0, sticky=tk.W
        )

    def _create_fields_input_section(self):
        """创建检测字段输入区域"""
        # 动态字段输入区域（可滚动）
        fields_section, self.fields_container = self._create_scrollable_area(
            self.left_frame, height=Config.LEFT_INPUT_SECTION_HEIGHT
        )
        fields_section.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.fields_container.columnconfigure(1, weight=1)

    def _create_save_button(self):
        """创建保存按钮"""
        self.submit_button = ttk.Button(
            self.left_frame, text="保存字段", command=self._handle_save_click
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
        saved_section, self.saved_container = self._create_scrollable_area(
            self.left_frame, height=Config.LEFT_SAVED_SECTION_HEIGHT
        )
        saved_section.grid(row=8, column=0, sticky=(tk.W, tk.E))
        self.saved_container.columnconfigure(0, weight=1)

    def _create_field_controls(self):
        """创建字段控制区域"""
        controls = ttk.Frame(self.left_frame)
        controls.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(6, 6))

        # 新增字段按钮
        self.add_field_btn = ttk.Button(
            controls, text="新增字段", command=self._add_field
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
            import_export_frame, text="导入字段", command=self._import_fields
        )
        self.import_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        # 导出字段按钮
        self.export_btn = ttk.Button(
            import_export_frame, text="导出字段", command=self._export_fields
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

    # ======================== 右侧面板：剪贴板显示 ========================
    def _create_right_panel(self, main_frame):
        """创建右侧剪贴板显示面板

        设计说明：
        - 使用固定宽度，保持布局稳定
        - 文本区域支持滚动条，内容过多时自动显示
        - 使用ScrolledText组件，内置滚动功能
        """
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

        # 初始化显示内容
        initial = self._get_clipboard_text()
        self._set_display_text(initial)
        self._last_clipboard_text = initial

        # 设置布局权重 - 文本区域填充整个框架
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

    # ======================== 底部面板：执行控制 ========================
    def _create_bottom_panel(self, main_frame):
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
            f"开始监听 ({self.start_hotkey})",
            self._start_clipboard_listen,
            0,
        )

        # 停止监听按钮
        self.stop_btn = self._create_action_button(
            bottom_frame,
            f"停止监听 ({self.stop_hotkey})",
            self._stop_clipboard_listen,
            1,
        )
        self.stop_btn.configure(state=tk.DISABLED)

        # 热键设置区域
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
        self.start_hotkey_var = tk.StringVar(value=self.start_hotkey)

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
        self.stop_hotkey_var = tk.StringVar(value=self.stop_hotkey)

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

    def _clear_match_tip(self):
        """清空匹配提示区域"""
        try:
            self.match_tip_text.configure(state=tk.NORMAL)
            self.match_tip_text.delete("1.0", tk.END)
            self.match_tip_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    def _set_match_tip(self, rule_text: str):
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

    def _setup_button_styles(self):
        """设置按钮样式"""
        style = ttk.Style()
        style.configure("Start.TButton", font=("Helvetica", 14))
        style.configure("Stop.TButton", font=("Helvetica", 14))

    def _create_action_button(self, parent, text, command, column):
        """创建操作按钮

        Args:
            parent: 父容器
            text: 按钮文本
            command: 点击命令
            column: 列位置

        Returns:
            创建的按钮对象
        """
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

    # ======================== 字段管理方法 ========================
    def _add_field(self):
        """新增一个检测字段"""
        if len(self.fields) >= Config.MAX_FIELDS:
            self._debug_print(
                f"已达到最大字段数量限制: {Config.MAX_FIELDS}", logging.WARNING
            )
            return

        # 创建字段数据
        text_var = tk.StringVar()
        mode_var = tk.StringVar(value="text")
        self.fields.append({"text": text_var, "mode": mode_var})

        # 创建对应的保存显示变量
        mode_label = self._get_mode_label(mode_var.get())
        self.saved_display_vars.append(
            tk.StringVar(
                value=f"字段{len(self.fields)}（{mode_label}）: （空）"
            )
        )

        self._debug_print(
            f"新增字段成功，当前字段数量: {len(self.fields)}", logging.INFO
        )

        # 重新渲染界面
        self._reflow_fields()
        self._reflow_saved_display()
        self._update_controls()

    def _import_fields(self):
        """导入字段配置"""
        try:
            self._debug_print("开始导入字段配置", logging.INFO)

            # 打开文件选择对话框
            filename = filedialog.askopenfilename(
                title="选择要导入的字段配置文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            )

            if not filename:
                self._debug_print("用户取消导入操作", logging.INFO)
                return

            self._debug_print(f"选择导入文件: {filename}", logging.INFO)

            # 读取JSON文件
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 验证数据格式
            if not isinstance(data, dict) or 'fields' not in data:
                self._debug_print(
                    "文件格式不正确，缺少fields字段", logging.ERROR
                )
                messagebox.showerror("错误", "文件格式不正确，缺少fields字段")
                return

            fields_data = data['fields']
            if not isinstance(fields_data, list):
                self._debug_print("fields字段必须是数组格式", logging.ERROR)
                messagebox.showerror("错误", "fields字段必须是数组格式")
                return

            self._debug_print(
                f"文件验证通过，包含 {len(fields_data)} 个字段", logging.INFO
            )

            # 清空现有字段
            old_count = len(self.fields)
            self.fields.clear()
            self.saved_display_vars.clear()
            self._debug_print(f"清空现有字段: {old_count} -> 0", logging.INFO)

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
                    self.fields.append({"text": text_var, "mode": mode_var})

                    # 创建对应的保存显示变量
                    mode_label = self._get_mode_label(mode_var.get())
                    display_text = (
                        field_data['text'] if field_data['text'] else '（空）'
                    )
                    self.saved_display_vars.append(
                        tk.StringVar(
                            value=f"字段{len(self.fields)}（{mode_label}）: "
                            f"{display_text}"
                        )
                    )
                    imported_count += 1

            self._debug_print(
                f"成功导入 {imported_count} 个字段", logging.INFO
            )

            # 如果没有字段，至少添加一个
            if not self.fields:
                self._debug_print("导入后无字段，添加默认字段", logging.INFO)
                self._add_field()

            # 重新渲染界面
            self._reflow_fields()
            self._reflow_saved_display()
            self._update_controls()

            messagebox.showinfo("成功", f"成功导入 {len(self.fields)} 个字段")

        except Exception as e:
            self._debug_print(f"导入失败: {str(e)}", logging.ERROR)
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _export_fields(self):
        """导出字段配置"""
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

            for field in self.fields:
                export_data["fields"].append(
                    {"text": field["text"].get(), "mode": field["mode"].get()}
                )

            # 写入JSON文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo(
                "成功", f"成功导出 {len(self.fields)} 个字段到 {filename}"
            )

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def _load_saved_config(self):
        """加载保存的字段配置"""
        try:
            if os.path.exists(Config.CONFIG_FILE):
                with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'fields' in data:
                    fields_data = data['fields']
                    if isinstance(fields_data, list):
                        # 清空现有字段
                        self.fields.clear()
                        self.saved_display_vars.clear()

                        # 加载字段数据
                        for field_data in fields_data:
                            if (
                                isinstance(field_data, dict)
                                and 'text' in field_data
                                and 'mode' in field_data
                            ):
                                text_var = tk.StringVar(
                                    value=field_data['text']
                                )
                                mode_var = tk.StringVar(
                                    value=field_data['mode']
                                )
                                self.fields.append(
                                    {"text": text_var, "mode": mode_var}
                                )

                                # 创建对应的保存显示变量
                                mode_label = self._get_mode_label(
                                    mode_var.get()
                                )
                                display_text = (
                                    field_data['text']
                                    if field_data['text']
                                    else '（空）'
                                )
                                self.saved_display_vars.append(
                                    tk.StringVar(
                                        value=f"字段{len(self.fields)}（{mode_label}）: "
                                        f"{display_text}"
                                    )
                                )

                        # 如果没有字段，至少添加一个
                        if not self.fields:
                            self._add_field()

                        # 重新渲染界面
                        self._reflow_fields()
                        self._reflow_saved_display()
                        self._update_controls()

        except Exception as e:
            # 如果加载失败，至少添加一个默认字段
            if not self.fields:
                self._add_field()

    def _save_config_to_file(self):
        """保存字段配置到文件"""
        try:
            # 准备保存数据
            save_data = {"fields": []}

            for field in self.fields:
                save_data["fields"].append(
                    {"text": field["text"].get(), "mode": field["mode"].get()}
                )

            # 写入配置文件
            with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            # 保存失败时不显示错误，避免影响用户体验
            pass

    # ======================== 热键控制方法 ========================
    def _update_button_hotkey_display(self):
        """更新按钮上的热键显示和输入框中的值

        设计说明：
        - 统一更新按钮文本和输入框值
        - 确保界面显示与实际配置一致
        """
        # 更新按钮文本
        self.start_btn.configure(text=f"开始监听 ({self.start_hotkey})")
        self.stop_btn.configure(text=f"停止监听 ({self.stop_hotkey})")

        # 同时更新输入框中的值
        if hasattr(self, 'start_hotkey_var'):
            self.start_hotkey_var.set(self.start_hotkey)
        if hasattr(self, 'stop_hotkey_var'):
            self.stop_hotkey_var.set(self.stop_hotkey)

    def _start_hotkey_listening(self):
        """启动热键监听

        设计说明：
        - 使用keyboard库实现真正的全局热键监听
        - 即使程序失去焦点也能响应热键
        - 支持功能键和普通键的绑定
        - 统一的绑定模式，便于维护
        """
        if self._hotkey_listening:
            return

        try:
            import pynput
            from pynput import keyboard as pynput_keyboard

            self._hotkey_listening = True

            # 使用pynput库绑定全局热键
            # 对于功能键，使用Listener来监听按键事件
            def on_press(key):
                try:
                    if hasattr(key, 'char'):
                        # 普通字符键
                        if key.char == self.start_hotkey:
                            self._on_start_hotkey()
                        elif key.char == self.stop_hotkey:
                            self._on_stop_hotkey()
                    else:
                        # 功能键
                        key_name = str(key).replace('Key.', '')
                        if key_name == self.start_hotkey.lower():
                            self._on_start_hotkey()
                        elif key_name == self.stop_hotkey.lower():
                            self._on_stop_hotkey()
                except Exception as e:
                    self._debug_print(f"热键处理错误: {e}", logging.ERROR)
            
            self._pynput_listener = pynput_keyboard.Listener(on_press=on_press)
            self._pynput_listener.start()

            self._debug_print(
                f"全局热键监听已启动: {self.start_hotkey}, {self.stop_hotkey}",
                logging.INFO,
            )

        except ImportError:
            # 如果keyboard库不可用，回退到Tkinter绑定
            self._debug_print(
                "keyboard库不可用，使用Tkinter绑定（仅窗口有焦点时有效）",
                logging.WARNING,
            )

            self._hotkey_listening = True

            # 绑定全局键盘事件
            self.root.bind_all(
                f"<Key-{self.start_hotkey}>", lambda e: self._on_start_hotkey()
            )
            self.root.bind_all(
                f"<Key-{self.stop_hotkey}>", lambda e: self._on_stop_hotkey()
            )

            # 对于F8和F9这样的功能键，使用特殊绑定
            if self.start_hotkey == "F8":
                self.root.bind_all(
                    "<KeyPress-F8>", lambda e: self._on_start_hotkey()
                )
            if self.stop_hotkey == "F9":
                self.root.bind_all(
                    "<KeyPress-F9>", lambda e: self._on_stop_hotkey()
                )
        except Exception as e:
            self._debug_print(f"启动热键监听失败: {e}", logging.ERROR)
            self._hotkey_listening = False

    def _stop_hotkey_listening(self):
        """停止热键监听

        设计说明：
        - 安全地解绑所有相关事件
        - 优先使用keyboard库，回退到Tkinter绑定
        - 使用try-except避免解绑失败
        """
        if not self._hotkey_listening:
            return

        self._hotkey_listening = False

        # 解绑键盘事件
        try:
            from pynput import keyboard as pynput_keyboard

            # 使用pynput库停止全局热键监听
            if hasattr(self, '_pynput_listener'):
                self._pynput_listener.stop()
                self._pynput_listener = None

            self._debug_print(
                f"全局热键监听已停止: {self.start_hotkey}, {self.stop_hotkey}",
                logging.INFO,
            )

        except ImportError:
            # 如果keyboard库不可用，使用Tkinter解绑
            try:
                self.root.unbind_all(f"<Key-{self.start_hotkey}>")
                self.root.unbind_all(f"<Key-{self.stop_hotkey}>")

                if self.start_hotkey == "F8":
                    self.root.unbind_all("<KeyPress-F8>")
                if self.stop_hotkey == "F9":
                    self.root.unbind_all("<KeyPress-F9>")
            except Exception:
                pass
        except Exception as e:
            self._debug_print(f"停止热键监听失败: {e}", logging.ERROR)

    def _on_start_hotkey(self):
        """开始监听热键回调

        设计说明：
        - 在主线程中执行UI操作，避免线程安全问题
        - 使用after方法确保线程安全
        """
        self.root.after(0, self._start_clipboard_listen)

    def _on_stop_hotkey(self):
        """停止监听热键回调

        设计说明：
        - 在主线程中执行UI操作，避免线程安全问题
        - 使用after方法确保线程安全
        """
        self.root.after(0, self._stop_clipboard_listen)

    def _load_hotkey_config(self):
        """加载热键配置

        设计说明：
        - 统一的配置加载逻辑
        - 自动验证和修正无效配置
        - 失败时回退到默认值
        """
        try:
            config_path = Config.get_config_file_path(
                Config.HOTKEY_CONFIG_FILE
            )
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    if 'start_hotkey' in data:
                        self.start_hotkey = data['start_hotkey']
                    if 'stop_hotkey' in data:
                        self.stop_hotkey = data['stop_hotkey']

        except Exception as e:
            self._debug_print(f"加载热键配置失败: {e}", logging.ERROR)
            # 加载失败时设置为默认快捷键
            self._set_default_hotkeys()
        else:
            # 验证加载的热键是否有效，如果无效则设置为默认值
            if not self._is_valid_hotkey(
                self.start_hotkey
            ) or not self._is_valid_hotkey(self.stop_hotkey):
                self._debug_print(
                    "加载的热键配置无效，使用默认快捷键", logging.WARNING
                )
                self._set_default_hotkeys()

    def _debug_print(self, message, level=logging.INFO):
        """调试输出方法

        设计说明：
        - 开发环境：显示调试信息
        - 打包环境：自动隐藏
        - 支持不同级别的调试信息

        Args:
            message: 调试信息
            level: 日志级别
        """
        if Config.DEBUG_MODE:
            logging.log(level, message)

    def _set_default_hotkeys(self):
        """设置默认快捷键并保存到配置文件

        设计说明：
        - 自动修正无效配置
        - 保存修正后的配置，避免重复修正
        - 提供清晰的用户反馈
        """
        self.start_hotkey = Config.DEFAULT_START_HOTKEY
        self.stop_hotkey = Config.DEFAULT_STOP_HOTKEY
        self._debug_print(
            f"已设置默认快捷键: 开始={self.start_hotkey}, 停止={self.stop_hotkey}"
        )

        # 保存默认快捷键到配置文件
        try:
            self._save_hotkey_config()
            self._debug_print("已保存默认快捷键到配置文件")
        except Exception as e:
            self._debug_print(f"保存默认快捷键配置失败: {e}", logging.ERROR)

    def _is_valid_hotkey(self, hotkey):
        """验证热键是否有效

        设计说明：
        - 预定义有效热键列表，避免无效输入
        - 支持功能键、字母键、数字键和特殊键
        - 严格的类型检查，提高安全性

        Args:
            hotkey: 要验证的热键字符串

        Returns:
            bool: 热键是否有效
        """
        if not hotkey or not isinstance(hotkey, str):
            return False

        # 检查是否是有效的热键格式
        valid_hotkeys = [
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "F10",
            "F11",
            "F12",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "Return",
            "Space",
            "Tab",
            "Escape",
            "BackSpace",
            "Delete",
            "Insert",
            "Home",
            "End",
            "Page_Up",
            "Page_Down",
            "Up",
            "Down",
            "Left",
            "Right",
        ]

        return hotkey in valid_hotkeys

    def _save_hotkey_config(self):
        """保存热键配置

        设计说明：
        - 统一的配置保存逻辑
        - 使用JSON格式，便于人工编辑和调试
        - 错误处理友好，不影响用户体验
        """
        try:
            save_data = {
                "start_hotkey": self.start_hotkey,
                "stop_hotkey": self.stop_hotkey,
            }

            config_path = Config.get_config_file_path(
                Config.HOTKEY_CONFIG_FILE
            )
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self._debug_print(f"保存热键配置失败: {e}", logging.ERROR)

    def _start_hotkey_on_init(self):
        """初始化时启动热键监听

        设计说明：
        - 在界面创建完成后初始化热键
        - 确保所有UI组件都已创建
        - 统一的初始化流程
        """
        # 加载热键配置
        self._load_hotkey_config()

        # 启动热键监听
        self._start_hotkey_listening()

        # 更新按钮热键显示
        self._update_button_hotkey_display()

    def _apply_hotkey_settings(self):
        """应用热键设置

        设计说明：
        - 从输入框获取热键配置
        - 验证用户输入的有效性
        - 更新内部热键变量
        - 重新启动热键监听
        - 保存到配置文件
        - 提供用户反馈
        """
        new_start = self.start_hotkey_var.get().strip()
        new_stop = self.stop_hotkey_var.get().strip()

        if not new_start or not new_stop:
            messagebox.showerror("错误", "热键不能为空")
            return

        if new_start == new_stop:
            messagebox.showerror("错误", "开始和停止热键不能相同")
            return

        # 停止当前热键监听
        self._stop_hotkey_listening()

        # 更新热键
        self.start_hotkey = new_start
        self.stop_hotkey = new_stop

        # 保存到配置文件
        self._save_hotkey_config()

        # 重新启动热键监听
        self._start_hotkey_listening()

        # 更新按钮显示
        self._update_button_hotkey_display()

        messagebox.showinfo("成功", "热键设置已应用")

    def _remove_field(self, index):
        """删除指定索引的检测字段

        Args:
            index: 要删除的字段索引
        """
        if len(self.fields) <= Config.MIN_FIELDS:
            self._debug_print(
                f"已达到最小字段数量限制: {Config.MIN_FIELDS}", logging.WARNING
            )
            return

        if 0 <= index < len(self.fields):
            # 删除字段数据
            del self.fields[index]

            # 删除对应的保存显示变量
            if 0 <= index < len(self.saved_display_vars):
                del self.saved_display_vars[index]

            self._debug_print(
                f"删除字段{index + 1}成功，当前字段数量: {len(self.fields)}",
                logging.INFO,
            )

            # 重新编号并渲染
            self._renumber_saved_display_vars()
            self._reflow_fields()
            self._reflow_saved_display()
            self._update_controls()

    def _reflow_fields(self):
        """重新渲染动态字段输入界面"""
        # 清空现有内容
        for child in self.fields_container.winfo_children():
            child.destroy()

        self._delete_buttons = []

        # 为每个字段创建输入界面
        for idx, field in enumerate(self.fields):
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
                command=lambda i=idx: self._remove_field(i),
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

    def _reflow_saved_display(self):
        """重新渲染保存字段显示界面"""
        # 清空现有内容
        for child in self.saved_container.winfo_children():
            child.destroy()

        # 为每个保存项创建显示和清除按钮
        for idx, var in enumerate(self.saved_display_vars):
            ttk.Label(self.saved_container, textvariable=var).grid(
                row=idx, column=0, sticky=(tk.W, tk.E)
            )

            ttk.Button(
                self.saved_container,
                text="清除",
                command=lambda i=idx: self._clear_saved(i),
            ).grid(row=idx, column=1, sticky=tk.E, padx=(8, 0))

    def _renumber_saved_display_vars(self):
        """重新编号保存字段显示变量"""
        count = min(len(self.saved_display_vars), len(self.fields))

        for i in range(count):
            var = self.saved_display_vars[i]
            field = self.fields[i]
            mode_label = self._get_mode_label(field["mode"].get())

            # 提取原有内容
            old = var.get()
            base = self._strip_match_suffix(old)
            content = "（空）"
            if ": " in base:
                content = base.split(": ", 1)[1]

            # 重新设置编号
            var.set(f"字段{i + 1}（{mode_label}）: {content}")

        # 调整数组长度
        if len(self.saved_display_vars) > len(self.fields):
            self.saved_display_vars = self.saved_display_vars[
                : len(self.fields)
            ]
        elif len(self.saved_display_vars) < len(self.fields):
            for i in range(len(self.saved_display_vars), len(self.fields)):
                mode_label = self._get_mode_label(self.fields[i]["mode"].get())
                self.saved_display_vars.append(
                    tk.StringVar(value=f"字段{i + 1}（{mode_label}）: （空）")
                )

    def _update_controls(self):
        """更新控制按钮状态"""
        count = len(self.fields)

        # 更新字段计数
        self.fields_count_label.configure(text=f"共 {count} 个字段")

        # 更新新增按钮状态
        self.add_field_btn.configure(
            state=(tk.DISABLED if count >= Config.MAX_FIELDS else tk.NORMAL)
        )

        # 更新删除按钮状态
        del_state = tk.DISABLED if count <= Config.MIN_FIELDS else tk.NORMAL
        for btn in getattr(self, "_delete_buttons", []):
            btn.configure(state=del_state)

    # ======================== 剪贴板监听方法 ========================
    def _start_clipboard_listen(self):
        """开始剪贴板监听"""
        if self._clipboard_listening:
            self._debug_print("剪贴板监听已在运行中", logging.WARNING)
            return

        # 验证是否有保存的字段
        if not self._has_any_saved_value():
            self._debug_print(
                "没有保存的非空字段，无法开始监听", logging.WARNING
            )
            messagebox.showwarning("提示", "请先在左侧保存至少一个非空字段。")
            return

        self._debug_print("开始剪贴板监听", logging.INFO)

        # 清空匹配提示
        self._clear_match_tip()

        # 清空剪贴板内容
        try:
            self.root.clipboard_clear()
        except tk.TclError:
            pass

        # 清空右侧显示内容
        self._set_display_text("（等待剪贴板内容...）")

        # 重置剪贴板状态
        self._last_clipboard_text = ""

        # 启动监听
        self._clipboard_listening = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

        # 开始轮询
        self._poll_clipboard()

    def _stop_clipboard_listen(self):
        """停止剪贴板监听"""
        if not self._clipboard_listening:
            self._debug_print("剪贴板监听未在运行", logging.WARNING)
            return

        self._debug_print("停止剪贴板监听", logging.INFO)

        # 停止监听
        self._clipboard_listening = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)

        # 取消定时器
        if self._clipboard_after_id is not None:
            try:
                self.root.after_cancel(self._clipboard_after_id)
            except Exception:
                pass
            self._clipboard_after_id = None

    def _poll_clipboard(self):
        """轮询剪贴板变化"""
        if not self._clipboard_listening:
            return

        # 获取当前剪贴板内容
        current = self._get_clipboard_text()

        # 检查内容是否变化
        if current != self._last_clipboard_text:
            self._debug_print(
                f"检测到剪贴板内容变化，长度: {len(current)}", logging.DEBUG
            )
            self._set_display_text(current)
            self._last_clipboard_text = current

            # 进行匹配检测（命中会在内部停止监听）
            self._process_matches(current)
        else:
            self._debug_print("剪贴板内容无变化", logging.DEBUG)

        # 继续轮询（若在匹配中已停止监听，下一次进入会直接return）
        self._clipboard_after_id = self.root.after(
            Config.CLIPBOARD_POLL_MS, self._poll_clipboard
        )

    def _process_matches(self, clipboard_text):
        """处理剪贴板内容匹配

        Args:
            clipboard_text: 剪贴板文本内容
        """
        self._debug_print(
            f"开始处理剪贴板内容匹配，内容长度: {len(clipboard_text)}",
            logging.INFO,
        )

        # 查找所有匹配项
        matches = self._find_matches(clipboard_text)

        if not matches:
            self._debug_print("未找到任何匹配项", logging.INFO)
            return

        self._debug_print(f"找到 {len(matches)} 个匹配项", logging.INFO)

        # 根据匹配策略处理
        match_mode = self.match_mode_var.get()
        self._debug_print(f"匹配策略: {match_mode}", logging.INFO)

        if match_mode == "single":
            # 单条匹配：匹配到任意一条即停止
            self._handle_single_match(matches)
        else:
            # 全部匹配：需匹配所有非空项才停止
            self._handle_all_match(matches)

    def _handle_single_match(self, matches):
        """处理单条匹配结果

        Args:
            matches: 匹配结果列表
        """
        # 构建匹配提示文本
        match_texts = []
        for idx, mode_label, value in matches:
            match_texts.append(f"字段{idx + 1}（{mode_label}）: {value}")

        rule_text = "匹配:\n" + "\n".join(match_texts)
        self._notify_match(rule_text)

    def _handle_all_match(self, matches):
        """处理全部匹配结果

        Args:
            matches: 匹配结果列表
        """
        # 检查是否匹配所有非空项
        non_empty_count = self._count_non_empty_saved_fields()

        if len(matches) >= non_empty_count:
            # 构建匹配提示文本
            match_texts = []
            for idx, mode_label, value in matches:
                match_texts.append(f"字段{idx + 1}（{mode_label}）: {value}")

            rule_text = "全部匹配:\n" + "\n".join(match_texts)
            self._notify_match(rule_text)

    def _notify_match(self, rule_text):
        """匹配命中时的统一通知：前置窗口、提示音并停止监听

        Args:
            rule_text: 要显示的匹配提示文本
        """
        # 使用Text设置提示并高亮 value
        self._set_match_tip(rule_text)

        # 前置窗口到最前并聚焦
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            # 稍后恢复常规置顶状态，避免一直压在最上层
            self.root.after(
                300, lambda: self.root.attributes("-topmost", False)
            )
            self.root.focus_force()
        except Exception:
            pass

        # 更尖锐的警报声
        self._play_sharp_alert()

        # 停止监听
        self._stop_clipboard_listen()

    def _play_sharp_alert(self):
        """播放更尖锐的警报声（跨平台实现）"""
        try:
            if sys.platform.startswith("win"):
                # Windows: 使用高频短促多次蜂鸣
                import winsound  # type: ignore

                for _ in range(3):
                    winsound.Beep(2200, 140)  # 2200Hz, 140ms
                    winsound.Beep(2600, 120)  # 2600Hz, 120ms
            else:
                # 其他平台: 使用多次系统铃声，形成连环警报效果
                # 连续响3次，每次间隔100ms
                self.root.bell()
                self.root.after(120, self.root.bell)
                self.root.after(240, self.root.bell)
                self.root.after(360, self.root.bell)
        except Exception:
            try:
                self._debug_print("\a\a\a", logging.DEBUG)  # 控制台铃声兜底
            except Exception:
                pass

    # ======================== 工具方法 ========================
    def _get_mode_label(self, mode_value):
        """获取模式的中文标签

        设计说明：
        - 简单的映射函数，避免复杂的逻辑
        - 支持扩展更多模式类型

        Args:
            mode_value: 模式值（'text' 或 'regex'）

        Returns:
            str: 中文标签
        """
        return "文本" if mode_value == "text" else "正则"

    def _strip_match_suffix(self, text):
        """去除文本中的匹配状态后缀

        设计说明：
        - 使用正则表达式清理文本
        - 支持多种后缀格式
        - 保持原始文本完整性

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        return re.sub(r" \[(匹配|不匹配|无效正则)\]$", "", text)

    def _extract_mode_and_value(self, saved_text):
        """从保存的字段文本中提取模式和值

        设计说明：
        - 解析格式化的字段文本
        - 提取模式和实际值
        - 处理边界情况

        Args:
            saved_text: 保存的字段文本

        Returns:
            tuple: (模式标签, 值) 元组
        """
        base = self._strip_match_suffix(saved_text)
        mode_label = "文本"
        value = ""

        # 提取模式（中文括号内）
        left = base.find("（")
        right = base.find("）")
        if left != -1 and right != -1 and right > left:
            mode_label = base[left + 1 : right]

        # 提取冒号后的内容
        if ": " in base:
            value = base.split(": ", 1)[1]

        return mode_label, value

    def _find_matches(self, clipboard_text):
        """查找剪贴板内容与保存字段的匹配项

        设计说明：
        - 清晰的匹配逻辑，避免过度复杂的处理
        - 统一的错误处理，提高稳定性
        - 支持纯文本和正则表达式两种模式

        Args:
            clipboard_text: 剪贴板文本内容

        Returns:
            list: 匹配结果列表 [(index, mode_label, value), ...]
        """
        self._debug_print(
            f"开始查找匹配项，剪贴板内容: {clipboard_text[:50]}...",
            logging.DEBUG,
        )

        matches = []

        for idx, var in enumerate(self.saved_display_vars):
            # 提取字段信息
            base = self._strip_match_suffix(var.get())
            mode_label, value = self._extract_mode_and_value(base)

            # 跳过空值
            if not value or value == "（空）":
                self._debug_print(
                    f"字段{idx + 1}为空，跳过匹配", logging.DEBUG
                )
                continue

            self._debug_print(
                f"检查字段{idx + 1}（{mode_label}）: {value}", logging.DEBUG
            )

            # 根据模式进行匹配
            if mode_label == "文本":
                # 纯文本匹配
                if value in clipboard_text:
                    self._debug_print(
                        f"字段{idx + 1}文本匹配成功: {value}", logging.INFO
                    )
                    matches.append((idx, mode_label, value))
                else:
                    self._debug_print(
                        f"字段{idx + 1}文本匹配失败: {value}", logging.DEBUG
                    )
            else:
                # 正则表达式匹配
                try:
                    if re.search(
                        value, clipboard_text, re.DOTALL | re.MULTILINE
                    ):
                        self._debug_print(
                            f"字段{idx + 1}正则匹配成功: {value}", logging.INFO
                        )
                        matches.append((idx, mode_label, value))
                    else:
                        self._debug_print(
                            f"字段{idx + 1}正则匹配失败: {value}",
                            logging.DEBUG,
                        )
                except re.error as e:
                    # 正则表达式错误时跳过，不影响其他字段匹配
                    self._debug_print(
                        f"字段{idx + 1}正则表达式错误: {e}", logging.ERROR
                    )
                    continue

        self._debug_print(
            f"匹配查找完成，共找到 {len(matches)} 个匹配项", logging.INFO
        )
        return matches

    def _count_non_empty_saved_fields(self):
        """统计非空的保存字段数量

        设计说明：
        - 简单的计数逻辑
        - 过滤空值和占位符
        - 用于匹配策略判断

        Returns:
            int: 非空字段数量
        """
        count = 0
        for var in self.saved_display_vars:
            text = self._strip_match_suffix(var.get())
            content = text.split(": ", 1)[1] if ": " in text else text
            if content and content != "（空）":
                count += 1
        return count

    def _has_any_saved_value(self):
        """检查是否有任何保存的非空字段

        设计说明：
        - 基于计数的简单判断
        - 用于验证监听条件
        - 避免空字段监听

        Returns:
            bool: True 如果有非空字段，否则 False
        """
        return self._count_non_empty_saved_fields() > 0

    def _get_clipboard_text(self):
        """安全地获取剪贴板文本内容

        设计说明：
        - 异常安全的剪贴板访问
        - 失败时返回空字符串
        - 避免程序崩溃

        Returns:
            str: 剪贴板文本内容，如果获取失败则返回空字符串
        """
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            text = ""
        return text

    def _set_display_text(self, text):
        """在右侧显示区域设置文本内容

        设计说明：
        - 安全的文本更新
        - 保持只读状态
        - 统一的显示格式

        Args:
            text: 要显示的文本
        """
        self.display_text.configure(state=tk.NORMAL)
        self.display_text.delete("1.0", tk.END)
        self.display_text.insert(tk.END, text)
        self.display_text.configure(state=tk.DISABLED)

    # ======================== 滚动区域支持 ========================
    def _create_scrollable_area(self, parent, height):
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
        self._enable_mousewheel(canvas, interior)

        return container, interior

    def _enable_mousewheel(self, canvas, interior):
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

    # ======================== 交互方法 ========================
    def _handle_save_click(self):
        """处理保存按钮点击事件"""
        self._debug_print("开始保存字段配置", logging.INFO)

        # 保存前校验正则表达式有效性
        for i, field in enumerate(self.fields, start=1):
            value = field["text"].get().strip()
            mode_label = self._get_mode_label(field["mode"].get())

            if mode_label == "正则" and value:
                try:
                    re.compile(value)
                    self._debug_print(
                        f"字段{i}正则表达式验证通过: {value}", logging.DEBUG
                    )
                except re.error as e:
                    self._debug_print(
                        f"字段{i}正则表达式验证失败: {value}, 错误: {e}",
                        logging.ERROR,
                    )
                    messagebox.showwarning("提示", f"字段{i} 的正则无效: {e}")
                    return

        # 确保保存显示变量数量正确
        if len(self.saved_display_vars) != len(self.fields):
            self._debug_print(
                f"调整保存显示变量数量: {len(self.saved_display_vars)} -> {len(self.fields)}",
                logging.DEBUG,
            )
            self.saved_display_vars = [
                tk.StringVar() for _ in range(len(self.fields))
            ]

        # 保存所有字段
        saved_count = 0
        for idx, field in enumerate(self.fields, start=1):
            value = field["text"].get().strip()
            mode_label = self._get_mode_label(field["mode"].get())
            text = value if value else "（空）"

            self.saved_display_vars[idx - 1].set(
                f"字段{idx}（{mode_label}）: {text}"
            )
            if value:
                saved_count += 1

        self._debug_print(
            f"字段保存完成，共 {len(self.fields)} 个字段，其中 {saved_count} 个有内容",
            logging.INFO,
        )

        # 重新渲染保存显示区域
        self._reflow_saved_display()

        # 保存配置到文件
        self._save_config_to_file()

    def _clear_saved(self, index):
        """清除指定索引的保存字段

        Args:
            index: 要清除的字段索引
        """
        if 0 <= index < len(self.fields):
            # 清空输入框内容
            self.fields[index]["text"].set("")

            # 更新保存显示
            mode_label = self._get_mode_label(self.fields[index]["mode"].get())
            self.saved_display_vars[index].set(
                f"字段{index + 1}（{mode_label}）: （空）"
            )

    def _start_hotkey_recording(self, entry, var, action_name):
        """开始录制热键

        设计说明：
        - 简化的录制机制，避免复杂的状态管理
        - 直接绑定键盘事件，减少中间环节
        - 清晰的用户反馈

        Args:
            entry: 热键输入框
            var: 对应的StringVar变量
            action_name: 动作名称（"开始"或"停止"）
        """
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
        self.root.bind_all("<Key>", self._on_key_pressed)

        # 设置焦点到输入框
        entry.focus_force()

    def _on_key_pressed(self, event):
        """处理按键事件

        设计说明：
        - 简化的按键处理逻辑
        - 支持ESC键取消录制
        - 直接更新输入框显示

        Args:
            event: 键盘事件对象

        Returns:
            str: 事件处理结果，"break"表示事件已处理
        """
        if hasattr(self, '_recording_entry') and self._recording_entry:
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
        """取消热键录制

        设计说明：
        - 恢复原始热键值
        - 清理录制状态
        - 用户友好的取消机制
        """
        if hasattr(self, '_recording_entry') and self._recording_entry:
            # 恢复原来的值
            if self._recording_action == "开始":
                self._recording_entry.configure(state="normal")
                self._recording_entry.delete(0, tk.END)
                self._recording_entry.insert(0, self.start_hotkey)
                self._recording_entry.configure(state="readonly")
            else:
                self._recording_entry.configure(state="normal")
                self._recording_entry.delete(0, tk.END)
                self._recording_entry.insert(0, self.stop_hotkey)
                self._recording_entry.configure(state="readonly")

        # 清理录制状态
        self._cleanup_recording()

    def _finish_hotkey_recording(self, key_name):
        """完成热键录制

        设计说明：
        - 仅更新对应的StringVar变量（输入框显示）
        - 不立即更新内部变量，等待用户点击"应用设置"
        - 清理录制状态
        - 准备下一次录制

        Args:
            key_name: 录制的按键名称
        """
        if hasattr(self, '_recording_entry') and self._recording_entry:
            # 仅更新显示变量，不更新内部热键变量
            if self._recording_action == "开始":
                self.start_hotkey_var.set(key_name)
            else:
                self.stop_hotkey_var.set(key_name)

        # 清理录制状态
        self._cleanup_recording()

    def _cleanup_recording(self):
        """清理录制状态

        设计说明：
        - 解绑全局键盘事件
        - 清理所有录制相关变量
        - 确保状态一致性
        """
        # 解绑键盘事件
        self.root.unbind_all("<Key>")

        # 清理录制变量
        if hasattr(self, '_recording_entry'):
            delattr(self, '_recording_entry')
        if hasattr(self, '_recording_var'):
            delattr(self, '_recording_var')
        if hasattr(self, '_recording_action'):
            delattr(self, '_recording_action')

    def _toggle_debug_mode(self):
        """切换调试模式

        设计说明：
        - 允许用户在运行时开启/关闭调试输出
        - 仅影响当前会话，不保存到配置文件
        """
        if hasattr(self, 'debug_var'):
            Config.DEBUG_MODE = self.debug_var.get()
            if Config.DEBUG_MODE:
                self._debug_print("调试模式已开启", logging.INFO)
            else:
                self._debug_print("调试模式已关闭", logging.INFO)


def main():
    """主函数"""
    root = tk.Tk()
    MainGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
