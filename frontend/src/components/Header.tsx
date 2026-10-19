import React from 'react';
import { RefreshCw, Play, Square, AlertCircle } from 'lucide-react';
import { JobStatus } from '../types';

interface HeaderProps {
  title: string;
  subtitle: string;
  jobStatus?: JobStatus;
  onRefresh: () => void;
  onStopJob: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  jobStatus,
  onRefresh,
  onStopJob,
  isLoading,
}) => {
  const isRunning = jobStatus?.status === 'running';

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-xs sticky top-0 z-20">
      <div>
        <h2 className="text-xl font-bold text-slate-800 tracking-tight">{title}</h2>
        <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
      </div>

      <div className="flex items-center space-x-3">
        {/* Active Job Floating Status Badge */}
        {isRunning && (
          <div className="flex items-center space-x-3 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full text-xs text-emerald-800 font-medium shadow-xs">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>
              Processing: <strong className="font-semibold">{jobStatus.progress_percent}%</strong> (FPS: {jobStatus.fps})
            </span>
            <button
              onClick={onStopJob}
              title="Stop Job"
              className="p-1 hover:bg-emerald-200/60 rounded text-emerald-900 transition"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
            </button>
          </div>
        )}

        {jobStatus?.status === 'failed' && (
          <div className="flex items-center space-x-1.5 bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-full text-xs text-rose-700 font-medium">
            <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
            <span>Job Failed</span>
          </div>
        )}

        {/* Global Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-semibold shadow-2xs transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-indigo-600' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
};
