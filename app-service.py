import os
import time
import base64
import cv2
import numpy as np
from fastapi import FastAPI, Body, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from onnxocr.onnx_paddleocr import ONNXPaddleOcr

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

model = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ocr_api")
async def ocr_api(data: dict = Body(...)):
    try:
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

        start_time = time.time()
        result = model.ocr(img)
        end_time = time.time()
        processing_time = end_time - start_time

        ocr_results = []
        for line in result[0]:
            if isinstance(line[0], (list, np.ndarray)):
                bounding_box = np.array(line[0]).reshape(4, 2).tolist()
            else:
                bounding_box = []
            cleaned_text = " ".join(str(line[1][0]).split())
            ocr_results.append({
                "text": cleaned_text,
                "confidence": float(line[1][1]),
                "bounding_box": bounding_box
            })

        return JSONResponse({
            "processing_time": processing_time,
            "results": ocr_results
        })
    except Exception as e:
        return JSONResponse({"error": f"An error occurred: {str(e)}"}, status_code=500)
