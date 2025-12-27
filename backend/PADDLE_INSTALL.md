PaddleOCR and Poppler installation notes
======================================

This project uses PaddleOCR for OCR. PaddleOCR requires the PaddlePaddle runtime
(`paddlepaddle`) to be installed separately and depends on your OS and Python
version. Follow the steps below for a typical Windows CPU installation.

1) Update pip and install PaddlePaddle (CPU)

```powershell
python -m pip install --upgrade pip
# Visit https://www.paddlepaddle.org.cn/install/quick for the latest wheel URL
pip install paddlepaddle -f https://www.paddlepaddle.org.cn/whl/windows.html
```

2) Install PaddleOCR and other Python deps

```powershell
pip install -r requirements.txt
pip install paddleocr
```

3) Install Poppler (required by `pdf2image` / PDF -> image conversion)

Using Chocolatey (recommended on Windows):

```powershell
choco install poppler
```

If you cannot use Chocolatey, download a Windows build of Poppler and add its
`bin` folder to your `PATH`.

Notes
-----
- If `pip install paddlepaddle` fails, check your Python version and visit the
  official PaddlePaddle installation page for platform-specific wheel commands.
- After installation, you can test PaddleOCR in a Python REPL:

```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=False, lang='en')
print('PaddleOCR ready')
```

- Once `paddleocr` and `paddlepaddle` are installed, restart the backend server.
