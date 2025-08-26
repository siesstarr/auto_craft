#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板内容匹配检测器 - 核心功能模块

功能说明：
- 剪贴板监听和内容获取
- 字段匹配逻辑（纯文本和正则表达式）
- 配置管理和持久化
- 热键管理
- 调试系统

设计原则：
- 业务逻辑与UI完全分离
- 单一职责原则：每个类只负责一个功能领域
- 配置与逻辑分离，便于维护
"""

import re
import json
import os
import logging
import sys
import tkinter as tk


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
    MIN_FIELDS = 1  # 最小字段数量

    # 配置文件路径
    CONFIG_FILE = "fields_config.json"  # 字段配置文件
    HOTKEY_CONFIG_FILE = "hotkey_config.json"  # 热键配置文件

    # 热键配置
    DEFAULT_START_HOTKEY = "F8"  # 默认开始监听热键
    DEFAULT_STOP_HOTKEY = "F9"  # 默认停止监听热键

    # 调试配置
    DEBUG_MODE = True  # 开发环境显示调试信息
    DEBUG_LEVEL = logging.DEBUG  # 调试级别

    @classmethod
    def get_config_dir(cls):
        """获取配置目录路径"""
        return os.environ.get("AUTO_CRAFT_CONFIG_DIR", ".")

    @classmethod
    def get_config_file_path(cls, filename):
        """获取配置文件的完整路径"""
        return os.path.join(cls.get_config_dir(), filename)


class DebugSystem:
    """调试系统管理类"""

    @staticmethod
    def setup_debug_system():
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

            logging.info(
                "调试系统已初始化，日志将同时输出到控制台和debug.log文件"
            )
        else:
            # 生产环境：只记录警告和错误
            logging.basicConfig(
                level=logging.WARNING,
                format='%(asctime)s - %(levelname)s - %(message)s',
            )

    @staticmethod
    def debug_print(message, level=logging.INFO):
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


class FieldManager:
    """字段管理类"""

    def __init__(self):
        self.fields = []
        self.saved_display_vars = []

    def add_field(self, text_var, mode_var):
        """添加新的检测字段"""

        # 创建字段数据
        field_data = {"text": text_var, "mode": mode_var}
        self.fields.append(field_data)

        # 创建对应的保存显示变量
        mode_label = self._get_mode_label(mode_var.get())
        self.saved_display_vars.append(
            tk.StringVar(
                value=f"字段{len(self.fields)}（{mode_label}）: （空）"
            )
        )

        DebugSystem.debug_print(
            f"字段添加成功，当前字段数量: {len(self.fields)}",
            logging.INFO,
        )
        return True

    def remove_field(self, index):
        """删除指定索引的检测字段"""
        if len(self.fields) <= Config.MIN_FIELDS:
            DebugSystem.debug_print(
                f"已达到最小字段数量限制: {Config.MIN_FIELDS}",
                logging.WARNING,
            )
            return False

        if 0 <= index < len(self.fields):
            # 删除字段数据
            del self.fields[index]

            # 删除对应的保存显示变量
            if 0 <= index < len(self.saved_display_vars):
                del self.saved_display_vars[index]

            DebugSystem.debug_print(
                f"字段删除成功，当前字段数量: {len(self.fields)}",
                logging.INFO,
            )
            return True
        return False

    def get_field_count(self):
        """获取字段数量"""
        return len(self.fields)

    def can_add_field(self):
        """检查是否可以添加字段"""
        return True  # 移除字段数量上限限制

    def can_remove_field(self):
        """检查是否可以删除字段"""
        return len(self.fields) > Config.MIN_FIELDS

    def _get_mode_label(self, mode_value):
        """获取模式的中文标签"""
        return "文本" if mode_value == "text" else "正则表达式"


class ClipboardManager:
    """剪贴板管理类"""

    def __init__(self, root):
        self.root = root
        self._clipboard_listening = False
        self._clipboard_after_id = None
        self._last_clipboard_text = ""

    def start_listening(self):
        """开始剪贴板监听"""
        if self._clipboard_listening:
            DebugSystem.debug_print("剪贴板监听已在运行中", logging.WARNING)
            return False

        DebugSystem.debug_print("开始剪贴板监听", logging.INFO)

        # 清空剪贴板
        try:
            self.root.clipboard_clear()
        except tk.TclError:
            pass

        # 重置剪贴板状态
        self._last_clipboard_text = ""

        # 开始监听
        self._clipboard_listening = True

        # 开始轮询
        self._poll_clipboard()
        return True

    def stop_listening(self):
        """停止剪贴板监听"""
        if not self._clipboard_listening:
            DebugSystem.debug_print("剪贴板监听未在运行", logging.WARNING)
            return False

        DebugSystem.debug_print("停止剪贴板监听", logging.INFO)

        # 停止监听
        self._clipboard_listening = False

        # 取消定时器
        if self._clipboard_after_id is not None:
            try:
                self.root.after_cancel(self._clipboard_after_id)
            except Exception:
                pass
            self._clipboard_after_id = None
        return True

    def is_listening(self):
        """获取监听状态"""
        return self._clipboard_listening

    def _poll_clipboard(self):
        """轮询剪贴板变化"""
        if not self._clipboard_listening:
            return

        # 获取当前剪贴板内容
        current = self._get_clipboard_text()

        # 检查内容变化
        if current != self._last_clipboard_text:
            DebugSystem.debug_print(
                f"检测到剪贴板内容变化，长度: {len(current)}",
                logging.DEBUG,
            )
            self._last_clipboard_text = current

            # 调用回调
            if hasattr(self, '_on_content_change'):
                self._on_content_change(current)
        else:
            DebugSystem.debug_print("剪贴板内容无变化", logging.DEBUG)

        # 继续轮询
        self._clipboard_after_id = self.root.after(
            Config.CLIPBOARD_POLL_MS, self._poll_clipboard
        )

    def _get_clipboard_text(self):
        """安全获取剪贴板文本内容"""
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            text = ""
        return text

    def set_content_change_callback(self, callback):
        """设置内容变化回调"""
        self._on_content_change = callback


class MatchEngine:
    """匹配引擎类"""

    def __init__(self, field_manager):
        self.field_manager = field_manager

    def find_matches(self, clipboard_text):
        """查找剪贴板内容与保存字段的匹配项目

        Args:
            clipboard_text: 剪贴板文本内容

        Returns:
            list: 匹配结果列表 [(index, mode_label, value), ...]
        """
        DebugSystem.debug_print(
            f"开始匹配项目搜索，剪贴板内容: {clipboard_text[:50]}...",
            logging.DEBUG,
        )

        matches = []

        for idx, var in enumerate(self.field_manager.saved_display_vars):
            # 提取字段信息
            base = self._strip_match_suffix(var.get())
            mode_label, value = self._extract_mode_and_value(base)

            # 跳过空值
            if not value or value == "（空）":
                DebugSystem.debug_print(
                    "字段为空，跳过匹配",
                    logging.DEBUG,
                )
                continue

            DebugSystem.debug_print(
                f"检查字段: {value}",
                logging.DEBUG,
            )

            # 基于模式进行匹配
            if mode_label == "文本":
                # 纯文本匹配
                if value in clipboard_text:
                    DebugSystem.debug_print(
                        f"字段{idx + 1}文本匹配成功: {value}",
                        logging.INFO,
                    )
                    matches.append((idx, mode_label, value))
                else:
                    DebugSystem.debug_print(
                        f"字段{idx + 1}文本匹配失败: {value}",
                        logging.DEBUG,
                    )
            else:
                # 正则表达式匹配
                try:
                    if re.search(
                        value, clipboard_text, re.DOTALL | re.MULTILINE
                    ):
                        DebugSystem.debug_print(
                            f"字段{idx + 1}正则表达式匹配成功: {value}",
                            logging.INFO,
                        )
                        matches.append((idx, mode_label, value))
                    else:
                        DebugSystem.debug_print(
                            f"字段{idx + 1}正则表达式匹配失败: {value}",
                            logging.DEBUG,
                        )
                except re.error as e:
                    # 正则表达式错误时跳过，不影响其他字段匹配
                    DebugSystem.debug_print(
                        f"字段{idx + 1}正则表达式错误: {e}",
                        logging.ERROR,
                    )
                    continue

        DebugSystem.debug_print(
            f"匹配搜索完成，找到{len(matches)}个匹配项目", logging.INFO
        )
        return matches

    def process_matches(self, clipboard_text, match_mode):
        """处理剪贴板内容匹配

        Args:
            clipboard_text: 剪贴板文本内容
            match_mode: 匹配模式 ("single" 或 "all")

        Returns:
            tuple: (is_match, match_text) 匹配结果和文本
        """
        DebugSystem.debug_print(
            f"开始剪贴板内容匹配处理，内容长度: {len(clipboard_text)}",
            logging.INFO,
        )

        # 搜索所有匹配项目
        matches = self.find_matches(clipboard_text)

        if not matches:
            DebugSystem.debug_print("未找到匹配项目", logging.INFO)
            return False, ""

        DebugSystem.debug_print(
            f"{len(matches)}个匹配项目被发现", logging.INFO
        )

        # 基于匹配策略进行处理
        DebugSystem.debug_print(f"匹配策略: {match_mode}", logging.INFO)

        if match_mode == "single":
            # 单一匹配：匹配任意1项即停止
            return self._handle_single_match(matches)
        else:
            # 全匹配：需要匹配所有非空项目
            return self._handle_all_match(matches)

    def _handle_single_match(self, matches):
        """处理单一匹配结果"""
        # 构建匹配提示文本
        match_texts = []
        for idx, mode_label, value in matches:
            match_texts.append(f"字段{idx + 1}（{mode_label}）: {value}")

        rule_text = "匹配:\n" + "\n".join(match_texts)
        return True, rule_text

    def _handle_all_match(self, matches):
        """处理全匹配结果"""
        # 检查是否匹配所有非空项目
        non_empty_count = self._count_non_empty_saved_fields()

        if len(matches) >= non_empty_count:
            # 构建匹配提示文本
            match_texts = []
            for idx, mode_label, value in matches:
                match_texts.append(f"字段{idx + 1}（{mode_label}）: {value}")

            rule_text = "全匹配:\n" + "\n".join(match_texts)
            return True, rule_text

        return False, ""

    def _count_non_empty_saved_fields(self):
        """计算非空保存字段数量"""
        count = 0
        for var in self.field_manager.saved_display_vars:
            text = self._strip_match_suffix(var.get())
            content = text.split(": ", 1)[1] if ": " in text else text
            if content and content != "（空）":
                count += 1
        return count

    def has_any_saved_value(self):
        """检查是否有非空保存字段"""
        return self._count_non_empty_saved_fields() > 0

    def _strip_match_suffix(self, text):
        """从文本中移除匹配状态后缀"""
        return re.sub(r" \[(匹配|不匹配|无效正则)\]$", "", text)

    def _extract_mode_and_value(self, saved_text):
        """从保存的字段文本中提取模式和值"""
        base = self._strip_match_suffix(saved_text)
        mode_label = "文本"
        value = ""

        # 提取模式（中文括弧内）
        left = base.find("（")
        right = base.find("）")
        if left != -1 and right != -1 and right > left:
            mode_label = base[left + 1 : right]  # noqa: E203

        # 提取冒号后的内容
        if ": " in base:
            value = base.split(": ", 1)[1]

        return mode_label, value


class ConfigManager:
    """配置管理类"""

    @staticmethod
    def load_fields_config():
        """加载保存的字段配置"""
        try:
            if os.path.exists(Config.CONFIG_FILE):
                with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'fields' in data:
                    fields_data = data['fields']
                    if isinstance(fields_data, list):
                        return fields_data
        except Exception as e:
            DebugSystem.debug_print(f"字段配置加载失败: {e}", logging.ERROR)
        return []

    @staticmethod
    def save_fields_config(fields_data):
        """将字段配置保存到文件"""
        try:
            # 准备保存数据
            save_data = {"fields": []}

            for field in fields_data:
                save_data["fields"].append(
                    {"text": field["text"].get(), "mode": field["mode"].get()}
                )

            # 写入配置文件
            with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            DebugSystem.debug_print(f"字段配置保存失败: {e}", logging.ERROR)
            return False

    @staticmethod
    def load_hotkey_config():
        """加载热键配置"""
        try:
            config_path = Config.get_config_file_path(
                Config.HOTKEY_CONFIG_FILE
            )
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    result = {}
                    if 'start_hotkey' in data:
                        result['start_hotkey'] = data['start_hotkey']
                    if 'stop_hotkey' in data:
                        result['stop_hotkey'] = data['stop_hotkey']
                    return result
        except Exception as e:
            DebugSystem.debug_print(f"热键配置加载失败: {e}", logging.ERROR)
        return {}

    @staticmethod
    def save_hotkey_config(start_hotkey, stop_hotkey):
        """保存热键配置"""
        try:
            save_data = {
                "start_hotkey": start_hotkey,
                "stop_hotkey": stop_hotkey,
            }

            config_path = Config.get_config_file_path(
                Config.HOTKEY_CONFIG_FILE
            )
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            DebugSystem.debug_print(f"热键配置保存失败: {e}", logging.ERROR)
            return False


class HotkeyManager:
    """热键管理类"""

    def __init__(self, root):
        self.root = root
        self.start_hotkey = Config.DEFAULT_START_HOTKEY
        self.stop_hotkey = Config.DEFAULT_STOP_HOTKEY
        self._hotkey_listening = False
        self._pynput_listener = None

    def load_config(self):
        """加载热键配置"""
        config = ConfigManager.load_hotkey_config()

        if 'start_hotkey' in config:
            self.start_hotkey = config['start_hotkey']
        if 'stop_hotkey' in config:
            self.stop_hotkey = config['stop_hotkey']

        # 检查加载的热键是否有效，无效则设置为默认值
        if not self._is_valid_hotkey(
            self.start_hotkey
        ) or not self._is_valid_hotkey(self.stop_hotkey):
            DebugSystem.debug_print(
                "加载的热键配置无效，使用默认热键",
                logging.WARNING,
            )
            self._set_default_hotkeys()

    def start_listening(self, start_callback, stop_callback):
        """开始热键监听"""
        if self._hotkey_listening:
            return False

        try:
            from pynput import keyboard as pynput_keyboard

            self._hotkey_listening = True

            # 使用pynput库绑定全局热键
            def on_press(key):
                try:
                    if hasattr(key, 'char'):
                        # 普通字符键
                        if key.char == self.start_hotkey:
                            start_callback()
                        elif key.char == self.stop_hotkey:
                            stop_callback()
                    else:
                        # 功能键
                        key_name = str(key).replace('Key.', '')
                        if key_name == self.start_hotkey.lower():
                            start_callback()
                        elif key_name == self.stop_hotkey.lower():
                            stop_callback()
                except Exception as e:
                    DebugSystem.debug_print(
                        f"热键处理错误: {e}", logging.ERROR
                    )

            self._pynput_listener = pynput_keyboard.Listener(on_press=on_press)
            self._pynput_listener.start()

            DebugSystem.debug_print(
                f"全局热键监听开始: {self.start_hotkey}, {self.stop_hotkey}",
                logging.INFO,
            )
            return True

        except ImportError:
            # pynput库不可用时，回退到Tkinter绑定
            DebugSystem.debug_print(
                "pynput库不可用，使用Tkinter绑定（仅窗口有焦点时有效）",
                logging.WARNING,
            )

            self._hotkey_listening = True

            # 绑定全局键盘事件
            self.root.bind_all(
                f"<Key-{self.start_hotkey}>", lambda e: start_callback()
            )
            self.root.bind_all(
                f"<Key-{self.stop_hotkey}>", lambda e: stop_callback()
            )

            # 对F8和F9这样的功能键使用特殊绑定
            if self.start_hotkey == "F8":
                self.root.bind_all("<KeyPress-F8>", lambda e: start_callback())
            if self.stop_hotkey == "F9":
                self.root.bind_all("<KeyPress-F9>", lambda e: stop_callback())
            return True
        except Exception as e:
            DebugSystem.debug_print(f"热键监听开始失败: {e}", logging.ERROR)
            self._hotkey_listening = False
            return False

    def stop_listening(self):
        """停止热键监听"""
        if not self._hotkey_listening:
            return False

        self._hotkey_listening = False

        # 解绑键盘事件
        try:
            # 使用pynput库停止全局热键监听
            if hasattr(self, '_pynput_listener'):
                self._pynput_listener.stop()
                self._pynput_listener = None

            DebugSystem.debug_print(
                f"全局热键监听停止: {self.start_hotkey}, {self.stop_hotkey}",
                logging.INFO,
            )

        except ImportError:
            # pynput库不可用时，使用Tkinter解绑
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
            DebugSystem.debug_print(f"热键监听停止失败: {e}", logging.ERROR)

        return True

    def update_hotkeys(self, start_hotkey, stop_hotkey):
        """更新热键"""
        # 停止当前的热键监听
        self.stop_listening()

        # 更新热键
        self.start_hotkey = start_hotkey
        self.stop_hotkey = stop_hotkey

        # 保存到配置文件
        ConfigManager.save_hotkey_config(start_hotkey, stop_hotkey)

    def _set_default_hotkeys(self):
        """设置默认热键"""
        self.start_hotkey = Config.DEFAULT_START_HOTKEY
        self.stop_hotkey = Config.DEFAULT_STOP_HOTKEY
        DebugSystem.debug_print(
            f"已设置默认热键: 开始={self.start_hotkey}, 停止={self.stop_hotkey}"
        )

        # 保存默认热键到配置文件
        try:
            ConfigManager.save_hotkey_config(
                self.start_hotkey, self.stop_hotkey
            )
            DebugSystem.debug_print("默认热键已保存到配置文件")
        except Exception as e:
            DebugSystem.debug_print(
                f"默认热键配置保存失败: {e}", logging.ERROR
            )

    def _is_valid_hotkey(self, hotkey):
        """检查热键是否有效"""
        if not hotkey or not isinstance(hotkey, str):
            return False

        # 检查是否为有效热键格式
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


class NotificationManager:
    """通知管理类"""

    def __init__(self, root):
        self.root = root

    def notify_match(self, rule_text):
        """匹配命中时的统一通知：前置窗口、提示音、停止监听"""
        # 将前面窗口移到最前面并聚焦
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
                # 其他平台：使用多次系统铃声，形成连续警报效果
                # 连续3次，每次间隔100ms
                self.root.bell()
                self.root.after(120, self.root.bell)
                self.root.after(240, self.root.bell)
                self.root.after(360, self.root.bell)
        except Exception:
            try:
                DebugSystem.debug_print(
                    "\a\a\a", logging.DEBUG
                )  # 控制台铃声兜底
            except Exception:
                pass
