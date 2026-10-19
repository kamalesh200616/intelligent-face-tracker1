import React, { useState, useEffect } from 'react';
import {
  ClipboardList,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  LogIn,
  LogOut,
  Users,
  X,
  ExternalLink,
  Calendar,
} from 'lucide-react';
import { EventItem } from '../types';
import { fetchEvents } from '../services/api';

export const EventsPage: React.FC = () => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const pageSize = 15;

  // Modal for viewing full cropped image
  const [selectedCrop, setSelectedCrop] = useState<{ url: string; title: string } | null>(null);

  const loadEventsData = async () => {
    setLoading(true);
    try {
      const data = await fetchEvents({
        event_type: eventTypeFilter === 'all' ? undefined : eventTypeFilter,
        search: searchQuery.trim() || undefined,
        limit: pageSize,
        offset: page * pageSize,
      });
      setEvents(data.events);
      setTotal(data.total);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error fetching events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEventsData();
  }, [eventTypeFilter, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    loadEventsData();
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Top Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search Face ID or Event ID..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        </form>

        {/* Filter Pills */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => {
                setEventTypeFilter('all');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-lg transition ${
                eventTypeFilter === 'all' ? 'bg-white text-slate-800 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              All Events
            </button>
            <button
              onClick={() => {
                setEventTypeFilter('entry');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-lg transition ${
                eventTypeFilter === 'entry' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Entries Only
            </button>
            <button
              onClick={() => {
                setEventTypeFilter('exit');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-lg transition ${
                eventTypeFilter === 'exit' ? 'bg-amber-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Exits Only
            </button>
          </div>
        </div>
      </div>

      {/* Events Table Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-400">Loading events...</div>
        ) : events.length === 0 ? (
          <div className="py-20 text-center text-xs text-slate-400">
            No events match the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-600 uppercase text-[11px] font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Face Crop</th>
                  <th className="px-6 py-3.5">Event ID</th>
                  <th className="px-6 py-3.5">Face ID</th>
                  <th className="px-6 py-3.5">Event Type</th>
                  <th className="px-6 py-3.5">Track ID</th>
                  <th className="px-6 py-3.5">Confidence</th>
                  <th className="px-6 py-3.5">Timestamp (UTC)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {events.map((ev) => (
                  <tr key={ev.event_id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-3">
                      {ev.thumbnail_url ? (
                        <img
                          src={ev.thumbnail_url}
                          alt={ev.face_id}
                          onClick={() =>
                            setSelectedCrop({
                              url: ev.thumbnail_url!,
                              title: `${ev.face_id} (${ev.event_type.toUpperCase()} - Track #${ev.track_id})`,
                            })
                          }
                          className="w-11 h-11 rounded-lg object-cover border border-slate-200 shadow-2xs hover:scale-110 transition cursor-zoom-in"
                        />
                      ) : (
                        <div className="w-11 h-11 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400">
                          <Users className="w-5 h-5" />
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-3 font-mono text-[11px] text-slate-400">{ev.event_id}</td>
                    <td className="px-6 py-3 font-bold text-slate-900 font-mono">
                      <span className="bg-indigo-50 border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded-md">
                        {ev.face_id}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider ${
                          ev.event_type === 'entry'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {ev.event_type === 'entry' ? (
                          <LogIn className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <LogOut className="w-3 h-3 text-amber-600" />
                        )}
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-mono text-slate-600">Track #{ev.track_id}</td>
                    <td className="px-6 py-3 font-mono">
                      <div className="flex items-center space-x-2">
                        <span>{(ev.confidence * 100).toFixed(1)}%</span>
                        <div className="w-12 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-indigo-600 h-full rounded-full"
                            style={{ width: `${ev.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-slate-500 font-mono text-[11px]">
                      {new Date(ev.timestamp).toLocaleDateString()} {new Date(ev.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/60 flex items-center justify-between text-xs text-slate-500 font-medium">
          <div>
            Showing <strong className="font-semibold text-slate-700">{events.length}</strong> of{' '}
            <strong className="font-semibold text-slate-700">{total}</strong> total events
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 transition cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-slate-700">
              Page {page + 1} of {Math.max(1, totalPages)}
            </span>
            <button
              onClick={() => setPage((p) => (p + 1 < totalPages ? p + 1 : p))}
              disabled={page + 1 >= totalPages}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 transition cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Modal for viewing high-res cropped face */}
      {selectedCrop && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h4 className="font-bold text-slate-800 text-sm">{selectedCrop.title}</h4>
              <button
                onClick={() => setSelectedCrop(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-950 aspect-square flex items-center justify-center">
              <img
                src={selectedCrop.url}
                alt={selectedCrop.title}
                className="w-full h-full object-contain"
              />
            </div>
            <div className="text-[11px] text-slate-400 text-center font-mono">
              Audit Face Crop saved to structured filesystem directory.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
