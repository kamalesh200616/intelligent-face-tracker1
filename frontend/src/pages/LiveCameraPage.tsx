import React, { useState, useEffect } from 'react';
import {
  Camera,
  Play,
  Square,
  Shield,
  Eye,
  EyeOff,
  Radio,
  CheckCircle2,
  AlertTriangle,
  Info,
  Server,
  Zap,
} from 'lucide-react';
import { JobStatus } from '../types';
import { fetchJobStatus, startProcessingJob, stopProcessingJob } from '../services/api';

export const LiveCameraPage: React.FC = () => {
  const [rtspUrl, setRtspUrl] = useState<string>('rtsp://admin:password@192.168.1.100:554/stream1');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [streamLabel, setStreamLabel] = useState<string>('Main Entrance Camera');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const s = await fetchJobStatus();
        setJobStatus(s);
      } catch (e) {
        // Ignore
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 1500);
    return () => clearInterval(interval);
  }, []);

  const isStreaming = jobStatus?.status === 'running' && jobStatus?.source_type === 'rtsp';

  const handleStartStream = async () => {
    if (!rtspUrl.trim().startsWith('rtsp://')) {
      setErrorMsg('Please enter a valid RTSP stream URL beginning with "rtsp://".');
      return;
    }

    try {
      setErrorMsg(null);
      await startProcessingJob({
        source_type: 'rtsp',
        rtsp_url: rtspUrl.trim(),
      });
      const s = await fetchJobStatus();
      setJobStatus(s);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to start RTSP live camera stream');
    }
  };

  const handleStopStream = async () => {
    try {
      await stopProcessingJob();
      const s = await fetchJobStatus();
      setJobStatus(s);
    } catch (err: any) {
      alert(err.message || 'Failed to stop stream');
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Configuration Header Card */}
      <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-slate-800 text-lg flex items-center gap-2">
              <Camera className="w-5 h-5 text-indigo-600" />
              <span>Live Camera Stream Configuration</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Connect to enterprise IP security cameras and network video streams for real-time visitor tracking and counting
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-indigo-600 animate-pulse" />
            Live Ingestion Ready
          </span>
        </div>

        {/* Stream Settings Form */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1.5 md:col-span-1">
              <label className="text-xs font-semibold text-slate-700">Camera Name / Label</label>
              <input
                type="text"
                value={streamLabel}
                onChange={(e) => setStreamLabel(e.target.value)}
                placeholder="e.g. Lobby Entrance 01"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>

            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
                <span>RTSP Stream URL</span>
                <span className="text-[11px] text-slate-400 font-normal">Format: rtsp://user:pass@ip:port/path</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  placeholder="rtsp://admin:pass@192.168.1.100:554/live"
                  className="w-full pl-3.5 pr-10 py-2.5 rounded-xl border border-slate-200 text-xs font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* Privacy & Credential Security Note */}
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 flex items-start space-x-2.5 text-xs text-slate-600">
            <Shield className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div className="space-y-0.5 leading-relaxed">
              <span className="font-semibold text-slate-800">Zero-Leak Credential Protection:</span>
              <p className="text-[11px] text-slate-500">
                Passwords in RTSP URLs are strictly masked as <code className="bg-slate-200 px-1 py-0.5 rounded text-[10px]">***:***@</code> in server logs, API responses, and browser transcripts to maintain biometric and network security.
              </p>
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium">
              {errorMsg}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            {isStreaming ? (
              <button
                onClick={handleStopStream}
                className="flex items-center space-x-2 bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-rose-600/30 transition cursor-pointer"
              >
                <Square className="w-4 h-4 fill-current" />
                <span>Disconnect Stream</span>
              </button>
            ) : (
              <button
                onClick={handleStartStream}
                className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-indigo-600/30 transition cursor-pointer"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Connect & Start Live Tracking</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Live Stream Telemetry & Status Card */}
      <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2.5">
            <span
              className={`w-3 h-3 rounded-full ${
                isStreaming ? 'bg-emerald-500 animate-ping' : 'bg-slate-300'
              }`}
            />
            <h3 className="font-bold text-slate-800 text-base">
              Stream Telemetry: {isStreaming ? 'ACTIVE STREAMING' : 'DISCONNECTED'}
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-500">
            Protocol: RTSP / H.264
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-[11px] text-slate-500 font-semibold block uppercase">Frames Read</span>
            <span className="text-xl font-black text-slate-800 font-mono mt-1 block">
              {isStreaming ? jobStatus?.current_frame : 0}
            </span>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-[11px] text-slate-500 font-semibold block uppercase">Streaming FPS</span>
            <span className="text-xl font-black text-emerald-600 font-mono mt-1 block">
              {isStreaming ? jobStatus?.fps : 0.0}
            </span>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-[11px] text-slate-500 font-semibold block uppercase">Active Tracks</span>
            <span className="text-xl font-black text-indigo-600 font-mono mt-1 block">
              {isStreaming ? jobStatus?.active_tracks : 0}
            </span>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-[11px] text-slate-500 font-semibold block uppercase">Unique Visitors</span>
            <span className="text-xl font-black text-slate-800 font-mono mt-1 block">
              {isStreaming ? jobStatus?.unique_visitors : 0}
            </span>
          </div>
        </div>

        {/* Reconnect Resilience Notice */}
        <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs text-indigo-900 flex items-start space-x-2.5">
          <Zap className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed text-[11px]">
            <strong>Automatic Network Reconnection Active:</strong> If the network camera stream drops or suffers packet loss, the backend automatically performs exponential backoff reconnect attempts up to 5 times (2s, 3s, 4.5s...) without dropping database sessions or interrupting active tracking state.
          </p>
        </div>
      </div>
    </div>
  );
};
