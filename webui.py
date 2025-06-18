import os
import shutil
import time
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from onnxocr_ui.logic import OCRLogic
import zipfile
import cv2
import base64
import numpy as np
from fastapi import Body
from onnxocr.onnx_paddleocr import ONNXPaddleOcr

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
RESULT_ROOT = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_ROOT, exist_ok=True)
os.makedirs(RESULT_ROOT, exist_ok=True)

# 模型选项
MODEL_OPTIONS = ["PP-OCRv5", "PP-OCRv4", "ch_ppocr_server_v2.0"]

# OCR 逻辑实例（全局，支持热切换）
ocr_logic = OCRLogic(lambda msg: print(msg))

# 独立 OCR 模型实例，避免影响 ocr_logic
ocr_model_api = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("webui.html", {"request": request, "model_options": MODEL_OPTIONS})

# 友好404页面
@app.exception_handler(404)
async def not_found(request, exc):
    # 只要不是静态资源，全部重定向到首页
    if not request.url.path.startswith("/static") and not request.url.path.startswith("/download"):
        return RedirectResponse("/")
    return JSONResponse({"detail": "NotFound"}, status_code=404)

@app.post("/set_model")
async def set_model(model_name: str = Form(...)):
    try:
        ocr_logic.set_model(model_name)
        return {"success": True, "msg": f"模型已切换为 {model_name}"}
    except Exception as e:
        return {"success": False, "msg": str(e)}

@app.post("/ocr")
async def ocr_files(
    files: List[UploadFile] = File(...),
    model_name: str = Form(...),
):
    # 切换模型
    try:
        ocr_logic.set_model(model_name)
    except Exception as e:
        return JSONResponse({"success": False, "msg": f"模型切换失败: {e}"}, status_code=500)

    # 新建时间戳文件夹
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(RESULT_ROOT, timestamp)
    os.makedirs(session_dir, exist_ok=True)

    # 保存上传文件
    file_paths = []
    for file in files:
        file_path = os.path.join(session_dir, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_paths.append(file_path)

    # 识别
    results = []
    def status_callback(msg): pass  # 可扩展为 WebSocket 推送
    logic = OCRLogic(status_callback)
    logic.set_model(model_name)
    logic.run(file_paths, save_txt=True, merge_txt=False, output_img=False)

    # 收集 txt 结果
    txt_files = []
    for file_path in file_paths:
        out_dir = os.path.join(os.path.dirname(file_path), "Output_OCR")
        for fname in os.listdir(out_dir):
            if fname.endswith(".txt") and fname.startswith(os.path.splitext(os.path.basename(file_path))[0]):
                txt_files.append(os.path.join(out_dir, fname))
                with open(os.path.join(out_dir, fname), "r", encoding="utf-8") as f:
                    content = f.read()
                results.append({"filename": fname, "content": content})

    # 打包 zip
    zip_path = os.path.join(session_dir, f"ocr_txt_{timestamp}.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for txt_file in txt_files:
            zipf.write(txt_file, os.path.basename(txt_file))

    return {
        "success": True,
        "results": results,
        "zip_url": f"/download/{timestamp}"
    }

@app.get("/download/{timestamp}")
async def download_zip(timestamp: str):
    session_dir = os.path.join(RESULT_ROOT, timestamp)
    zip_path = os.path.join(session_dir, f"ocr_txt_{timestamp}.zip")
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename=f"ocr_txt_{timestamp}.zip", media_type="application/zip")
    return JSONResponse({"success": False, "msg": "文件不存在"}, status_code=404)

@app.post("/ocr_api")
async def ocr_api(data: dict = Body(...)):
    """
    接收 base64 图像 JSON，返回单图 OCR 结果，兼容 app-service.py
    {
        "image": "base64字符串"
    }
    """
    if not data or "image" not in data:
        return JSONResponse({"error": "Invalid request, 'image' field is required."}, status_code=400)
    image_base64 = data["image"]
    try:
        image_bytes = base64.b64decode(image_base64)
        image_np = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        if img is None:
            return JSONResponse({"error": "Failed to decode image from base64."}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Image decoding failed: {str(e)}"}, status_code=400)
    import time
    start_time = time.time()
    result = ocr_model_api.ocr(img)
    end_time = time.time()
    processing_time = end_time - start_time
    ocr_results = []
    for line in result[0]:
        if isinstance(line[0], (list, np.ndarray)):
            bounding_box = np.array(line[0]).reshape(4, 2).tolist()
        else:
            bounding_box = []
        ocr_results.append({
            "text": line[1][0],
            "confidence": float(line[1][1]),
            "bounding_box": bounding_box
        })
    return JSONResponse({
        "processing_time": processing_time,
        "results": ocr_results
    })

# 你需要在 templates/webui.html 和 static/ 目录下放置前端页面和 JS，支持多文件上传、模型切换、识别、结果展示和下载。
# 启动命令：uvicorn webui:app --reload
