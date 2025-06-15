# 🚀 OnnxOCR-UI

## 📖 OnnxOCR-UI 简介
OnnxOCR-UI 是基于 [OnnxOCR](https://github.com/jingsongliujing/OnnxOCR) 的高级批量图片/PDF OCR 识别工具，采用 Tkinter + customTkinter 打造，专为高效、易用和美观的桌面批量文字识别场景设计。

![OnnxOCR-UI](./docs/images/UI-20250614211544.jpg)

## ✨ 主要功能
- 支持批量图片、PDF 文件拖拽或选择添加
- PDF 转图片采用 pymupdf，无需 poppler
- 识别结果可分别输出 txt 或合并为一个 txt，文件名自动带时间戳
- 输出文件夹自动创建，兼容中文路径
- 自定义高端黑色主题 UI，窗口支持拉伸、最大化、最小化、居中、任务栏图标
- 状态栏实时显示进度与提示
- 文件列表区显示文件名、大小、处理用时
- “清除添加”按钮可一键清空已选文件
- 支持模型选择（PP-OCRv5、PP-OCRv4、ch_ppocr_server_v2.0），可热切换
- 可选是否输出处理图片(_ocr.jpg)
- 进度条实时显示整体进度，PDF按页数动态更新
- 多图识别时状态栏提示平均速度

## 🛠️ 依赖环境
- Python 3.7
- customtkinter
- tkinterdnd2
- Pillow
- opencv-python
- pymupdf

安装依赖：
```
pip install -r requirements.txt
```

## 启动方式

```bash
python main.py
```

## 目录结构
- `onnxocr_ui`   项目目录   
    - `ui.py`        UI 界面与交互逻辑
    - `logic.py`     OCR 识别与文件处理逻辑
    - `requirements.txt`  依赖包列表
    - `app_icon.ico` 界面与任务栏图标
- `main.py`      启动入口，仅负责启动 UI

## 其他说明
- 支持 PyInstaller 打包，图标自动适配
- 详细开发说明见 docs/OnnxOCR 开发说明.md
- 版本更新详见 docs/ChangeLogs.md

## 🙏感谢
- [OnnxOCR](https://github.com/jingsongliujing/OnnxOCR)
