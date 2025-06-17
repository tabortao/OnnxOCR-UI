import os
import time
import zipfile
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from onnxocr_ui.logic import OCRLogic

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
RESULT_ROOT = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_ROOT, exist_ok=True)
os.makedirs(RESULT_ROOT, exist_ok=True)

MODEL_OPTIONS = ["PP-OCRv5", "PP-OCRv4", "ch_ppocr_server_v2.0"]

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

ocr_logic = OCRLogic(lambda msg: print(msg))

@app.route("/")
def index():
    return render_template("webui.html", model_options=MODEL_OPTIONS)

@app.errorhandler(404)
def not_found(e):
    path = request.path
    if not path.startswith("/static") and not path.startswith("/download"):
        return redirect(url_for("index"))
    return jsonify({"detail": "NotFound"}), 404

@app.route("/set_model", methods=["POST"])
def set_model():
    model_name = request.form.get("model_name")
    try:
        ocr_logic.set_model(model_name)
        return {"success": True, "msg": f"模型已切换为 {model_name}"}
    except Exception as e:
        return {"success": False, "msg": str(e)}

@app.route("/ocr", methods=["POST"])
def ocr_files():
    files = request.files.getlist("files")
    model_name = request.form.get("model_name")
    if not files or not model_name:
        return jsonify({"success": False, "msg": "缺少文件或模型参数"}), 400
    try:
        ocr_logic.set_model(model_name)
    except Exception as e:
        return jsonify({"success": False, "msg": f"模型切换失败: {e}"}), 500
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(RESULT_ROOT, timestamp)
    os.makedirs(session_dir, exist_ok=True)
    file_paths = []
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(session_dir, filename)
        file.save(file_path)
        file_paths.append(file_path)
    results = []
    def status_callback(msg): pass
    logic = OCRLogic(status_callback)
    logic.set_model(model_name)
    logic.run(file_paths, save_txt=True, merge_txt=False, output_img=False)
    txt_files = []
    for file_path in file_paths:
        out_dir = os.path.join(os.path.dirname(file_path), "Output_OCR")
        if not os.path.exists(out_dir):
            continue
        for fname in os.listdir(out_dir):
            if fname.endswith(".txt") and fname.startswith(os.path.splitext(os.path.basename(file_path))[0]):
                txt_files.append(os.path.join(out_dir, fname))
                with open(os.path.join(out_dir, fname), "r", encoding="utf-8") as f:
                    content = f.read()
                results.append({"filename": fname, "content": content})
    zip_path = os.path.join(session_dir, f"ocr_txt_{timestamp}.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for txt_file in txt_files:
            zipf.write(txt_file, os.path.basename(txt_file))
    return jsonify({
        "success": True,
        "results": results,
        "zip_url": f"/download/{timestamp}"
    })

@app.route("/download/<timestamp>")
def download_zip(timestamp):
    session_dir = os.path.join(RESULT_ROOT, timestamp)
    zip_path = os.path.join(session_dir, f"ocr_txt_{timestamp}.zip")
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True, download_name=f"ocr_txt_{timestamp}.zip")
    return jsonify({"success": False, "msg": "文件不存在"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)
