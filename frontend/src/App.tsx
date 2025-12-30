import { useState } from 'react';
import type { AnalysisReport } from './types';
import ConfrontationTable from './components/ConfrontationTable';
import './index.css';
import Login from './components/Login';
import { useAuth } from './contexts/AuthContext';

function App() {
  const { user, logout, loading: authLoading } = useAuth();
  const [s1Text, setS1Text] = useState("");
  const [s1Type, setS1Type] = useState("FIR");
  const [s2Text, setS2Text] = useState("");
  const [s2Type, setS2Type] = useState("Section 161");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);

  const handleFileUpload = async (
    e: React.ChangeEvent<HTMLInputElement>,
    setText: (t: string) => void,
    type: string
  ) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("statement_type", type);

      const response = await fetch('/upload-document', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const err = await response.json();
          throw new Error(err.detail || "Upload failed");
        } else {
          const textErr = await response.text();
          throw new Error("Server Error: " + textErr);
        }
      }

      const data = await response.json();
      console.log('upload response', data);
      // Ensure content_preview is a string and set it safely
      const preview = typeof data.content_preview === 'string' ? data.content_preview : String(data.content_preview || '');
      setText(preview);
      // Show short preview alert for immediate feedback
      alert(`Extracted text from ${data.filename}. Preview: ${preview.slice(0,200)}\n\nPlease review and edit if necessary.`);
    } catch (err) {
      console.error(err);
      alert("Failed to upload/extract text: " + (err as Error).message);
    } finally {
      setLoading(false);
      // Reset file input
      e.target.value = '';
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setReport(null);
    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          statement_1_text: s1Text,
          statement_1_type: s1Type,
          statement_2_text: s2Text,
          statement_2_type: s2Type,
        }),
      });

      if (!response.ok) throw new Error("Analysis failed");

      const data = await response.json();
      setReport(data);
    } catch (error) {
      console.error("Fetch error details:", error);
      alert(`Error analyzing statements: ${(error as Error).message}. Check console for details.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-200 selection:bg-blue-500/30">

      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-lg shadow-blue-500/20"></div>
            <h1 className="text-xl font-bold tracking-tight text-white">Sakshya AI <span className="text-xs font-normal text-slate-400 bg-slate-800 px-2 py-0.5 rounded ml-2">MVP</span></h1>
          </div>
          <div className="flex items-center gap-4">
            <nav className="text-sm font-medium text-slate-400 hover:text-white transition-colors cursor-pointer">Docs</nav>
            {authLoading ? (
              <div className="text-sm text-slate-400">Checking auth...</div>
            ) : user ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-300">{user.email}</span>
                <button onClick={() => logout()} className="text-sm text-blue-400 hover:text-blue-300">Sign out</button>
              </div>
            ) : (
              <div className="text-sm text-slate-400">Not signed in</div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-12">
        {/* If user not signed in, show login */}
        {!user && !authLoading && (
          <div className="mb-12">
            <Login />
          </div>
        )}

        {/* Intro */}
        {user && !report && !loading && (
          <div className="mb-12 text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-white mb-4">Witness Statement Analysis</h2>
            <p className="text-slate-400">Upload or paste statements below to identify semantic contradictions, omissions, and legal discrepancies automatically.</p>
          </div>
        )}

        {/* Input Section */}
        {user && !report && !loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div className="space-y-4">
              <div className="flex justify-between items-center bg-slate-800 p-2 rounded">
                <label className="font-semibold text-slate-300">Statement 1</label>
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileUpload(e, setS1Text, s1Type)}
                    className="hidden"
                    id="file-upload-1"
                  />
                  <label htmlFor="file-upload-1" className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-blue-300">
                    📄 Upload PDF/Img
                  </label>
                  <select
                    value={s1Type}
                    onChange={(e) => setS1Type(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="FIR">FIR</option>
                    <option value="Section 161">Section 161</option>
                    <option value="Section 164">Section 164</option>
                    <option value="Court Deposition">Court Deposition</option>
                  </select>
                </div>
              </div>
              <textarea
                className="w-full h-80 bg-slate-900/50 border border-slate-700 rounded-lg p-4 resize-none focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder:text-slate-600"
                placeholder="Paste text here or upload a document..."
                value={s1Text}
                onChange={(e) => setS1Text(e.target.value)}
              />
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center bg-slate-800 p-2 rounded">
                <label className="font-semibold text-slate-300">Statement 2</label>
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileUpload(e, setS2Text, s2Type)}
                    className="hidden"
                    id="file-upload-2"
                  />
                  <label htmlFor="file-upload-2" className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-blue-300">
                    📄 Upload PDF/Img
                  </label>
                  <select
                    value={s2Type}
                    onChange={(e) => setS2Type(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="FIR">FIR</option>
                    <option value="Section 161">Section 161</option>
                    <option value="Section 164">Section 164</option>
                    <option value="Court Deposition">Court Deposition</option>
                  </select>
                </div>
              </div>
              <textarea
                className="w-full h-80 bg-slate-900/50 border border-slate-700 rounded-lg p-4 resize-none focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder:text-slate-600"
                placeholder="Paste text here or upload a document..."
                value={s2Text}
                onChange={(e) => setS2Text(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* Action Button */}
        {!report && !loading && (
          <div className="flex justify-center mb-12">
            <button
              onClick={handleAnalyze}
              disabled={!s1Text || !s2Text}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow-lg shadow-blue-500/25 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Analyze Statements
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 space-y-6">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
            <div className="text-slate-400 animate-pulse">Analyzing semantic discrepancies...</div>
          </div>
        )}

        {/* Report Section */}
        {report && (
          <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-center">
              <div className="flex flex-col">
                <h2 className="text-2xl font-bold text-white">Analysis Report</h2>
                {report.input_language !== 'en' && (
                  <span className="text-xs text-yellow-400 mt-1">
                    Detected Language: {report.input_language.toUpperCase()} — Analysis performed via English translation for legal accuracy.
                  </span>
                )}
              </div>
              <button onClick={() => setReport(null)} className="text-sm text-blue-400 hover:text-blue-300">Start New Analysis</button>
            </div>

            <ConfrontationTable rows={report.rows} />

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg text-sm text-slate-500">
              <p className="font-bold mb-2">LEGAL DISCLAIMER</p>
              <p>{report.disclaimer}</p>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}

export default App
