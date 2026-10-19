import React, { useState, useEffect } from 'react';
import { Settings, Save, RotateCcw, CheckCircle2, AlertCircle, Shield, Sliders } from 'lucide-react';
import { ConfigSettings } from '../types';
import { fetchConfig, updateConfig } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<ConfigSettings | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Form State
  const [frameSkip, setFrameSkip] = useState<number>(2);
  const [confThreshold, setConfThreshold] = useState<number>(0.60);
  const [simThreshold, setSimThreshold] = useState<number>(0.60);
  const [timeoutSec, setTimeoutSec] = useState<number>(2.0);
  const [blurThreshold, setBlurThreshold] = useState<number>(50.0);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const c = await fetchConfig();
        setConfig(c);
        setFrameSkip(c.detection.frame_skip);
        setConfThreshold(c.detection.confidence_threshold);
        setSimThreshold(c.recognition.similarity_threshold);
        setTimeoutSec(c.tracking.track_lost_timeout_seconds);
        setBlurThreshold(c.recognition.blur_threshold);
      } catch (err: any) {
        setToast({ type: 'error', message: err.message || 'Failed to load configuration' });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setToast(null);

    try {
      await updateConfig({
        frame_skip: frameSkip,
        confidence_threshold: confThreshold,
        similarity_threshold: simThreshold,
        track_lost_timeout_seconds: timeoutSec,
        blur_threshold: blurThreshold,
      });
      setToast({ type: 'success', message: 'Configuration saved and persisted to config.json!' });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to update configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleResetDefaults = () => {
    setFrameSkip(2);
    setConfThreshold(0.60);
    setSimThreshold(0.60);
    setTimeoutSec(2.0);
    setBlurThreshold(50.0);
  };

  if (loading) {
    return <div className="py-20 text-center text-xs text-slate-400">Loading settings...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Toast Alert */}
      {toast && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-semibold ${
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600" />
            )}
            <span>{toast.message}</span>
          </div>
          <button onClick={() => setToast(null)} className="text-slate-400 hover:text-slate-600 font-bold">
            ×
          </button>
        </div>
      )}

      {/* Main Settings Form Card */}
      <form onSubmit={handleSave} className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="font-bold text-slate-800 text-base flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-600" />
              <span>AI Vision & Pipeline Configuration</span>
            </h3>
            <p className="text-xs text-slate-500">
              Tune parameters for detection throughput, ArcFace matching sensitivity, and track state timeouts
            </p>
          </div>
          <button
            type="button"
            onClick={handleResetDefaults}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
        </div>

        {/* Section 1: Detection Tuning */}
        <div className="space-y-4">
          <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
            Detection & Hardware Acceleration
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Frame Skip */}
            <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/60 space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>Detection Frame Skip Interval</span>
                <span className="font-mono text-indigo-600 font-bold">{frameSkip} frames</span>
              </div>
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={frameSkip}
                onChange={(e) => setFrameSkip(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Execute YOLO face detection every (N + 1) frames. Higher values conserve CPU/GPU compute, achieving 30+ FPS.
              </p>
            </div>

            {/* Confidence Threshold */}
            <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/60 space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>YOLO Detection Confidence Threshold</span>
                <span className="font-mono text-indigo-600 font-bold">{confThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.20"
                max="0.90"
                step="0.05"
                value={confThreshold}
                onChange={(e) => setConfThreshold(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Minimum bounding box probability required to validate a candidate face crop.
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Biometric Matching Tuning */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
            ArcFace Biometric Recognition & Quality Gating
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Similarity Threshold */}
            <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/60 space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>Cosine Similarity Matching Threshold</span>
                <span className="font-mono text-indigo-600 font-bold">{simThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.40"
                max="0.85"
                step="0.05"
                value={simThreshold}
                onChange={(e) => setSimThreshold(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Threshold for re-identifying an existing visitor. If similarity falls below this value, an auto-registration is created.
              </p>
            </div>

            {/* Blur Threshold */}
            <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/60 space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>Laplacian Blur Variance Threshold</span>
                <span className="font-mono text-indigo-600 font-bold">{blurThreshold.toFixed(0)}</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={blurThreshold}
                onChange={(e) => setBlurThreshold(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Rejects blurry face crops (Var(Laplacian) &lt; threshold) from corrupting the database embeddings.
              </p>
            </div>
          </div>
        </div>

        {/* Section 3: Tracking & Event Timeout */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
            Multi-Object Tracking Lifecycle
          </h4>

          <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/60 space-y-2 max-w-lg">
            <div className="flex justify-between text-xs font-semibold text-slate-700">
              <span>Track-Lost Timeout (Exit Trigger)</span>
              <span className="font-mono text-indigo-600 font-bold">{timeoutSec.toFixed(1)} seconds</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="5.0"
              step="0.5"
              value={timeoutSec}
              onChange={(e) => setTimeoutSec(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Duration a person must be missing from the camera frame before an official Exit event is logged.
            </p>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-indigo-600/30 transition disabled:opacity-50 cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
