# Sakshya AI - Legal Decision Support Tool

**Sakshya AI** ("Evidence AI") is an AI-powered legal decision-support tool designed to assist Indian judges, advocates, and legal professionals in automating the analysis of witness statement consistency under **Section 145 of the Bharatiya Sakshya Adhiniyam**.

The system identifies **semantic contradictions** and **material omissions** between witness statements at different procedural stages (e.g., FIR, Section 161 statement, Court Deposition), with support for **Indian languages** and intelligent legal heuristics to minimize false positives.

## ✨ Key Features

- **🌍 Multilingual Legal Analysis**: Supports **Malayalam, Hindi, Tamil, Telugu, Kannada, Bengali**, and English
  - Analysis is performed **in the same language as input** (no forced translation)
  - Discrepancies and explanations are returned in the original language
  
- **📊 Smart Event Extraction**: AI-powered extraction of factual events (actors, actions, targets, times, locations) from witness statements
  
- **🔍 Semantic Consistency Checking**: Compares extracted events to identify:
  - **Contradictions**: Direct conflicts between statements
  - **Omissions**: Missing facts in later statements
  - **Minor Discrepancies**: Time/location variations
  - **Consistent Statements**: Aligned facts
  
- **⚖️ Legal Logic Safeguards**:
  - Actor Consistency Rules
  - Action Compatibility Checks
  - Presence vs. Participation distinction
  - FIR omission handling
  
- **📄 Document Processing**:
  - **PDF Support**: Typed PDFs via `pdfplumber`
  - **Image OCR**: Handwritten documents via remote PaddleOCR API
  - Automatic text extraction and preprocessing
  
- **🔐 Flexible Authentication**:
  - **Guest Mode**: Use all analysis features without logging in (Privacy-focused)
  - **Advocate Login**: Sign up/Log in to save and manage case history
  - **My Analyses**: Dashboard to view past analyses with summaries, actors, and severity scores

- **🎨 Judge-Friendly UI**:
  - Clean React-based dashboard
  - **Authentication flows** (Guest/User)
  - Real-time analysis feedback
  - Severity badges (Critical/Minor)
  - Legal footnotes and explanations

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Frontend** | React 19.2, TypeScript, Vite, TailwindCSS |
| **Auth & DB** | Firebase Authentication, Cloud Firestore |
| **AI Engine** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| **Language Detection** | langdetect |
| **OCR** | Remote PaddleOCR API, pdfplumber, OpenCV |

## 📋 Prerequisites

Before setting up, ensure you have:

- **Python 3.10+** installed
- **Node.js & npm** (v16+)
- **Google Gemini API Key** (free tier available at [ai.google.dev](https://ai.google.dev))
- **Firebase Project Config** (for Auth & History features)
- **Git**

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sakshya-ai.git
cd "Sakshya AI"
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `backend/.env` file by copying the template:

```bash
cp .env.example .env
```

Then edit `backend/.env` with your actual API keys:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash
PADDLE_OCR_URL=https://your-paddle-ocr-endpoint.com  # Optional
```

#### Run Backend Server
```bash
python -m uvicorn main:app --reload --port 8005
```

Backend will be available at **http://127.0.0.1:8005**

### 3. Frontend Setup

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at **http://localhost:5174** (or next available port if 5174 is in use)

### 4. Access the Application

Open your browser and navigate to **http://localhost:5174**

## 📖 Usage

### Via Web Interface

1. **Upload or Paste Statements**: 
   - Select statement type (FIR, Section 161, Court Deposition, etc.)
   - Upload a PDF/image or paste text directly

2. **Analyze**: 
   - Upload the second statement
   - Click "Analyze"
   - System automatically detects language and processes

3. **Review Results**:
   - View identified discrepancies
   - Check severity (Critical/Minor)
   - Read legal explanations
   - Results are displayed in the **same language as input**

### Via API (Manual Testing)

```bash
curl -X POST http://127.0.0.1:8005/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "statement_1_type": "FIR",
    "statement_1_text": "The accused assaulted the victim with a knife at the market.",
    "statement_2_type": "Court Deposition",
    "statement_2_text": "The accused was standing nearby at the market."
  }'
```

## 🇮🇳 Language Support

### Supported Languages
- ✅ English (en)
- ✅ Hindi (hi)
- ✅ Malayalam (ml)
- ✅ Tamil (ta)
- ✅ Telugu (te)
- ✅ Kannada (kn)
- ✅ Bengali (bn)

### How It Works
1. **Automatic Detection**: System detects input language using `langdetect`
2. **Same-Language Processing**: Analysis is performed in the original language (not translated)
3. **Same-Language Output**: Results (classifications, explanations) are returned in the input language

## 🔧 Configuration

### `.env` File Template

See `.env.example` for the template. Copy it and fill in your credentials:

```bash
cp backend/.env.example backend/.env
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key" or "Create API Key"
3. Create a new API key (free tier available)
4. Copy the key and paste into `backend/.env` as `GEMINI_API_KEY`

### Firebase Configuration (Frontend)

To enable Authentication and History, you need a Firebase project:

1.  Go to [Firebase Console](https://console.firebase.google.com/) and create a project.
2.  Enable **Authentication** (Email/Password).
3.  Enable **Cloud Firestore** (Create Database).
4.  Go to Project Settings -> General -> "Your apps" -> Add Web App.
5.  Copy the config values and add them to `frontend/.env`:

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

**Note**: Free tier has rate limits. For production, upgrade to a paid tier.

## 📁 Project Structure

```
Sakshya AI/
├── backend/
│   ├── main.py              # FastAPI application & routes
│   ├── config.py            # Configuration & environment loading
│   ├── extraction.py        # Event extraction via LLM
│   ├── compare.py           # Event comparison logic
│   ├── prompts.py           # LLM prompts (same-language output)
│   ├── translation.py       # Language detection & translation
│   ├── heuristics.py        # Legal logic rules
│   ├── filters.py           # Pre-comparison filtering
│   ├── report.py            # Report generation
│   ├── schemas.py           # Data models (Pydantic)
│   ├── ingestion.py         # Text cleaning
│   ├── ocr.py               # Document processing & OCR
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example         # Example environment file (COPY THIS)
│   └── .env                 # Your local secrets (DO NOT COMMIT)
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx         # React entry point
│   │   ├── App.tsx          # Main component
│   │   ├── types.ts         # TypeScript types
│   │   ├── components/      # React components
│   │   │   └── ConfrontationTable.tsx
│   │   ├── assets/
│   │   ├── App.css
│   │   └── index.css
│   ├── vite.config.ts       # Vite config with API proxy
│   ├── tsconfig.json
│   ├── package.json
│   └── README.md
│
├── .gitignore               # Git ignore patterns
├── .env.example             # Example environment file
├── README.md                # This file
└── MALAYALAM_FIX_SUMMARY.md # Details on language support updates
```

## 🧪 Testing

### Test with Sample Data (via Frontend)

1. Start both backend and frontend servers (see Setup above)
2. Navigate to http://localhost:5174
3. Paste sample text or upload a PDF
4. Click "Analyze"

### Run Malayalam Analysis Test (CLI)

```bash
cd "Sakshya AI"
python test_malayalam.py
```

This will send a test request with Malayalam text and display the analysis result.

## 🐛 Troubleshooting

### Backend Port Already in Use (Port 8005)
```bash
# Windows
netstat -ano | findstr :8005
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8005 | xargs kill -9
```

### API Quota Exceeded (429 Error)
- Free tier Gemini API has rate limits
- **Solution**: Upgrade to a paid API plan or get a new API key
- Check usage at [Google AI Studio](https://aistudio.google.com/app/usage)

### No Events Extracted
- Ensure statement text is long enough (>50 characters)
- Check backend logs for LLM errors
- Verify `GEMINI_API_KEY` is valid and has available quota

### OCR Not Working
- For remote OCR: Ensure `PADDLE_OCR_URL` is configured in `.env`
- For local Tesseract: Install via `choco install tesseract` (Windows) or `brew install tesseract` (macOS)
- Set `TESSERACT_CMD` path in `.env` if in non-standard location

### Language Not Detected
- Try longer text samples (at least 30+ characters)
- Ensure text is primarily in one language
- Check [langdetect](https://github.com/Mimino666/langdetect) documentation for supported languages

## 📡 API Endpoints

### Health Check
```
GET /
```
Returns: `{"status": "ok", "message": "Sakshya AI Backend Running"}`

### Upload Document
```
POST /upload-document
Content-Type: multipart/form-data

Parameters:
- file: PDF or Image file
- statement_type: "FIR" | "Section 161" | "Court Deposition" | etc.

Response: {"filename": "...", "message": "...", "content_preview": "extracted text"}
```

### Analyze Statements
```
POST /analyze
Content-Type: application/json

Body:
{
  "statement_1_type": "FIR",
  "statement_1_text": "Malayalam or any supported language text here",
  "statement_2_type": "Court Deposition",
  "statement_2_text": "Another statement in the same language"
}

Response: {
  "input_language": "ml",
  "analysis_language": "ml",
  "rows": [
    {
      "event_1_actor": "...",
      "event_1_action": "...",
      "event_2_actor": "...",
      "event_2_action": "...",
      "classification": "contradiction",
      "explanation": "Malayalam explanation here",
      "severity": "Critical",
      "legal_basis": "..."
    }
  ],
  "disclaimer": "..."
}
```

## 🚀 Deployment

### Backend (Production - Linux/macOS)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8005 "main:app"
```

### Backend (Production - Docker)
```bash
docker build -t sakshya-ai-backend -f Dockerfile .
docker run -p 8005:8005 --env-file .env sakshya-ai-backend
```

### Frontend (Production)
```bash
npm run build
# Output is in frontend/dist/
# Deploy to Vercel, Netlify, or any static host
```

## 📜 License

This project is provided for educational and legal research purposes. Consult with legal experts before using in actual court proceedings.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Disclaimer

**Sakshya AI is an AI-assisted tool for preliminary analysis only.** It does **NOT**:
- Constitute legal advice
- Replace human judgment
- Guarantee accuracy of analysis
- Assess truthfulness of statements

Lawyers and judges must independently verify all findings against original case records and apply their legal expertise before making any decisions.

## 📧 Support & Feedback

For issues, feature requests, or feedback:
- Open an issue on GitHub
- Contact: [devadathanappu69@gmail.com]

## 🔄 Recent Updates (v1.1)

- ✅ **Authentication System**: Guest Mode, Sign Up, and Login functionality
- ✅ **Analysis History**: Firestore integration to save and review past analyses
- ✅ **Rich History Details**: View actors, preview text, and severity summaries in history
- ✅ **Branding**: Updated logo and application title
- ✅ **Malayalam & all Indian language support** with same-language output
- ✅ Improved extraction and comparison prompts with language preservation
- ✅ Enhanced error handling and JSON response parsing
- ✅ Updated to Google Gemini 2.5 Flash model
- ✅ Better `.env` configuration handling with `.env.example` template
- ✅ Comprehensive `.gitignore` for Python/Node.js projects

---

**Made with ❤️ for Indian legal system modernization**
