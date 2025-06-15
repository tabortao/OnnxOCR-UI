# ui.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from onnxocr_ui.logic import OCRLogic
import threading
from tkinterdnd2 import DND_FILES, TkinterDnD
import os

class OCRApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = TkinterDnD.Tk()
        self.root.overrideredirect(True)  # 去除原生标题栏
        self.root.geometry("800x600") # # 修改窗口大小
        self.logic = OCRLogic(self.update_status)
        self.logic.ui_ref = self  # 让logic.py可以回调UI方法
        self.selected_files = []
        self._drag_data = {'x': 0, 'y': 0}
        # 支持窗口拖动
        self.resizing = False
        self.root.bind('<ButtonPress-1>', self._start_move)
        self.root.bind('<B1-Motion>', self._on_move)
        # 支持窗口拉伸（四边+右下角）
        self._resize_dir = None
        self.root.bind('<Motion>', self._resize_cursor)
        self.root.bind('<ButtonPress-1>', self._start_resize)
        self.root.bind('<B1-Motion>', self._on_resize)
        self.root.bind('<ButtonRelease-1>', self._stop_resize)
        self._build_ui()

    def _build_ui(self):
        # 自定义标题栏
        self.title_bar = ctk.CTkFrame(self.root, height=36, fg_color="#181c20", corner_radius=0)
        self.title_bar.pack(fill="x", side="top")
        self.title_icon = ctk.CTkLabel(self.title_bar, text="", image=None)
        self.title_icon.pack(side="left", padx=8)
        self.title_text = ctk.CTkLabel(self.title_bar, text=" OnnxOCR-UI 高级OCR识别工具", font=("微软雅黑", 14, "bold"), text_color="#f8f8fa")
        self.title_text.pack(side="left", padx=2)
        self.title_bar.bind('<Button-1>', self._start_move)
        self.title_bar.bind('<B1-Motion>', self._on_move)
        self.title_text.bind('<Button-1>', self._start_move)
        self.title_text.bind('<B1-Motion>', self._on_move)
        # 最小化、最大化、关闭按钮（关闭按钮最右侧）
        self.btn_close = ctk.CTkButton(self.title_bar, text="✕", width=32, height=28, fg_color="#23272b", hover_color="#31363b", command=self.root.destroy, corner_radius=6, text_color="#fff")
        self.btn_close.pack(side="right", padx=2, pady=2)
        self.btn_max = ctk.CTkButton(self.title_bar, text="□", width=32, height=28, fg_color="#23272b", hover_color="#31363b", command=self._maximize, corner_radius=6, text_color="#f8f8fa")
        self.btn_max.pack(side="right", padx=2, pady=2)
        self.btn_min = ctk.CTkButton(self.title_bar, text="—", width=32, height=28, fg_color="#23272b", hover_color="#31363b", command=self._minimize, corner_radius=6, text_color="#f8f8fa")
        self.btn_min.pack(side="right", padx=(0,2), pady=2)

        # 左上角显示UI图标（使用CTkImage避免警告）
        try:
            from PIL import Image
            from customtkinter import CTkImage
            icon_path = os.path.abspath("onnxocr_ui/app_icon.ico")
            icon_img = Image.open(icon_path).resize((24, 24), Image.LANCZOS)
            self.tk_icon = CTkImage(light_image=icon_img, dark_image=icon_img, size=(24, 24))
            self.title_icon.configure(image=self.tk_icon)
        except Exception:
            pass

        # 设置窗口logo（确保任务栏图标始终显示）
        try:
            import ctypes
            import sys
            if hasattr(sys, 'frozen'):
                icon_path = os.path.join(sys._MEIPASS, "onnxocr_ui/app_icon.ico")
            else:
                icon_path = "onnxocr_ui/app_icon.ico"
            self.root.iconbitmap(icon_path)
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('OnnxOCR')
        except Exception:
            pass
        self.root.update_idletasks()

        # 启动时窗口居中
        self.root.update_idletasks()
        w, h = 800, 600 # 修改窗口大小
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # 主体深色背景
        self.root.configure(bg="#23272b")

        # 标题
        self.title_label = ctk.CTkLabel(self.root, text="OnnxOCR-UI 批量图片/PDF识别", font=("微软雅黑", 24, "bold"), text_color="#f8f8fa", bg_color="#23272b")
        self.title_label.pack(pady=20)

        # 文件选择
        self.file_frame = ctk.CTkFrame(self.root, fg_color="#23272b", corner_radius=8)
        self.file_frame.pack(pady=10, fill="x", padx=40)
        self.select_btn = ctk.CTkButton(self.file_frame, text="选择图片或PDF", command=self.select_files, fg_color="#1976d2", hover_color="#1565c0", text_color="#fff")
        self.select_btn.pack(side="left", padx=10)
        self.file_label = ctk.CTkLabel(self.file_frame, text="未选择文件", anchor="w", text_color="#f8f8fa", bg_color="#23272b")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        # 清除已添加文件按钮
        self.clear_btn = ctk.CTkButton(self.file_frame, text="清除添加", command=self.clear_files, fg_color="#31363b", hover_color="#23272b", text_color="#fff", width=80)
        self.clear_btn.pack(side="right", padx=10)
        # 拖拽提示
        self.drag_tip_label = ctk.CTkLabel(self.file_frame, text="可直接拖入图片或PDF文件到此窗口", font=("微软雅黑", 13), text_color="#b0b0b0", bg_color="#23272b")
        self.drag_tip_label.pack(side="right", padx=10)
        # 拖拽支持
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_files)

        # 文件列表显示区
        self.file_list_frame = ctk.CTkFrame(self.root, fg_color="#23272b", corner_radius=8)
        self.file_list_frame.pack(padx=40, fill="both", expand=False)
        self.file_listbox = ctk.CTkTextbox(self.file_list_frame, height=180, font=("微软雅黑", 13), fg_color="#181c20", text_color="#f8f8fa", wrap="none")
        self.file_listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self.file_listbox.configure(state="disabled")

        # 识别按钮（选项上方）
        self.ocr_btn = ctk.CTkButton(self.root, text="开始识别", command=self.start_ocr, fg_color="#1976d2", hover_color="#1565c0", font=("微软雅黑", 20, "bold"), text_color="#fff")
        self.ocr_btn.pack(pady=(20, 20))

        # 选项（识别按钮上方）
        self.options_frame = ctk.CTkFrame(self.root, fg_color="#23272b", corner_radius=8)
        self.options_frame.pack(pady=(0, 20), fill="x", padx=40)
        # 模型选择区域放到合并选项左侧
        self.model_label = ctk.CTkLabel(self.options_frame, text="模型选择：", font=("微软雅黑", 14), text_color="#b0b0b0", bg_color="#23272b")
        self.model_label.pack(side="left", padx=(10, 2))
        self.model_var = tk.StringVar(value="PP-OCRv5")
        self.model_select = ctk.CTkComboBox(self.options_frame, values=["PP-OCRv5", "PP-OCRv4", "ch_ppocr_server_v2.0"], variable=self.model_var, width=180, font=("微软雅黑", 13), fg_color="#23272b", text_color="#f8f8fa")
        self.model_select.pack(side="left", padx=2)
        self.model_select.set("PP-OCRv5")
        self.merge_txt_var = tk.BooleanVar(value=True)
        self.merge_txt_cb = ctk.CTkCheckBox(self.options_frame, text="多文件合并为一个txt", variable=self.merge_txt_var, text_color="#f8f8fa", bg_color="#23272b")
        self.merge_txt_cb.pack(side="left", padx=10)
        self.output_img_var = tk.BooleanVar(value=False)
        self.output_img_cb = ctk.CTkCheckBox(self.options_frame, text="输出处理图片", variable=self.output_img_var, text_color="#f8f8fa", bg_color="#23272b")
        self.output_img_cb.pack(side="left", padx=10)
        # 启用GPU选项，放到输出处理图片右侧
        self.gpu_var = tk.BooleanVar(value=False)
        self.gpu_cb = ctk.CTkCheckBox(self.options_frame, text="启用GPU", variable=self.gpu_var, text_color="#f8f8fa", bg_color="#23272b")
        self.gpu_cb.pack(side="left", padx=10)

        # 进度条（选项栏下方）
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self.root, variable=self.progress_var, width=600, height=16, fg_color="#23272b", progress_color="#1976d2", border_color="#31363b", border_width=2)
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0)

        # 状态栏（始终最底部，单独用pack(side='bottom')，不要被其他控件挤上去）
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_bar = ctk.CTkLabel(self.root, textvariable=self.status_var, anchor="w", font=("微软雅黑", 12), text_color="#b0b0b0", fg_color="#181c20", bg_color="#181c20")
        self.status_bar.pack(side="bottom", fill="x", padx=0, pady=0)

    def update_file_listbox(self):
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")
        for f in self.selected_files:
            try:
                size = os.path.getsize(f)
                size_mb = size / 1024 / 1024
                self.file_listbox.insert("end", f"{os.path.basename(f)}    {size_mb:.2f} MB\n")
            except Exception:
                self.file_listbox.insert("end", f"{os.path.basename(f)}    (无法获取大小)\n")
        self.file_listbox.configure(state="disabled")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片或PDF文件",
            filetypes=[("图片和PDF", ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.pdf")), ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.file_label.configure(text=f"已选择 {len(files)} 个文件")
            self.update_file_listbox()
        else:
            self.selected_files = []
            self.file_label.configure(text="未选择文件")
            self.update_file_listbox()

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        valid_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.pdf'))]
        if valid_files:
            self.selected_files = list(valid_files)
            self.file_label.configure(text=f"已拖入 {len(valid_files)} 个文件")
            self.update_file_listbox()
        else:
            self.selected_files = []
            self.file_label.configure(text="未选择文件")
            self.update_file_listbox()

    def start_ocr(self):
        if not self.selected_files:
            messagebox.showwarning("未选择文件", "请先选择图片或PDF文件！")
            return
        self.ocr_btn.configure(state="disabled")
        self.status_var.set("正在识别中，请稍候...")
        self.progress_var.set(0)  # 进度条重置为0
        model_name = self.model_var.get()
        output_img = self.output_img_var.get()
        use_gpu = self.gpu_var.get()  # 新增
        threading.Thread(target=self._run_ocr, args=(model_name, output_img, use_gpu), daemon=True).start()

    def _run_ocr(self, model_name, output_img, use_gpu):
        def file_time_callback(idx, seconds):
            self.update_file_process_time(idx, seconds)
        def pdf_progress_callback(done, total):
            if self.selected_files:
                pdf_idx = self.selected_files.index(self.current_pdf) if hasattr(self, 'current_pdf') else 0
                total_files = len(self.selected_files)
                base = pdf_idx / total_files
                step = 1 / total_files
                self.progress_var.set(base + step * (done / total))
        try:
            self.logic.set_model(model_name, use_gpu=use_gpu)  # 修正：传递use_gpu参数
            def run_with_pdf_progress(*args, **kwargs):
                return self.logic.run(*args, pdf_progress_callback=pdf_progress_callback, **kwargs)
            for f in self.selected_files:
                if f.lower().endswith('.pdf'):
                    self.current_pdf = f
            self.logic.run(
                self.selected_files,
                save_txt=True,
                merge_txt=self.merge_txt_var.get(),
                output_img=output_img,
                file_time_callback=file_time_callback,
                pdf_progress_callback=pdf_progress_callback
            )
            self.progress_var.set(1.0)
        except Exception as e:
            messagebox.showerror("识别出错", str(e))
        finally:
            self.ocr_btn.configure(state="normal")

    def update_status(self, msg):
        self.status_var.set(msg)

    def _start_move(self, event):
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def _on_move(self, event):
        x = event.x_root - self._drag_data['x']
        y = event.y_root - self._drag_data['y']
        self.root.geometry(f'+{x}+{y}')

    def _minimize(self):
        self.root.update_idletasks()
        self.root.overrideredirect(False)
        self.root.iconify()
        def restore_override():
            if self.root.state() == 'iconic':
                self.root.after(100, restore_override)
            else:
                self.root.overrideredirect(True)
        self.root.after(100, restore_override)

    def _maximize(self):
        # 最大化到屏幕工作区（不覆盖任务栏），再次点击恢复原窗口大小
        import ctypes
        if not hasattr(self, '_normal_geometry') or self.root.geometry() != getattr(self, '_max_geometry', None):
            # 记录原始大小和位置
            self._normal_geometry = self.root.geometry()
            # 获取工作区（不含任务栏）
            class RECT(ctypes.Structure):
                _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long), ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
            rect = RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            work_w = rect.right - rect.left
            work_h = rect.bottom - rect.top
            self._max_geometry = f"{work_w}x{work_h}+{rect.left}+{rect.top}"
            self.root.geometry(self._max_geometry)
            self.progress_bar.configure(width=work_w - 80) 
        else:
            self.root.geometry(self._normal_geometry)
            self.progress_bar.configure(width=600)

    def _set_cursor_default(self, event=None):
        self.root.config(cursor="arrow")

    def _resize_cursor(self, event):
        x, y = event.x, event.y
        w, h = self.root.winfo_width(), self.root.winfo_height()
        border = 8
        if x < border:
            self.root.config(cursor="size_we")
            self._resize_dir = 'left'
        elif w - border < x < w:
            self.root.config(cursor="size_we")
            self._resize_dir = 'right'
        elif h - border < y < h:
            if w - border < x < w:
                self.root.config(cursor="size_nw_se")
                self._resize_dir = 'corner'
            else:
                self.root.config(cursor="size_ns")
                self._resize_dir = 'bottom'
        else:
            self.root.config(cursor="arrow")
            self._resize_dir = None

    def _start_resize(self, event):
        if self._resize_dir:
            self.resizing = True
            self._resize_start = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height(), self._resize_dir)
        else:
            self._start_move(event)

    def _on_resize(self, event):
        if not getattr(self, 'resizing', False):
            return
        x0, y0, win_x, win_y, w0, h0, direction = self._resize_start
        dx = event.x_root - x0
        dy = event.y_root - y0
        min_w, min_h = 400, 300
        if direction == 'right':
            new_w = max(min_w, w0 + dx)
            self.root.geometry(f"{new_w}x{h0}")
        elif direction == 'left':
            new_w = max(min_w, w0 - dx)
            new_x = win_x + dx
            self.root.geometry(f"{new_w}x{h0}+{new_x}+{win_y}")
        elif direction == 'bottom':
            new_h = max(min_h, h0 + dy)
            self.root.geometry(f"{w0}x{new_h}")
        elif direction == 'corner':
            # 右下角等比例缩放
            scale = max(dx / w0, dy / h0)
            new_w = max(min_w, int(w0 + w0 * scale))
            new_h = max(min_h, int(h0 + h0 * scale))
            self.root.geometry(f"{new_w}x{new_h}")

    def _stop_resize(self, event):
        self.resizing = False
        self._resize_dir = None

    def update_file_process_time(self, file_idx, seconds):
        # 在文件列表区追加处理时间
        self.file_listbox.configure(state="normal")
        lines = self.file_listbox.get("1.0", "end").splitlines()
        if 0 <= file_idx < len(lines):
            if "处理用时" in lines[file_idx]:
                # 已有处理用时则替换
                lines[file_idx] = lines[file_idx].split("  处理用时")[0]
            lines[file_idx] += f"  处理用时: {seconds:.2f} 秒"
        self.file_listbox.delete("1.0", "end")
        self.file_listbox.insert("1.0", "\n".join(lines)+"\n")
        self.file_listbox.configure(state="disabled")
        # 更新进度条
        if self.selected_files:
            self.progress_var.set((file_idx + 1) / len(self.selected_files))

    def clear_files(self):
        self.selected_files = []
        self.file_label.configure(text="未选择文件")
        self.update_file_listbox()

    def update_gpu_status(self, msg):
        # 在文件列表区追加一行警告信息
        self.file_listbox.configure(state="normal")
        content = self.file_listbox.get("1.0", "end").rstrip("\n")
        if content:
            content += "\n"
        content += f"[警告] {msg}"
        self.file_listbox.delete("1.0", "end")
        self.file_listbox.insert("1.0", content+"\n")
        self.file_listbox.configure(state="disabled")

    def run(self):
        self.root.mainloop()
