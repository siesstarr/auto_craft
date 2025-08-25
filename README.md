# 剪贴板内容匹配检测器

一个基于Python Tkinter的GUI应用程序，用于实时监听剪贴板内容并根据预设规则进行匹配检测。

## 设计原则

### 🎯 代码设计理念
- **简洁性**：避免过度设计，保持代码简单易懂
- **单一职责**：每个方法只做一件事，便于维护和测试
- **配置分离**：配置与业务逻辑分离，便于维护
- **错误友好**：优雅的错误处理，不影响用户体验

### 🏗️ 架构特点
- **模块化设计**：界面创建、业务逻辑、配置管理分离
- **统一配置**：所有配置项集中管理，避免魔法数字
- **简化实现**：使用Tkinter原生组件，避免复杂自定义实现

## 功能特性

### 🎯 核心功能
- **动态字段管理**：支持多个检测字段的动态增删
- **双模式匹配**：支持纯文本和正则表达式两种匹配模式
- **智能策略**：支持匹配单条/匹配全部两种策略
- **实时监听**：自动监听剪贴板内容变化，匹配命中后自动停止
- **匹配结果展示**：
  - 底部提示区域以多行形式展示匹配规则
  - 每行规则中冒号后的 value 文本以红色高亮显示
- **执行反馈**：匹配命中时前置窗口并发出尖锐警报声
- **滚动支持**：左侧两个区域支持鼠标滚轮滚动（macOS/Windows/Linux）

### 🔧 交互细节
- **开始监听**：
  - 清空底部提示区域
  - 清空右侧剪贴板显示为"（等待剪贴板内容...）"
  - 清空系统剪贴板内容（若系统允许）
- **命中后行为**：
  - 将窗口前置（短暂置顶）与聚焦
  - 播放尖锐的警报声（Windows使用多次Beep，其他平台多次bell）
  - 停止剪贴板监听

### 📁 导入导出功能
- **导入字段**：支持从JSON文件导入字段配置，自动验证文件格式和正则表达式有效性
- **导出字段**：可将当前检测字段配置导出到JSON文件，支持自定义文件名
- **自动保存**：程序自动保存用户字段配置到`fields_config.json`文件
- **启动恢复**：程序启动时自动加载上次保存的字段配置，数据持久化不丢失

### ⌨️ 热键控制功能
- **默认热键**：F8开始监听，F9停止监听
- **按钮显示**：开始/停止按钮上直接显示对应的热键
- **直观设置**：在按钮下方直接显示热键设置区域，无需额外对话框
- **实时修改**：可直接在输入框中修改热键，点击"应用设置"立即生效
- **全局响应**：热键在程序运行时全局有效，即使程序不在前台也能响应
- **配置持久化**：热键设置自动保存到`hotkey_config.json`文件
- **自动修正**：检测到无效配置时自动修正并保存，确保程序稳定运行

## 运行与使用

### 🚀 启动程序
```bash
python man.py
```

### 📝 操作流程
1. 在左侧新增/编辑检测字段，选择模式（纯文本/正则表达式）
2. 点击"保存字段"保存设置
3. 选择匹配策略（匹配单条/匹配全部）
4. 点击"开始监听"，复制文本到剪贴板进行检测
5. 命中规则将前置窗口、播放警报声，同时在底部提示区域显示匹配详情（value红色高亮）

### ⌨️ 热键操作
- **使用默认热键**：
  - 按F8键开始监听剪贴板
  - 按F9键停止监听剪贴板
- **修改热键设置**：
  - 点击热键输入框进入录制模式
  - 按下想要设置的按键（仅更新显示）
  - 点击"应用设置"按钮验证、保存并生效热键
- **热键状态**：开始/停止按钮上直接显示当前热键
- **调试模式**：开发环境显示调试开关，可实时控制调试输出

### 📥📤 导入导出操作
- **导入字段**：
  1. 点击"导入字段"按钮
  2. 选择要导入的JSON配置文件
  3. 程序自动验证并导入字段配置
- **导出字段**：
  1. 设置好检测字段后点击"导出字段"按钮
  2. 选择保存位置和文件名
  3. 导出成功后显示提示信息

## 架构说明

```
MainGUI类
├── 初始化与布局
│   ├── __init__ / _setup_window / _init_data_states / _create_interface / _setup_layout
├── 左侧：检测字段管理
│   ├── _create_left_panel / _create_fields_title / _create_fields_input_section
│   ├── _create_field_controls / _create_match_mode_selection / _create_save_button
│   ├── _create_separator / _create_saved_fields_section
│   ├── _add_field / _remove_field / _reflow_fields / _reflow_saved_display
│   ├── _handle_save_click / _clear_saved
│   └── _import_fields / _export_fields / _load_saved_config / _save_config_to_file
├── 右侧：剪贴板显示
│   └── _create_right_panel / _set_display_text / _get_clipboard_text
├── 底部：执行控制
│   ├── _create_bottom_panel / _create_action_button
│   ├── _start_clipboard_listen / _stop_clipboard_listen
│   ├── _clear_match_tip / _set_match_tip
│   ├── _play_sharp_alert / _notify_match
│   └── _start_hotkey_recording / _on_key_pressed / _cancel_hotkey_recording
├── 监听与匹配
│   ├── _poll_clipboard / _process_matches
│   ├── _find_matches（文本/正则）
│   ├── _handle_single_match（列出全部匹配项）
│   └── _handle_all_match（需匹配全部非空项）
├── 热键控制
│   ├── _start_hotkey_listening / _stop_hotkey_listening
│   ├── _update_button_hotkey_display / _load_hotkey_config
│   ├── _save_hotkey_config / _start_hotkey_on_init
│   ├── _apply_hotkey_settings / _is_valid_hotkey
│   └── _set_default_hotkeys（自动修正功能）
└── 工具与滚动支持
    ├── _get_mode_label / _strip_match_suffix / _extract_mode_and_value
    ├── _count_non_empty_saved_fields / _has_any_saved_value
    └── _create_scrollable_area / _enable_mousewheel
```

## 🔍 调试系统

### 智能调试输出
- **开发环境**：显示详细调试信息，包括日志文件和控制台输出
- **打包环境**：自动隐藏调试信息，只保留警告和错误日志
- **运行时控制**：开发环境提供调试开关，可实时开启/关闭调试输出

### 调试信息类型
- **INFO**：一般信息（如热键设置、配置加载）
- **WARNING**：警告信息（如配置验证失败）
- **ERROR**：错误信息（如文件操作失败）
- **DEBUG**：详细调试信息（如警报声播放）

### 日志文件
- 开发环境：`debug.log`（UTF-8编码）
- 生产环境：仅控制台输出

## 配置文件格式

### 字段配置文件（fields_config.json）
```json
{
  "fields": [
    {
      "text": "字段内容",
      "mode": "text"
    },
    {
      "text": "\\d+",
      "mode": "regex"
    }
  ]
}
```

### 热键配置文件（hotkey_config.json）
```json
{
  "start_hotkey": "F8",
  "stop_hotkey": "F9"
}
```

### 字段说明
- `text`: 字段的文本内容或正则表达式
- `mode`: 字段模式，支持"text"（纯文本）和"regex"（正则表达式）

## Windows 打包为 .exe

> 需要在 Windows 环境下执行（PyInstaller 不能在 macOS 直接产出 .exe）

```powershell
python -m venv venv
venv\Scripts\activate
pip install -U pip pyinstaller
pyinstaller --onefile --windowed --name ClipboardMatcher ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.ttk ^
  --hidden-import=tkinter.scrolledtext ^
  man.py
```
- 产物位于 `dist/ClipboardMatcher.exe`
- 自定义图标：`--icon=app.ico`
- 打包资源：`--add-data "assets\\config.json;assets"`
- 需要控制台输出时移除 `--windowed`

## 测试

### 🧪 运行测试
```bash
python -m pytest test_man.py -v
```

### 📊 测试覆盖
- 字段增删、保存、重编号、计数与按钮状态
- 剪贴板监听启动/停止流程
- 文本/正则匹配逻辑（有效/无效正则）
- 滚动区域创建与事件绑定
- 底部提示区域渲染（Text高亮）
- 热键控制功能测试
- 热键配置自动修正功能测试

## 常见问题

- **无提示音**：
  - Windows 使用 winsound.Beep；请确认系统已开启系统声音
  - macOS/Linux 使用 bell；个别桌面环境可能默认静音
- **剪贴板无变化不触发**：
  - 监听采用轮询模式；已修复变化但未匹配时也持续轮询
  - 可在开始监听前手动复制任意文本以确保后续变化被检测
- **权限问题**：
  - 某些系统需要允许应用访问剪贴板/辅助功能
- **正则表达式匹配问题**：
  - 确保正确设置了正则表达式字段并点击"保存字段"
  - 确保启动了剪贴板监听
  - 程序已添加调试输出，可在控制台查看详细匹配过程
- **热键无响应**：
  - 检查程序是否正在运行
  - 确认热键设置是否正确
  - 检查系统权限设置
- **热键配置问题**：
  - 程序会自动检测并修正无效的热键配置
  - 修正后的配置会自动保存，下次启动正常

## 许可证与贡献

- 许可证：MIT
- 欢迎提交 Issue / PR 改进项目
