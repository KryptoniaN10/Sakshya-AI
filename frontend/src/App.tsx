import { useRef, useState } from 'react';
import type { AnalysisReport } from './types';
import ConfrontationTable from './components/ConfrontationTable';
import './index.css';
import Login from './components/Login';
import HistoryViewer from './components/HistoryViewer';
import { useAuth } from './contexts/AuthContext';
import { db } from './firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

const API_BASE = import.meta.env.VITE_API_URL || ''; // Fallback to relative path for proxy if not set

function App() {
  const { user, logout, loading: authLoading } = useAuth();
  const [s1Text, setS1Text] = useState("");
  const [s1Type, setS1Type] = useState("FIR");
  const [s2Text, setS2Text] = useState("");
  const [s2Type, setS2Type] = useState("Section 161");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);

  // Audio recording state
  const [recordingTarget, setRecordingTarget] = useState<'s1' | 's2' | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [transcribingTarget, setTranscribingTarget] = useState<'s1' | 's2' | null>(null);

  // UI State
  const [showLogin, setShowLogin] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

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

      const response = await fetch(`${API_BASE}/upload-document`, {
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
      const preview = typeof data.content_preview === 'string' ? data.content_preview : String(data.content_preview || '');
      setText(preview);
      alert(`Extracted text from ${data.filename}. Preview: ${preview.slice(0, 200)}\n\nPlease review and edit if necessary.`);
    } catch (err) {
      console.error(err);
      alert("Failed to upload/extract text: " + (err as Error).message);
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  const callSpeechToText = async (
    audioBlob: Blob,
    setText: (t: string) => void,
    statementType: string
  ) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    formData.append('statement_type', statementType);

    try {
      const response = await fetch(`${API_BASE}/speech-to-text`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const maybeJson = await response.text();
        throw new Error(`STT failed: ${maybeJson}`);
      }

      const data = await response.json();
      const text = typeof data.text === 'string' ? data.text : String(data.text || '');
      setText(prev => (prev ? prev + '\n' + text : text));
    } catch (err) {
      console.error('Speech-to-text error', err);
      alert('Failed to transcribe audio: ' + (err as Error).message);
    }
  };

  const handleAudioUpload = async (
    e: React.ChangeEvent<HTMLInputElement>,
    setText: (t: string) => void,
    statementType: string,
    target: 's1' | 's2',
  ) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    setTranscribingTarget(target);
    try {
      await callSpeechToText(file, setText, statementType);
    } finally {
      setTranscribingTarget(null);
      e.target.value = '';
    }
  };

  const startRecording = async (target: 's1' | 's2') => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Audio recording is not supported in this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const targetSetter = target === 's1' ? setS1Text : setS2Text;

        setTranscribingTarget(target);
        try {
          await callSpeechToText(audioBlob, targetSetter, target === 's1' ? s1Type : s2Type);
        } finally {
          setTranscribingTarget(null);
        }
        setRecordingTarget(null);
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setRecordingTarget(target);
    } catch (err) {
      console.error('Error starting recording', err);
      alert('Could not access microphone: ' + (err as Error).message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  const saveHistory = async (reportData: AnalysisReport) => {
    if (!user) return;

    try {
      // Calculate summary stats
      const summary = {
        critical: reportData.rows.filter(r => r.severity === 'Critical').length,
        material: reportData.rows.filter(r => r.severity === 'Material').length,
        minor: reportData.rows.filter(r => r.severity === 'Minor').length,
        omission: reportData.rows.filter(r => r.classification === 'omission').length
      };

      // Extract unique actors from the rows (parsing "Type: Actor Action")
      const actorsSet = new Set<string>();
      reportData.rows.forEach(row => {
        // Try to extract actor name if it follows the pattern "EventType: Actor Action..."
        // We look for the first word or two after the colon
        // This is a heuristic.
        const match = row.source_1.match(/:\s*([^ ]+)/);
        if (match && match[1]) actorsSet.add(match[1]);
      });
      const actors = Array.from(actorsSet).slice(0, 3);

      await addDoc(collection(db, 'analysis_history'), {
        userId: user.uid,
        caseId: `CASE-${Date.now()}`, // Simple ID generation
        title: `Analysis: ${s1Type} vs ${s2Type}`,
        previewText: s1Text.slice(0, 150) + (s1Text.length > 150 ? "..." : ""),
        actors: actors,
        createdAt: serverTimestamp(),
        detectedLanguage: reportData.input_language,
        summary
      });
      console.log("Analysis history saved.");
    } catch (err) {
      console.error("Failed to save history:", err);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setReport(null);
    try {
      const response = await fetch(`${API_BASE}/analyze`, {
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
      console.log("DEBUG: Received Analysis Report:", data);
      setReport(data);

      // Save history if logged in
      if (user) {
        saveHistory(data);
      }

    } catch (error) {
      console.error("Fetch error details:", error);
      alert(`Error analyzing statements: ${(error as Error).message}. Check console for details.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-200 selection:bg-blue-500/30 relative">

      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.jpeg" alt="Sakshya AI Logo" className="h-8 w-8 rounded-lg object-cover" />
            <h1 className="text-xl font-bold tracking-tight text-white">Sakshya AI <span className="text-xs font-normal text-slate-400 bg-slate-800 px-2 py-0.5 rounded ml-2">MVP</span></h1>
          </div>
          <div className="flex items-center gap-4">
            <nav className="text-sm font-medium text-slate-400 hover:text-white transition-colors cursor-pointer">Docs</nav>
            {authLoading ? (
              <div className="text-sm text-slate-400">Loading...</div>
            ) : user ? (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowHistory(true)}
                  className="text-sm text-slate-300 hover:text-white bg-slate-800/50 px-3 py-1 rounded border border-slate-700/50 hover:border-slate-600 transition-all"
                >
                  My Analyses
                </button>
                <div className="h-4 w-px bg-slate-700"></div>
                <button onClick={() => logout()} className="text-sm text-blue-400 hover:text-blue-300">Sign out</button>
              </div>
            ) : (
              <button
                onClick={() => setShowLogin(true)}
                className="text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 px-4 py-1.5 rounded transition-colors"
              >
                Log In
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Login Modal */}
      {showLogin && !user && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-lg w-full max-w-md shadow-2xl relative">
            <button
              onClick={() => setShowLogin(false)}
              className="absolute top-4 right-4 text-slate-500 hover:text-white z-10"
            >
              ✕
            </button>
            <Login onGuest={() => setShowLogin(false)} />
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistory && user && (
        <HistoryViewer onClose={() => setShowHistory(false)} onLoadReport={() => { }} />
      )}

      <main className="mx-auto max-w-7xl px-6 py-12">

        {/* Intro */}
        {!report && !loading && (
          <div className="mb-12 text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-white mb-4">Witness Statement Analysis</h2>
            <p className="text-slate-400 mb-6">Upload or paste statements below to identify semantic contradictions, omissions, and legal discrepancies automatically.</p>
            {!user && (
              <div className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-3 text-sm text-blue-300 inline-block">
                💡 <span className="font-semibold">Guest Mode:</span> You can use all features freely. <button onClick={() => setShowLogin(true)} className="underline hover:text-white">Log in</button> to save your history.
              </div>
            )}
          </div>
        )}

        {/* Input Section - ALWAYS VISIBLE (Guest Mode Support) */}
        {!report && !loading && (
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
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={(e) => handleAudioUpload(e, setS1Text, s1Type, 's1')}
                    className="hidden"
                    id="audio-upload-1"
                  />
                  <label
                    htmlFor="audio-upload-1"
                    className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-blue-300"
                  >
                    🎵 Upload Audio
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      recordingTarget === 's1' ? stopRecording() : startRecording('s1')
                    }
                    className={`text-xs px-2 py-1 rounded border ${
                      recordingTarget === 's1'
                        ? 'bg-red-600 border-red-500 text-white'
                        : 'bg-slate-700 border-slate-600 text-amber-300'
                    }`}
                  >
                    {recordingTarget === 's1' ? '⏹ Stop' : '🎙 Record'}
                  </button>
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
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={(e) => handleAudioUpload(e, setS2Text, s2Type, 's2')}
                    className="hidden"
                    id="audio-upload-2"
                  />
                  <label
                    htmlFor="audio-upload-2"
                    className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-blue-300"
                  >
                    🎵 Upload Audio
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      recordingTarget === 's2' ? stopRecording() : startRecording('s2')
                    }
                    className={`text-xs px-2 py-1 rounded border ${
                      recordingTarget === 's2'
                        ? 'bg-red-600 border-red-500 text-white'
                        : 'bg-slate-700 border-slate-600 text-amber-300'
                    }`}
                  >
                    {recordingTarget === 's2' ? '⏹ Stop' : '🎙 Record'}
                  </button>
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
                {!user && (
                  <span className="text-xs text-slate-500 mt-1">
                    Log in to save this analysis to your history.
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

        {report && (
          <div className="mt-12 p-4 border-t border-slate-800 text-slate-500 text-xs">
            <details>
              <summary className="cursor-pointer hover:text-slate-300">Debug JSON View (Click to expand)</summary>
              <pre className="mt-4 p-4 bg-slate-900 rounded overflow-auto h-64">
                {JSON.stringify(report, null, 2)}
              </pre>
            </details>
          </div>
        )}

      </main>
      {transcribingTarget && (
        <div className="fixed inset-0 z-40 pointer-events-none flex items-end justify-center">
          <div className="mb-10 flex items-center gap-3 rounded-full border border-blue-500/40 bg-slate-900/70 px-4 py-2 shadow-lg shadow-blue-950/40 backdrop-blur">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
            <span className="text-sm text-slate-100">
              Transcribing audio for {transcribingTarget === 's1' ? 'Statement 1' : 'Statement 2'}...
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
