import React, { useEffect, useState } from 'react';
import { db } from '../firebase';
import { collection, query, where, orderBy, getDocs } from 'firebase/firestore';
import { useAuth } from '../contexts/AuthContext';
import type { AnalysisHistoryItem } from '../types';

interface Props {
    onClose: () => void;
    onLoadReport: (reportId: string) => void; // Placeholder if we want to load full report later
}

const HistoryViewer: React.FC<Props> = ({ onClose }) => {
    const { user } = useAuth();
    const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) return;

        const fetchHistory = async () => {
            try {
                const q = query(
                    collection(db, 'analysis_history'),
                    where('userId', '==', user.uid),
                    orderBy('createdAt', 'desc')
                );

                const snapshot = await getDocs(q);
                const data = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data()
                })) as AnalysisHistoryItem[];

                setHistory(data);
            } catch (err) {
                console.error("Error fetching history:", err);
                // Fallback for missing index or other errors
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, [user]);

    return (
        <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl">
                <div className="flex justify-between items-center p-6 border-b border-slate-800">
                    <h2 className="text-xl font-bold text-white">My Analyses</h2>
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                        ✕ Close
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="text-center text-slate-500 py-10">Loading history...</div>
                    ) : history.length === 0 ? (
                        <div className="text-center text-slate-500 py-10">
                            <p>No saved analyses found.</p>
                            <p className="text-sm mt-2">Analyses you run while logged in will appear here.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {history.map(item => (
                                <div key={item.id} className="bg-slate-800/50 border border-slate-700 p-4 rounded-lg hover:bg-slate-800 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="font-semibold text-slate-200 truncate pr-2">{item.title}</h3>
                                        <span className="text-xs text-slate-500 whitespace-nowrap">
                                            {item.createdAt?.seconds ? new Date(item.createdAt.seconds * 1000).toLocaleDateString() : 'N/A'}
                                        </span>
                                    </div>

                                    {/* Preview Text */}
                                    {item.previewText && (
                                        <p className="text-xs text-slate-400 italic mb-3 line-clamp-2 border-l-2 border-slate-700 pl-2">
                                            "{item.previewText}"
                                        </p>
                                    )}

                                    {/* Actors & Language */}
                                    <div className="flex flex-wrap gap-2 mb-3">
                                        <span className="text-[10px] font-bold bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded uppercase">
                                            {item.detectedLanguage}
                                        </span>
                                        {item.actors?.map(actor => (
                                            <span key={actor} className="text-[10px] bg-blue-900/40 text-blue-300 px-1.5 py-0.5 rounded">
                                                👤 {actor}
                                            </span>
                                        ))}
                                    </div>

                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div className="bg-red-500/10 text-red-300 px-2 py-1 rounded text-center border border-red-500/20">
                                            {item.summary?.critical || 0} Critical
                                        </div>
                                        <div className="bg-orange-500/10 text-orange-300 px-2 py-1 rounded text-center border border-orange-500/20">
                                            {item.summary?.material || 0} Material
                                        </div>
                                        <div className="bg-yellow-500/10 text-yellow-300 px-2 py-1 rounded text-center border border-yellow-500/20">
                                            {item.summary?.minor || 0} Minor
                                        </div>
                                        <div className="bg-blue-500/10 text-blue-300 px-2 py-1 rounded text-center border border-blue-500/20">
                                            {item.summary?.omission || 0} Omissions
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default HistoryViewer;
