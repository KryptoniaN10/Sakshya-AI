import React, { useState } from 'react';
import type { ReportRow } from '../types';

interface Props {
    rows: ReportRow[];
}

const SeverityBadge = ({ severity }: { severity: string }) => {
    const colors = {
        Minor: "bg-yellow-500/20 text-yellow-300 border-yellow-500/50",
        Material: "bg-orange-500/20 text-orange-300 border-orange-500/50",
        Critical: "bg-red-500/20 text-red-300 border-red-500/50",
    };

    return (
        <span className={`px-2 py-1 rounded border text-xs font-bold uppercase ${colors[severity as keyof typeof colors] || "bg-gray-500"}`}>
            {severity}
        </span>
    );
};

const ConfrontationTable: React.FC<Props> = ({ rows }) => {
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const toggleExpand = (id: string) => {
        setExpandedId(expandedId === id ? null : id);
    };

    return (
        <div className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-800/50 shadow-xl">
            <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-900/50 text-xs uppercase text-slate-400">
                    <tr>
                        <th className="px-6 py-4">Severity</th>
                        <th className="px-6 py-4" title="Classification reflects semantic inconsistency, not truthfulness or credibility.">
                            Classification
                            <span className="ml-1 text-slate-500 cursor-help">ℹ️</span>
                        </th>
                        <th className="px-6 py-4">Prior Statement (FIR)</th>
                        <th className="px-6 py-4">Later Statement (Deposition)</th>
                        <th className="px-6 py-4">Legal Basis</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                    {rows.map((row) => (
                        <React.Fragment key={row.id}>
                            <tr
                                className={`hover:bg-slate-700/30 cursor-pointer transition-colors ${expandedId === row.id ? "bg-slate-700/40" : ""}`}
                                onClick={() => toggleExpand(row.id)}
                            >
                                <td className="px-6 py-4"><SeverityBadge severity={row.severity} /></td>
                                <td className="px-6 py-4 font-medium text-white capitalize">{row.classification.replace('_', ' ')}</td>
                                <td className="px-6 py-4 max-w-xs truncate" title={row.source_1}>{row.source_1}</td>
                                <td className="px-6 py-4 max-w-xs truncate" title={row.source_2}>{row.source_2}</td>
                                <td className="px-6 py-4 text-slate-400">Click to expand...</td>
                            </tr>
                            {expandedId === row.id && (
                                <tr className="bg-slate-900/30">
                                    <td colSpan={5} className="px-6 py-4">
                                        <div className="space-y-4 rounded bg-slate-800 p-4 border border-slate-700">
                                            <div>
                                                <h4 className="text-xs font-bold uppercase text-slate-500 mb-1">Legal Logic</h4>
                                                <p className="text-slate-200">{row.legal_basis}</p>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="p-3 bg-slate-900/50 rounded border border-slate-700/50">
                                                    <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">Source Reference A</h4>
                                                    <p className="italic text-slate-300">"{row.source_sentence_refs[0]}"</p>
                                                </div>
                                                <div className="p-3 bg-slate-900/50 rounded border border-slate-700/50">
                                                    <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">Source Reference B</h4>
                                                    <p className="italic text-slate-300">"{row.source_sentence_refs[1]}"</p>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </React.Fragment>
                    ))}
                    {rows.length === 0 && (
                        <tr>
                            <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                                No discrepancies found. Statements appear consistent.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
            <div className="px-6 py-2 bg-slate-900/80 border-t border-slate-800 text-xs text-slate-500 italic text-center">
                This analysis is structured for witness confrontation under Section 145 of the Bharatiya Sakshya Adhiniyam.
            </div>
        </div>
    );
};

export default ConfrontationTable;
