import React, { useEffect, useState } from 'react';
import {
  Users,
  LogIn,
  LogOut,
  Building2,
  TrendingUp,
  Clock,
  Play,
  Square,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { EventItem, JobStatus, Stats, TemporalAnalytics } from '../types';
import { fetchEvents, fetchStats, fetchTemporalAnalytics, stopProcessingJob } from '../services/api';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentEvents, setRecentEvents] = useState<EventItem[]>([]);
  const [temporal, setTemporal] = useState<TemporalAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    try {
      const [statsData, eventsData, temporalData] = await Promise.all([
        fetchStats(),
        fetchEvents({ limit: 6 }),
        fetchTemporalAnalytics(),
      ]);
      setStats(statsData);
      setRecentEvents(eventsData.events);
      setTemporal(temporalData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error loading dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    // Poll stats every 3 seconds for live updates
    const interval = setInterval(loadDashboardData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleStopJob = async () => {
    try {
      await stopProcessingJob();
      loadDashboardData();
    } catch (err: any) {
      alert(err.message || 'Failed to stop job');
    }
  };

  const isJobRunning = stats?.active_job?.status === 'running';

  return (
    <div className="space-y-6">
      {/* Active Processing Job Banner */}
      {isJobRunning && stats?.active_job && (
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 text-white shadow-xl border border-indigo-500/30 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 flex-1 w-full">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs uppercase font-bold tracking-wider text-emerald-400">
                Live Video Processing in Progress
              </span>
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              Processing: {stats.active_job.source_path.split(/[\\/]/).pop()}
            </h3>
            <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden border border-slate-700">
              <div
                className="bg-gradient-to-r from-cyan-400 to-indigo-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.max(stats.active_job.progress_percent, 5)}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-slate-400 pt-1 font-mono">
              <span>
                Frame: <strong>{stats.active_job.current_frame}</strong> /{' '}
                {stats.active_job.total_frames || 'Stream'}
              </span>
              <span>Speed: <strong>{stats.active_job.fps} FPS</strong></span>
              <span>Progress: <strong>{stats.active_job.progress_percent}%</strong></span>
            </div>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={handleStopJob}
              className="flex items-center space-x-2 bg-rose-600 hover:bg-rose-700 text-white px-4 py-2.5 rounded-xl font-semibold text-xs transition shadow-lg shadow-rose-600/30 cursor-pointer"
            >
              <Square className="w-4 h-4 fill-current" />
              <span>Stop Processing</span>
            </button>
          </div>
        </div>
      )}

      {/* 4 Primary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Unique Visitors */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Unique Visitors
            </span>
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h4 className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {stats?.total_unique_visitors ?? (loading ? '...' : 0)}
            </h4>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1 font-medium">
              <span className="text-emerald-600 font-semibold">Distinct Biometric IDs</span>
              <span>(No double count)</span>
            </p>
          </div>
        </div>

        {/* Card 2: Total Entries */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Entries
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <LogIn className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h4 className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {stats?.total_entries ?? (loading ? '...' : 0)}
            </h4>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1 font-medium">
              <span>Confirmed Arrivals</span>
            </p>
          </div>
        </div>

        {/* Card 3: Total Exits */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Exits
            </span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <LogOut className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h4 className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {stats?.total_exits ?? (loading ? '...' : 0)}
            </h4>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1 font-medium">
              <span>Confirmed Departures</span>
            </p>
          </div>
        </div>

        {/* Card 4: Current Occupancy */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              In-Camera Estimate
            </span>
            <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
              <Building2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h4 className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {stats?.current_occupancy ?? (loading ? '...' : 0)}
            </h4>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1 font-medium">
              <span>Current Present (Entries - Exits)</span>
            </p>
          </div>
        </div>
      </div>

      {/* Visual Analytics & Quick Actions Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Timeline Chart Card */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-slate-800 text-base">Visitor Activity Overview</h3>
              <p className="text-xs text-slate-500">Distribution of confirmed Entry and Exit events</p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="flex items-center gap-1.5 font-medium text-emerald-700">
                <span className="w-3 h-3 rounded bg-emerald-500 inline-block" /> Entries
              </span>
              <span className="flex items-center gap-1.5 font-medium text-amber-700">
                <span className="w-3 h-3 rounded bg-amber-500 inline-block" /> Exits
              </span>
            </div>
          </div>

          {/* Simple Responsive Bar Chart */}
          {temporal && temporal.hourly_activity.length > 0 ? (
            <div className="space-y-3 pt-2">
              {temporal.hourly_activity.map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600">
                    <span>Hour {item.hour}</span>
                    <span>{item.entries} in / {item.exits} out</span>
                  </div>
                  <div className="flex h-3 rounded-full overflow-hidden bg-slate-100">
                    <div
                      className="bg-emerald-500 transition-all duration-500"
                      style={{ width: `${Math.min(100, item.entries * 25)}%` }}
                    />
                    <div
                      className="bg-amber-500 transition-all duration-500"
                      style={{ width: `${Math.min(100, item.exits * 25)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 text-xs">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              No historical event distribution recorded yet. Process a video to generate analytics.
            </div>
          )}
        </div>

        {/* Quick Launch & Actions */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-800 text-base mb-1">Quick Actions</h3>
            <p className="text-xs text-slate-500 mb-5">Launch new processing jobs or configure camera</p>

            <div className="space-y-3">
              <button
                onClick={() => onNavigate('upload')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl border border-slate-200 hover:border-indigo-400 bg-slate-50/50 hover:bg-indigo-50/40 text-left transition group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-bold text-slate-800 group-hover:text-indigo-700">
                    Upload Video File
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Process MP4/AVI with YOLO & ArcFace
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition" />
              </button>

              <button
                onClick={() => onNavigate('live')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl border border-slate-200 hover:border-cyan-400 bg-slate-50/50 hover:bg-cyan-50/40 text-left transition group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-bold text-slate-800 group-hover:text-cyan-700">
                    Connect Live Camera
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Stream directly from IP security cameras
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-cyan-600 group-hover:translate-x-0.5 transition" />
              </button>

              <button
                onClick={() => onNavigate('identities')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl border border-slate-200 hover:border-violet-400 bg-slate-50/50 hover:bg-violet-50/40 text-left transition group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-bold text-slate-800 group-hover:text-violet-700">
                    Registered Identities Directory
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Inspect unique biometric profiles
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-violet-600 group-hover:translate-x-0.5 transition" />
              </button>
            </div>
          </div>

          <div className="pt-5 mt-5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Database: SQLite (WAL)</span>
            <span className="text-indigo-600 font-semibold flex items-center gap-1">
              ACID Compliant
            </span>
          </div>
        </div>
      </div>

      {/* Recent Visitor Events Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-slate-800 text-base">Recent Visitor Events</h3>
            <p className="text-xs text-slate-500">Latest confirmed Entry and Exit detections</p>
          </div>
          <button
            onClick={() => onNavigate('events')}
            className="flex items-center space-x-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
          >
            <span>View All Events</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentEvents.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            No events logged yet. Process a video file to record entries and exits.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-600 uppercase text-[11px] font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Face Crop</th>
                  <th className="px-6 py-3.5">Face ID</th>
                  <th className="px-6 py-3.5">Event Type</th>
                  <th className="px-6 py-3.5">Track ID</th>
                  <th className="px-6 py-3.5">Confidence</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {recentEvents.map((ev) => (
                  <tr key={ev.event_id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-3">
                      {ev.thumbnail_url ? (
                        <img
                          src={ev.thumbnail_url}
                          alt={ev.face_id}
                          className="w-10 h-10 rounded-lg object-cover border border-slate-200 shadow-2xs"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400">
                          <Users className="w-4 h-4" />
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-3 font-semibold text-slate-800 font-mono">
                      {ev.face_id}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider ${
                          ev.event_type === 'entry'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-mono text-slate-500">#{ev.track_id}</td>
                    <td className="px-6 py-3 font-mono">{(ev.confidence * 100).toFixed(1)}%</td>
                    <td className="px-6 py-3 text-slate-500 font-mono">
                      {new Date(ev.timestamp).toLocaleTimeString()} ({new Date(ev.timestamp).toLocaleDateString()})
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
