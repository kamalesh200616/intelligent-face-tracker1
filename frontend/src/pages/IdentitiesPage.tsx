import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  ShieldCheck,
  Calendar,
  Clock,
  History,
  X,
  LogIn,
  LogOut,
  Sparkles,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import { IdentityItem } from '../types';
import { deleteIdentity, fetchIdentities, fetchIdentityDetail } from '../services/api';

export const IdentitiesPage: React.FC = () => {
  const [identities, setIdentities] = useState<IdentityItem[]>([]);
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal
  const [selectedVisitor, setSelectedVisitor] = useState<any | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);

  // Delete Confirmation Modal
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadIdentities = async () => {
    setLoading(true);
    try {
      const data = await fetchIdentities();
      setIdentities(data.identities);
    } catch (err: any) {
      setError(err.message || 'Error loading identities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIdentities();
  }, []);

  const handleOpenDetail = async (faceId: string) => {
    setLoadingDetail(true);
    try {
      const data = await fetchIdentityDetail(faceId);
      setSelectedVisitor(data);
    } catch (e) {
      alert(`Could not load history for ${faceId}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deletingId) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteIdentity(deletingId);
      setIdentities((prev) => prev.filter((item) => item.face_id !== deletingId));
      setDeletingId(null);
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete identity');
    } finally {
      setIsDeleting(false);
    }
  };

  const filtered = identities.filter(
    (id) =>
      id.face_id.toLowerCase().includes(search.toLowerCase()) ||
      id.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Banner and Search Bar */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-slate-800 text-base">Registered Biometric Identities</h3>
          <p className="text-xs text-slate-500">
            Unique visitors automatically enrolled by the ArcFace deep embedding pipeline
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search visitor ID or label..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        </div>
      </div>

      {/* Identities Grid */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400">Loading registered identities...</div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl p-16 text-center text-xs text-slate-400 border border-slate-200">
          <Users className="w-10 h-10 mx-auto text-slate-300 mb-2" />
          No registered identities match your search query.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((item) => (
            <div
              key={item.face_id}
              className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    {item.thumbnail_url ? (
                      <img
                        src={item.thumbnail_url}
                        alt={item.face_id}
                        className="w-14 h-14 rounded-xl object-cover border border-slate-200 shadow-2xs"
                      />
                    ) : (
                      <div className="w-14 h-14 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center">
                        <Users className="w-7 h-7" />
                      </div>
                    )}
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm">{item.name}</h4>
                      <span className="inline-block px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-mono text-[11px] font-bold mt-0.5">
                        {item.face_id}
                      </span>
                    </div>
                  </div>
                  <span className="px-2 py-1 rounded-md text-[10px] font-extrabold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {item.total_visits} {item.total_visits === 1 ? 'Visit' : 'Visits'}
                  </span>
                </div>

                <div className="space-y-1 text-[11px] text-slate-500 font-mono bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <div className="flex justify-between">
                    <span className="text-slate-400">First Enrolled:</span>
                    <span>{new Date(item.first_seen).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Latest Sighting:</span>
                    <span>{new Date(item.last_seen).toLocaleDateString()} {new Date(item.last_seen).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Biometric Shield Pill */}
                <div className="flex items-center space-x-1.5 text-[11px] text-indigo-700 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <span>ArcFace 512-D Biometric Embedding Secured</span>
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <button
                  onClick={() => handleOpenDetail(item.face_id)}
                  className="flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl border border-slate-200 hover:border-indigo-300 bg-white hover:bg-indigo-50/50 text-indigo-600 font-bold text-xs shadow-2xs transition cursor-pointer"
                >
                  <History className="w-3.5 h-3.5" />
                  <span>View History</span>
                </button>
                <button
                  onClick={() => {
                    setDeleteError(null);
                    setDeletingId(item.face_id);
                  }}
                  title={`Delete visitor ${item.face_id}`}
                  className="p-2 rounded-xl border border-slate-200 hover:border-rose-300 bg-white hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Visitor Event History Modal */}
      {selectedVisitor && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 shrink-0">
              <div>
                <h4 className="font-bold text-slate-800 text-base">
                  Event History for {selectedVisitor.name}
                </h4>
                <p className="text-xs text-slate-500 font-mono">
                  Persistent Identity: {selectedVisitor.face_id}
                </p>
              </div>
              <button
                onClick={() => setSelectedVisitor(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-3 flex-1 pr-1">
              {selectedVisitor.events && selectedVisitor.events.length > 0 ? (
                selectedVisitor.events.map((ev: any) => (
                  <div
                    key={ev.event_id}
                    className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center space-x-3">
                      {ev.thumbnail_url ? (
                        <img
                          src={ev.thumbnail_url}
                          alt={ev.event_id}
                          className="w-12 h-12 rounded-lg object-cover border border-slate-200"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-lg bg-slate-200 flex items-center justify-center text-slate-400">
                          <Users className="w-5 h-5" />
                        </div>
                      )}
                      <div>
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                            ev.event_type === 'entry'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {ev.event_type === 'entry' ? (
                            <LogIn className="w-3 h-3 text-emerald-600" />
                          ) : (
                            <LogOut className="w-3 h-3 text-amber-600" />
                          )}
                          {ev.event_type}
                        </span>
                        <div className="font-mono text-slate-700 text-[11px] mt-1">
                          {new Date(ev.timestamp).toLocaleDateString()} {new Date(ev.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-right font-mono text-[11px] text-slate-400">
                      <div>Confidence: {(ev.confidence * 100).toFixed(1)}%</div>
                      <div className="text-[10px]">{ev.event_id}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-xs text-slate-400">
                  No events found for this identity.
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end shrink-0">
              <button
                onClick={() => setSelectedVisitor(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5 text-rose-600" />
              </div>
              <div>
                <h4 className="font-bold text-slate-800 text-base">
                  Delete Visitor Identity?
                </h4>
                <p className="text-xs text-slate-500 font-mono">
                  Target: {deletingId}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to permanently delete visitor identity <strong>{deletingId}</strong>?
              This will remove the ArcFace embedding vector and all associated entry and exit events from the database.
              This action cannot be undone.
            </p>

            {deleteError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end space-x-2.5 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setDeletingId(null)}
                disabled={isDeleting}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl shadow-xs transition flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{isDeleting ? 'Deleting...' : 'Delete Permanently'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
