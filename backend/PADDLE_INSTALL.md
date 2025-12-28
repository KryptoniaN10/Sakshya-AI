PaddleOCR and Poppler installation notes
======================================

Remote-first OCR (default)
---------------------------

This project uses a remote PaddleOCR API by default. Configure the remote
endpoint in `backend/.env` using the `PADDLE_OCR_URL` environment variable:

```env
PADDLE_OCR_URL=https://your-remote-paddle-endpoint.example/
```

With the remote endpoint set, the backend will send images (multipart `file`)
to that URL and expect a JSON response containing the recognized `text` and
optionally a numeric `confidence` or `avg_conf` field.

Local PaddleOCR (optional)
--------------------------

If you prefer to run PaddleOCR locally instead of using the remote API, follow
the steps below to install `paddlepaddle` and `paddleocr`. Local Paddle is
optional — the remote API is the default and recommended for easiest setup.

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
