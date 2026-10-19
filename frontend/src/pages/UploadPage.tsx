import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  FileVideo,
  Play,
  Square,
  CheckCircle2,
  AlertCircle,
  Sliders,
  Users,
  LogIn,
  LogOut,
  ArrowRight,
  Film,
  RotateCcw,
  FolderOpen,
} from 'lucide-react';
import { JobStatus, UploadedVideoItem } from '../types';
import {
  fetchJobStatus,
  fetchUploadedVideos,
  resetJobStatus,
  startProcessingJob,
  stopProcessingJob,
  uploadVideoFile,
} from '../services/api';

interface UploadPageProps {
  onNavigate: (tab: string) => void;
}

export const UploadPage: React.FC<UploadPageProps> = ({ onNavigate }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [serverFilePath, setServerFilePath] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  // Available local videos in data/uploads
  const [availableVideos, setAvailableVideos] = useState<UploadedVideoItem[]>([]);
  const [loadingVideos, setLoadingVideos] = useState<boolean>(false);

  // Job tuning options
  const [frameSkip, setFrameSkip] = useState<number>(2);
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.52);

  // Job state polling
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load available videos from data/uploads
  const refreshAvailableVideos = async () => {
    setLoadingVideos(true);
    try {
      const res = await fetchUploadedVideos();
      setAvailableVideos(res.videos);
    } catch (e) {
      // Non-fatal
    } finally {
      setLoadingVideos(false);
    }
  };

  useEffect(() => {
    refreshAvailableVideos();
  }, []);

  // Poll job status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await fetchJobStatus();
        setJobStatus(status);
      } catch (e) {
        // Ignore polling errors
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 1500);
    return () => clearInterval(interval);
  }, []);

  const handleSelectLocalVideo = async (vid: UploadedVideoItem) => {
    setSelectedFile(null);
    setUploadError(null);
    setServerFilePath(vid.file_path);
    setPreviewUrl(vid.preview_url);
    try {
      await resetJobStatus();
      setJobStatus(null);
    } catch (e) {
      // Ignore
    }
  };

  const handleFileChange = async (file: File) => {
    const validExtensions = ['.mp4', '.avi', '.mkv', '.mov'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setUploadError(`Invalid video file type (${ext}). Please upload an MP4, AVI, MKV, or MOV file.`);
      return;
    }

    setSelectedFile(file);
    setUploadError(null);
    setIsUploading(true);

    try {
      const res = await uploadVideoFile(file);
      setPreviewUrl(res.preview_url);
      setServerFilePath(res.file_path);
      await resetJobStatus();
      setJobStatus(null);
      refreshAvailableVideos();
    } catch (err: any) {
      setUploadError(err.message || 'Error uploading file to server');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleUseSampleVideo = async () => {
    setServerFilePath('data/sample_video.mp4');
    setPreviewUrl('/static/uploads/sample_video.mp4');
    setSelectedFile(null);
    setUploadError(null);
    try {
      await resetJobStatus();
      setJobStatus(null);
    } catch (e) {
      // Ignore
    }
  };

  const handleResetJob = async () => {
    try {
      await resetJobStatus();
      const updated = await fetchJobStatus();
      setJobStatus(updated);
    } catch (e) {
      // Ignore
    }
  };

  const handleStartProcessing = async () => {
    if (!serverFilePath) {
      setUploadError('Please select or upload a video file first.');
      return;
    }

    try {
      setUploadError(null);
      await startProcessingJob({
        source_type: 'file',
        file_path: serverFilePath,
        frame_skip: frameSkip,
        similarity_threshold: similarityThreshold,
      });
      // Refresh status
      const updated = await fetchJobStatus();
      setJobStatus(updated);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to start processing');
    }
  };

  const handleStopProcessing = async () => {
    try {
      await stopProcessingJob();
      const updated = await fetchJobStatus();
      setJobStatus(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to stop processing');
    }
  };

  const isRunning = jobStatus?.status === 'running';
  const isCompleted = jobStatus?.status === 'completed';

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Upload & Source Selection Card */}
      <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs space-y-6">
        <div>
          <h3 className="font-bold text-slate-800 text-lg">Select Video Source</h3>
          <p className="text-xs text-slate-500">
            Upload custom footage or run the preloaded Katomaran demonstration video
          </p>
        </div>

        {/* Drag and Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            isDragOver
              ? 'border-indigo-500 bg-indigo-50/50 scale-[1.005]'
              : 'border-slate-200 hover:border-slate-300 bg-slate-50/40 hover:bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/avi,video/mkv,video/quicktime"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileChange(e.target.files[0]);
              }
            }}
          />
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3 shadow-xs">
            <UploadCloud className="w-7 h-7" />
          </div>
          <h4 className="font-bold text-slate-800 text-sm">
            {isUploading ? 'Uploading Video...' : 'Drag and drop video here, or Browse Files'}
          </h4>
          <p className="text-xs text-slate-400 mt-1">
            Supports MP4, AVI, MKV, MOV up to 500MB
          </p>
          {selectedFile && (
            <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 bg-indigo-50 border border-indigo-200 rounded-full text-xs text-indigo-700 font-semibold">
              <FileVideo className="w-3.5 h-3.5" />
              <span>{selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(1)} MB)</span>
            </div>
          )}
        </div>

        {/* Available Local Videos in data/uploads */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
              <FolderOpen className="w-4 h-4 text-indigo-600" />
              <span>Available Test Videos in data/uploads</span>
            </div>
            <button
              onClick={refreshAvailableVideos}
              className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center space-x-1 cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Refresh</span>
            </button>
          </div>

          {availableVideos.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {availableVideos.map((vid) => {
                const isSelected = serverFilePath === vid.file_path;
                return (
                  <div
                    key={vid.filename}
                    onClick={() => handleSelectLocalVideo(vid)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition flex flex-col justify-between space-y-2 ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-50/60 shadow-xs'
                        : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/70'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1.5 font-bold text-slate-800 truncate">
                        <FileVideo className={`w-4 h-4 shrink-0 ${isSelected ? 'text-indigo-600' : 'text-slate-500'}`} />
                        <span className="truncate" title={vid.filename}>{vid.filename}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {vid.size_mb} MB
                      </div>
                    </div>
                    <button
                      type="button"
                      className={`w-full py-1.5 rounded-lg font-bold text-[11px] transition cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-600 text-white shadow-2xs'
                          : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {isSelected ? '✓ Selected' : 'Select Video'}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center text-xs text-slate-400">
              {loadingVideos ? 'Scanning data/uploads...' : 'No video files currently in data/uploads.'}
            </div>
          )}
        </div>

        {/* Preset Sample Video Shortcut */}
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200/60 text-xs">
          <div className="flex items-center space-x-2 text-slate-600">
            <Film className="w-4 h-4 text-indigo-600" />
            <span>
              Or use the pre-generated sample corridor test video (<strong>data/sample_video.mp4</strong>)
            </span>
          </div>
          <button
            onClick={handleUseSampleVideo}
            className="px-3 py-1.5 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold rounded-lg shadow-2xs transition cursor-pointer"
          >
            Use Sample Video
          </button>
        </div>

        {/* Error message */}
        {uploadError && (
          <div className="flex items-center space-x-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Video Preview Player */}
        {previewUrl && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-slate-600 flex items-center justify-between">
              <span>Video Preview Player</span>
              <span className="text-slate-400 font-mono text-[11px] truncate max-w-md">{serverFilePath}</span>
            </div>
            <div className="rounded-xl overflow-hidden border border-slate-200 bg-black aspect-video max-h-80 flex items-center justify-center">
              <video
                src={previewUrl}
                controls
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        )}

        {/* AI Parameters Tuning */}
        <div className="pt-4 border-t border-slate-100 space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
            <Sliders className="w-4 h-4 text-indigo-600" />
            <span>Processing Pipeline Settings</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
            {/* Frame Skip */}
            <div className="space-y-1.5 bg-slate-50/70 p-3.5 rounded-xl border border-slate-200/60">
              <div className="flex justify-between font-semibold text-slate-700">
                <span>Detection Frame Skip</span>
                <span className="font-mono text-indigo-600 font-bold">{frameSkip} frames</span>
              </div>
              <input
                type="range"
                min="0"
                max="5"
                step="1"
                value={frameSkip}
                onChange={(e) => setFrameSkip(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Skips face detection every N frames to accelerate throughput to 30+ FPS.
              </p>
            </div>

            {/* Similarity Threshold */}
            <div className="space-y-1.5 bg-slate-50/70 p-3.5 rounded-xl border border-slate-200/60">
              <div className="flex justify-between font-semibold text-slate-700">
                <span>ArcFace Similarity Threshold</span>
                <span className="font-mono text-indigo-600 font-bold">{similarityThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.40"
                max="0.80"
                step="0.02"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Cosine similarity required to re-identify an existing identity.
              </p>
            </div>
          </div>
        </div>

        {/* Launch / Stop Actions */}
        <div className="flex items-center justify-end space-x-3 pt-3">
          {jobStatus && jobStatus.status !== 'idle' && !isRunning && (
            <button
              onClick={handleResetJob}
              className="flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2.5 rounded-xl font-bold text-xs transition cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear Job Status</span>
            </button>
          )}

          {isRunning ? (
            <button
              onClick={handleStopProcessing}
              className="flex items-center space-x-2 bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-rose-600/30 transition cursor-pointer"
            >
              <Square className="w-4 h-4 fill-current" />
              <span>Cancel Processing Job</span>
            </button>
          ) : (
            <button
              onClick={handleStartProcessing}
              disabled={!serverFilePath}
              className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-indigo-600/30 transition cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start AI Processing</span>
            </button>
          )}
        </div>
      </div>

      {/* Live Processing Status Card */}
      {jobStatus && jobStatus.status !== 'idle' && (
        <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <span
                className={`w-3 h-3 rounded-full ${
                  isRunning
                    ? 'bg-emerald-500 animate-ping'
                    : isCompleted
                    ? 'bg-emerald-500'
                    : 'bg-rose-500'
                }`}
              />
              <h3 className="font-bold text-slate-800 text-base">
                Job Status: <span className="uppercase">{jobStatus.status}</span>
              </h3>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-xs text-slate-400 font-mono">
                Job ID: {jobStatus.job_id}
              </span>
              {!isRunning && (
                <button
                  onClick={handleResetJob}
                  className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
                  title="Reset to idle"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold text-slate-600 font-mono">
              <span>
                Processed Frames: {jobStatus.current_frame} / {jobStatus.total_frames || 'N/A'}
              </span>
              <span>{jobStatus.progress_percent}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  isRunning
                    ? 'bg-gradient-to-r from-indigo-500 to-cyan-400'
                    : isCompleted
                    ? 'bg-emerald-500'
                    : 'bg-rose-500'
                }`}
                style={{ width: `${Math.max(jobStatus.progress_percent, 5)}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-400 font-mono pt-1">
              <span>Throughput: {jobStatus.fps} FPS</span>
              <span>Elapsed: {jobStatus.elapsed_seconds}s</span>
            </div>
          </div>

          {/* Live Visitor Metrics Grid */}
          <div className="grid grid-cols-3 gap-4 pt-2">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/60 text-center">
              <Users className="w-5 h-5 text-indigo-600 mx-auto mb-1" />
              <div className="text-2xl font-black text-slate-800">
                {jobStatus.unique_visitors}
              </div>
              <div className="text-[11px] text-slate-500 font-medium">Session Unique Visitors</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/60 text-center">
              <LogIn className="w-5 h-5 text-emerald-600 mx-auto mb-1" />
              <div className="text-2xl font-black text-slate-800">
                {jobStatus.total_entries}
              </div>
              <div className="text-[11px] text-slate-500 font-medium">Session Entry Events</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/60 text-center">
              <LogOut className="w-5 h-5 text-amber-600 mx-auto mb-1" />
              <div className="text-2xl font-black text-slate-800">
                {jobStatus.total_exits}
              </div>
              <div className="text-[11px] text-slate-500 font-medium">Session Exit Events</div>
            </div>
          </div>

          {/* Completion Action Alert */}
          {isCompleted && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between text-xs text-emerald-900">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>
                  Processing successfully completed for this video! Session visitor counts and audit events are recorded in the database.
                </span>
              </div>
              <button
                onClick={() => onNavigate('events')}
                className="flex items-center space-x-1 font-bold text-emerald-800 hover:text-emerald-950 underline shrink-0 cursor-pointer"
              >
                <span>View Events</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
