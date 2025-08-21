#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板内容匹配检测器

功能说明：
- 左侧：可动态增删的检测字段输入区，支持纯文本和正则表达式两种模式
- 右侧：实时显示剪贴板内容
- 底部：开始/停止监听剪贴板，支持单条匹配和全部匹配两种模式
- 支持鼠标滚轮滚动左侧区域
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import re


# ============================== 常量配置 ==============================
class Config:
    """程序配置常量"""

    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 800
    LEFT_INPUT_SECTION_HEIGHT = 210
    LEFT_SAVED_SECTION_HEIGHT = 210
    START_STOP_BUTTON_WIDTH = 120
    START_STOP_BUTTON_HEIGHT = 60
    CLIPBOARD_POLL_MS = 500
    MAX_FIELDS = 20
    MIN_FIELDS = 1


class MainGUI:
    """主窗口应用类

    主要功能：
    1. 动态字段管理：支持1-20个检测字段的增删
    2. 剪贴板监听：实时监听剪贴板内容变化
    3. 内容匹配：支持纯文本和正则表达式两种匹配模式
    4. 匹配策略：支持单条匹配和全部匹配两种策略
    """

    def __init__(self, root):
        """初始化主窗口

        Args:
            root: Tkinter根窗口对象
        """
        self.root = root
        self.root.title("剪贴板内容匹配检测器")
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # 初始化数据状态
        self._init_data_states()

        # 创建界面
        self._create_interface()

        # 设置布局权重
        self._setup_layout()

    def _init_data_states(self):
        """初始化数据状态变量"""
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

        # 当前活动的滚动画布（用于鼠标滚轮事件分发）
        self._active_scroll_canvas = None

    def _create_interface(self):
        """创建主界面"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 创建各个面板
        self._create_left_panel(main_frame)
        self._create_right_panel(main_frame)
        self._create_bottom_panel(main_frame)

    def _setup_layout(self):
        """设置布局权重"""
        # 主框架布局权重
        main_frame = self.root.winfo_children()[0]
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)

    # ======================== 左侧面板：字段管理 ========================
    def _create_left_panel(self, main_frame):
        """创建左侧字段管理面板"""
        # 左侧主框架
        self.left_frame = ttk.LabelFrame(
            main_frame, text="检测字段管理", padding="10"
        )
        self.left_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10)
        )

        # 标题
        ttk.Label(self.left_frame, text="检测字段（1-20）").grid(
            row=0, column=0, sticky=tk.W
        )

        # 动态字段输入区域（可滚动）
        fields_section, self.fields_container = self._create_scrollable_area(
            self.left_frame, height=Config.LEFT_INPUT_SECTION_HEIGHT
        )
        fields_section.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.fields_container.columnconfigure(1, weight=1)

        # 字段控制区域
        self._create_field_controls()

        # 匹配模式选择
        self._create_match_mode_selection()

        # 保存按钮
        self.submit_button = ttk.Button(
            self.left_frame, text="保存字段", command=self._handle_save_click
        )
        self.submit_button.grid(row=4, column=0, sticky=tk.W)

        # 分隔线
        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).grid(
            row=5, column=0, sticky=(tk.E, tk.W), pady=(10, 10)
        )

        # 保存字段显示区域
        ttk.Label(self.left_frame, text="当前保存的字段").grid(
            row=6, column=0, sticky=tk.W, pady=(0, 6)
        )

        # 保存字段显示区域（可滚动）
        saved_section, self.saved_container = self._create_scrollable_area(
            self.left_frame, height=Config.LEFT_SAVED_SECTION_HEIGHT
        )
        saved_section.grid(row=7, column=0, sticky=(tk.W, tk.E))
        self.saved_container.columnconfigure(0, weight=1)

        # 初始化至少一个字段
        self._add_field()

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

    def _create_match_mode_selection(self):
        """创建匹配模式选择区域"""
        match_mode_frame = ttk.Frame(self.left_frame)
        match_mode_frame.grid(row=3, column=0, sticky=tk.W, pady=(6, 6))

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
        """创建右侧剪贴板显示面板"""
        right_frame = ttk.LabelFrame(
            main_frame, text="剪贴板内容显示", padding="10"
        )
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 文本显示区域（只读）
        self.display_text = scrolledtext.ScrolledText(
            right_frame, width=50, height=20, wrap=tk.WORD
        )
        self.display_text.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )
        self.display_text.configure(state=tk.DISABLED)

        # 初始化显示内容
        initial = self._get_clipboard_text()
        self._set_display_text(initial)
        self._last_clipboard_text = initial

        # 设置布局权重
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
            bottom_frame, "开始监听", self._start_clipboard_listen, 0
        )

        # 停止监听按钮
        self.stop_btn = self._create_action_button(
            bottom_frame, "停止监听", self._stop_clipboard_listen, 1
        )
        self.stop_btn.configure(state=tk.DISABLED)

        # 匹配结果提示（Text，支持局部高亮）
        self.match_tip_text = tk.Text(
            bottom_frame, width=40, height=4, wrap=tk.WORD
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

        # 重新渲染界面
        self._reflow_fields()
        self._reflow_saved_display()
        self._update_controls()

    def _remove_field(self, index):
        """删除指定索引的检测字段

        Args:
            index: 要删除的字段索引
        """
        if len(self.fields) <= Config.MIN_FIELDS:
            return

        if 0 <= index < len(self.fields):
            # 删除字段数据
            del self.fields[index]

            # 删除对应的保存显示变量
            if 0 <= index < len(self.saved_display_vars):
                del self.saved_display_vars[index]

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
            return

        # 验证是否有保存的字段
        if not self._has_any_saved_value():
            messagebox.showwarning("提示", "请先在左侧保存至少一个非空字段。")
            return

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
            return

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
            self._set_display_text(current)
            self._last_clipboard_text = current

            # 进行匹配检测（命中会在内部停止监听）
            self._process_matches(current)

        # 继续轮询（若在匹配中已停止监听，下一次进入会直接return）
        self._clipboard_after_id = self.root.after(
            Config.CLIPBOARD_POLL_MS, self._poll_clipboard
        )

    def _process_matches(self, clipboard_text):
        """处理剪贴板内容匹配

        Args:
            clipboard_text: 剪贴板文本内容
        """
        # 查找所有匹配项
        matches = self._find_matches(clipboard_text)

        if not matches:
            return

        # 根据匹配策略处理
        match_mode = self.match_mode_var.get()

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
                print("\a\a\a", end="")  # 控制台铃声兜底
            except Exception:
                pass

    # ======================== 工具方法 ========================
    def _get_mode_label(self, mode_value):
        """获取模式的中文标签

        Args:
            mode_value: 模式值（'text' 或 'regex'）

        Returns:
            中文标签
        """
        return "文本" if mode_value == "text" else "正则"

    def _strip_match_suffix(self, text):
        """去除文本中的匹配状态后缀

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        return re.sub(r" \[(匹配|不匹配|无效正则)\]$", "", text)

    def _extract_mode_and_value(self, saved_text):
        """从保存的字段文本中提取模式和值

        Args:
            saved_text: 保存的字段文本

        Returns:
            (模式标签, 值) 元组
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

        Args:
            clipboard_text: 剪贴板文本内容

        Returns:
            匹配结果列表 [(index, mode_label, value), ...]
        """
        matches = []

        for idx, var in enumerate(self.saved_display_vars):
            base = self._strip_match_suffix(var.get())
            mode_label, value = self._extract_mode_and_value(base)

            # 跳过空值
            if not value or value == "（空）":
                continue

            # 根据模式进行匹配
            if mode_label == "文本":
                # 纯文本匹配
                if value in clipboard_text:
                    matches.append((idx, mode_label, value))
            else:
                # 正则表达式匹配
                try:
                    if re.search(
                        value, clipboard_text, re.DOTALL | re.MULTILINE
                    ):
                        matches.append((idx, mode_label, value))
                except re.error:
                    # 无效正则表达式，跳过
                    continue

        return matches

    def _count_non_empty_saved_fields(self):
        """统计非空的保存字段数量

        Returns:
            非空字段数量
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

        Returns:
            True 如果有非空字段，否则 False
        """
        return self._count_non_empty_saved_fields() > 0

    def _get_clipboard_text(self):
        """安全地获取剪贴板文本内容

        Returns:
            剪贴板文本内容，如果获取失败则返回空字符串
        """
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            text = ""
        return text

    def _set_display_text(self, text):
        """在右侧显示区域设置文本内容

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

        Args:
            parent: 父容器
            height: 区域高度

        Returns:
            (容器框架, 内部框架) 元组
        """
        container = ttk.Frame(parent)
        canvas = tk.Canvas(container, height=height, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=canvas.yview
        )
        interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(
            (0, 0), window=interior, anchor="nw"
        )
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

        Args:
            canvas: 画布对象
            interior: 内部框架对象
        """
        for widget in (canvas, interior):
            widget.bind(
                "<Enter>",
                lambda e, c=canvas: self._bind_global_mousewheel(c),
            )
            widget.bind(
                "<Leave>",
                lambda e: self._unbind_global_mousewheel(),
            )

    def _bind_global_mousewheel(self, canvas):
        """绑定全局鼠标滚轮事件

        Args:
            canvas: 要绑定的画布对象
        """
        self._active_scroll_canvas = canvas
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.root.bind_all("<Button-4>", self._on_global_mousewheel)
        self.root.bind_all("<Button-5>", self._on_global_mousewheel)

    def _unbind_global_mousewheel(self):
        """解除全局鼠标滚轮事件绑定"""
        self._active_scroll_canvas = None
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")

    def _on_global_mousewheel(self, event):
        """全局鼠标滚轮事件处理

        Args:
            event: 鼠标滚轮事件对象

        Returns:
            事件处理结果
        """
        canvas = self._active_scroll_canvas
        if canvas is None:
            return "break"

        # 计算滚动步长
        step = 0
        if getattr(event, "num", None) in (4, 5):
            step = -1 if event.num == 4 else 1
        elif hasattr(event, "delta") and event.delta:
            if sys.platform == "darwin":
                step = -1 if event.delta > 0 else 1
            else:
                step = -int(event.delta / 120) if event.delta else 0
                if step == 0:
                    step = -1 if event.delta > 0 else 1

        # 执行滚动
        if step:
            canvas.yview_scroll(step * 3, "units")

        return "break"

    # ======================== 交互方法 ========================
    def _handle_save_click(self):
        """处理保存按钮点击事件"""
        # 保存前校验正则表达式有效性
        for i, field in enumerate(self.fields, start=1):
            value = field["text"].get().strip()
            mode_label = self._get_mode_label(field["mode"].get())

            if mode_label == "正则" and value:
                try:
                    re.compile(value)
                except re.error as e:
                    messagebox.showwarning("提示", f"字段{i} 的正则无效: {e}")
                    return

        # 确保保存显示变量数量正确
        if len(self.saved_display_vars) != len(self.fields):
            self.saved_display_vars = [
                tk.StringVar() for _ in range(len(self.fields))
            ]

        # 保存所有字段
        for idx, field in enumerate(self.fields, start=1):
            value = field["text"].get().strip()
            mode_label = self._get_mode_label(field["mode"].get())
            text = value if value else "（空）"

            self.saved_display_vars[idx - 1].set(
                f"字段{idx}（{mode_label}）: {text}"
            )

        # 重新渲染保存显示区域
        self._reflow_saved_display()

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


def main():
    """主函数"""
    root = tk.Tk()
    MainGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
