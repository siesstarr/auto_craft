# 剪贴板内容匹配检测器

一个基于Python Tkinter的GUI应用程序，用于实时监听剪贴板内容并根据预设规则进行匹配检测。

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
│   ├── __init__ / _init_data_states / _create_interface / _setup_layout
├── 左侧：检测字段管理
│   ├── _create_left_panel / _add_field / _remove_field
│   ├── _reflow_fields / _reflow_saved_display
│   ├── _handle_save_click / _clear_saved
│   └── _import_fields / _export_fields / _load_saved_config / _save_config_to_file
├── 右侧：剪贴板显示
│   └── _create_right_panel / _set_display_text / _get_clipboard_text
├── 底部：执行控制
│   ├── _create_bottom_panel / _create_action_button
│   ├── _start_clipboard_listen / _stop_clipboard_listen
│   ├── _clear_match_tip / _set_match_tip
│   └── _play_sharp_alert / _notify_match
├── 监听与匹配
│   ├── _poll_clipboard / _process_matches
│   ├── _find_matches（文本/正则）
│   ├── _handle_single_match（列出全部匹配项）
│   └── _handle_all_match（需匹配全部非空项）
└── 工具与滚动支持
    ├── _get_mode_label / _strip_match_suffix / _extract_mode_and_value
    └── _create_scrollable_area / _enable_mousewheel / _on_global_mousewheel
```

## 配置文件格式

### 字段配置文件（JSON）
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

## 许可证与贡献

- 许可证：MIT
- 欢迎提交 Issue / PR 改进项目
