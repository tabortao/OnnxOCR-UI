

20250619:
添加一个批处理OCR页面。
1、新增webui.py、webui.html、ocr_images_pdfs.py3个文件，使用Flask实现简单批量OCR处理一个或多个图片或PDF文件。
2、建议使用Python 3.8以上版本，处理速度提升很多，使用cp312时，发现需要对onnxruntime-gpu取消版本限制、numpy<2.0.0做出版本限制。
3、支持多线程OCR图片。