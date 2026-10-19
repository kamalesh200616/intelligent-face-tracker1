import React, { useState, useEffect } from 'react';
import { Activity, Clock, CheckCircle2, AlertCircle, RefreshCw, FileVideo, Camera } from 'lucide-react';
import { SessionItem } from '../types';
import { fetchSessions } from '../services/api';

export const HistoryPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await fetchSessions();
      setSessions(data.sessions);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error loading processing history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-800 text-base">Processing Run History</h3>
          <p className="text-xs text-slate-500">
            Audit log of all video processing jobs recorded in the SQLite database
          </p>
        </div>
        <button
          onClick={loadSessions}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-semibold shadow-2xs transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          <span>Refresh Runs</span>
        </button>
      </div>

      {/* Sessions Table Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-400">Loading processing runs...</div>
        ) : sessions.length === 0 ? (
          <div className="py-20 text-center text-xs text-slate-400">
            No processing runs recorded yet. Process a video to create a run record.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-600 uppercase text-[11px] font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Session ID</th>
                  <th className="px-6 py-3.5">Source Type</th>
                  <th className="px-6 py-3.5">Source Target</th>
                  <th className="px-6 py-3.5">Started At</th>
                  <th className="px-6 py-3.5">Duration / Ended</th>
                  <th className="px-6 py-3.5">Frames Processed</th>
                  <th className="px-6 py-3.5">Unique Visitors</th>
                  <th className="px-6 py-3.5">Terminal Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {sessions.map((sess) => (
                  <tr key={sess.session_id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-3 font-mono font-bold text-slate-900">
                      {sess.session_id}
                    </td>
                    <td className="px-6 py-3">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-700 uppercase">
                        {sess.source_type === 'rtsp' ? (
                          <Camera className="w-3.5 h-3.5 text-cyan-600" />
                        ) : (
                          <FileVideo className="w-3.5 h-3.5 text-indigo-600" />
                        )}
                        {sess.source_type}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-mono text-slate-600 max-w-xs truncate" title={sess.source_path}>
                      {sess.source_path}
                    </td>
                    <td className="px-6 py-3 text-slate-500 font-mono text-[11px]">
                      {new Date(sess.started_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 text-slate-500 font-mono text-[11px]">
                      {sess.ended_at ? new Date(sess.ended_at).toLocaleTimeString() : 'Running...'}
                    </td>
                    <td className="px-6 py-3 font-mono font-semibold text-slate-800">
                      {sess.total_frames} frames
                    </td>
                    <td className="px-6 py-3 font-mono font-bold text-indigo-600">
                      {sess.unique_faces_count}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider ${
                          sess.status === 'COMPLETED'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : sess.status === 'RUNNING'
                            ? 'bg-indigo-50 text-indigo-700 border border-indigo-200 animate-pulse'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {sess.status === 'COMPLETED' ? (
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        ) : sess.status === 'RUNNING' ? (
                          <Activity className="w-3 h-3 text-indigo-600" />
                        ) : (
                          <AlertCircle className="w-3 h-3 text-rose-600" />
                        )}
                        {sess.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
