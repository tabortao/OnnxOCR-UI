# logic.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from onnxocr.onnx_paddleocr import ONNXPaddleOcr, sav2Img
import cv2
from typing import List, Callable
from pathlib import Path
import time
import numpy as np

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

try:
    import fitz  # pymupdf
    def pdf_to_images(pdf_path, dpi=200):
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape((pix.height, pix.width, pix.n))
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            images.append(img)
        return images
except ImportError:
    pdf_to_images = None

class OCRLogic:
    def __init__(self, status_callback: Callable[[str], None]):
        self.status_callback = status_callback
        self.model = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)

    def run(self, files: List[str], save_txt: bool, merge_txt: bool, output_img: bool = False, file_time_callback=None, pdf_progress_callback=None):
        start_time = time.time()
        all_text = []
        for idx, file in enumerate(files):
            ext = os.path.splitext(file)[1].lower()
            self.status_callback(f"正在处理: {os.path.basename(file)} ({idx+1}/{len(files)})")
            t0 = time.time()
            if ext == ".pdf":
                if pdf_to_images is None:
                    raise RuntimeError("未安装pymupdf库，无法处理PDF文件。请先安装pymupdf。")
                images = pdf_to_images(file, dpi=300)
                pdf_text = self._ocr_images(images, file, save_txt, merge_txt, output_img=output_img, is_pdf=True, pdf_progress_callback=pdf_progress_callback)
                if save_txt and not merge_txt:
                    all_text.append(pdf_text)
            else:
                # 兼容中文路径图片读取
                try:
                    if file.lower().endswith('.bmp'):
                        img = cv2.imdecode(np.fromfile(file, dtype=np.uint8), cv2.IMREAD_COLOR)
                    else:
                        with open(file, 'rb') as fimg:
                            img_array = np.frombuffer(fimg.read(), np.uint8)
                        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                except Exception as e:
                    self.status_callback(f"图片读取失败: {file}，错误: {e}")
                    if file_time_callback:
                        file_time_callback(idx, 0)
                    continue
                if img is None:
                    self.status_callback(f"文件无法读取或不是有效图片: {file}")
                    if file_time_callback:
                        file_time_callback(idx, 0)
                    continue
                text = self._ocr_image(img, file, save_txt, output_img=output_img)
                if save_txt and not merge_txt:
                    all_text.append(text)
            t1 = time.time()
            if file_time_callback:
                file_time_callback(idx, t1-t0)
            # 新增：提示单张图片识别用时
            self.status_callback(f"{os.path.basename(file)} 识别用时: {t1-t0:.2f} 秒")
            # 新增：多图时提示平均速度
            if len(files) > 1:
                avg = (t1 - start_time) / (idx + 1)
                self.status_callback(f"已完成 {idx+1}/{len(files)}，平均单张用时: {avg:.2f} 秒")
        if save_txt and merge_txt and len(files) > 1:
            out_dir = self._get_output_dir(files[0])
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            out_txt = os.path.join(out_dir, f"merged_ocr_{timestamp}.txt")
            # 修正：合并所有文本内容（包括pdf和图片）
            with open(out_txt, "w", encoding="utf-8") as f:
                for idx, file in enumerate(files):
                    ext = os.path.splitext(file)[1].lower()
                    txt_path = os.path.join(out_dir, f"{Path(file).stem}_ocr_*.txt")
                    import glob
                    txt_files = glob.glob(txt_path)
                    if txt_files:
                        with open(txt_files[0], "r", encoding="utf-8") as tf:
                            f.write(tf.read())
                            f.write("\n\n")
        elapsed = time.time() - start_time
        if files:
            out_dir = self._get_output_dir(files[0])
            self.status_callback(f"识别完成，总耗时：{elapsed:.2f}秒，文件保存在：{out_dir}")
        else:
            self.status_callback(f"识别完成，总耗时：{elapsed:.2f}秒")

    def _ocr_images(self, images, pdf_path, save_txt, merge_txt, output_img=False, is_pdf=False, pdf_progress_callback=None):
        out_dir = self._get_output_dir(pdf_path)
        pdf_text = []
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        total = len(images)
        for i, img in enumerate(images):
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            result = self.model.ocr(img_cv)
            if output_img:
                out_img_path = os.path.join(out_dir, f"{Path(pdf_path).stem}_page{i+1}_ocr.jpg")
                sav2Img(img_cv, result, name=out_img_path)
            page_text = self._result_to_text(result)
            pdf_text.append(page_text)
            # 新增：每处理一页回调进度
            if pdf_progress_callback:
                pdf_progress_callback(i + 1, total)
        if save_txt:
            txt_path = os.path.join(out_dir, f"{Path(pdf_path).stem}_ocr_{timestamp}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(pdf_text))
        return "\n\n".join(pdf_text)

    def _ocr_image(self, img, img_path, save_txt, output_img=False):
        out_dir = self._get_output_dir(img_path)
        result = self.model.ocr(img)
        if output_img:
            out_img_path = os.path.join(out_dir, f"{Path(img_path).stem}_ocr.jpg")
            sav2Img(img, result, name=out_img_path)
        text = self._result_to_text(result)
        if save_txt:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            txt_path = os.path.join(out_dir, f"{Path(img_path).stem}_ocr_{timestamp}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        return text

    def _result_to_text(self, result):
        # 健壮性检查，防止result为空或结构异常
        if not result or not isinstance(result, list) or not result[0] or not isinstance(result[0], list):
            return "[未检测到内容]"
        lines = []
        for box in result[0]:
            # 兼容只检测无识别内容的情况
            if isinstance(box, list) and len(box) == 2 and isinstance(box[1], (list, tuple)) and len(box[1]) >= 1:
                lines.append(str(box[1][0]))
            elif isinstance(box, list) and (isinstance(box[0], (list, tuple)) or isinstance(box[0], float)):
                # 只有检测框，无识别内容
                lines.append("[未识别] " + str(box))
            else:
                lines.append(str(box))
        return "\n".join(lines)

    def _get_output_dir(self, file_path):
        base_dir = os.path.dirname(file_path)
        out_dir = os.path.join(base_dir, "Image_Output_OCR")
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def set_model(self, model_name):
        import os
        base_model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "onnxocr", "models"))
        model_map = {
            "PP-OCRv5": "ppocrv5",
            "PP-OCRv4": "ppocrv4",
            "ch_ppocr_server_v2.0": "ch_ppocr_server_v2.0"
        }
        model_dir = model_map.get(model_name, "ppocrv5")
        model_path = os.path.join(base_model_dir, model_dir)
        det_model_dir = os.path.join(model_path, "det", "det.onnx")
        cls_model_dir = os.path.join(model_path, "cls", "cls.onnx")
        # 所有模型统一使用ppocrv5/ppocrv5_dict.txt
        rec_char_dict_path = os.path.join(base_model_dir, "ppocrv5", "ppocrv5_dict.txt")
        rec_model_dir = os.path.join(model_path, "rec", "rec.onnx") if os.path.exists(os.path.join(model_path, "rec", "rec.onnx")) else None
        ocr_kwargs = dict(
            use_angle_cls=True,
            use_gpu=False,
            det_model_dir=det_model_dir,
            cls_model_dir=cls_model_dir,
            rec_char_dict_path=rec_char_dict_path
        )
        if rec_model_dir and os.path.exists(rec_model_dir):
            ocr_kwargs["rec_model_dir"] = rec_model_dir
        self.model = ONNXPaddleOcr(**ocr_kwargs)
