export interface Stats {
  total_unique_visitors: number;
  total_entries: number;
  total_exits: number;
  current_occupancy: number;
  active_job: JobStatus;
}

export interface JobStatus {
  job_id: string | null;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped';
  source_type: string;
  source_path: string;
  current_frame: number;
  total_frames: number;
  progress_percent: number;
  fps: number;
  unique_visitors: number;
  total_entries: number;
  total_exits: number;
  active_tracks: number;
  error_message: string | null;
  start_time: string | null;
  end_time: string | null;
  elapsed_seconds: number;
}

export interface EventItem {
  event_id: string;
  session_id?: string;
  face_id: string;
  track_id: number;
  event_type: 'entry' | 'exit';
  timestamp: string;
  confidence: number;
  thumbnail_url: string | null;
  has_thumbnail: boolean;
}

export interface UploadedVideoItem {
  filename: string;
  file_path: string;
  preview_url: string;
  size_bytes: number;
  size_mb: number;
  modified_iso: string;
}

export interface IdentityItem {
  face_id: string;
  name: string;
  first_seen: string;
  last_seen: string;
  total_visits: number;
  metadata: Record<string, any>;
  thumbnail_url: string | null;
  has_thumbnail: boolean;
}

export interface SessionItem {
  session_id: string;
  source_type: string;
  source_path: string;
  started_at: string;
  ended_at: string | null;
  total_frames: number;
  unique_faces_count: number;
  status: string;
}

export interface ConfigSettings {
  detection: {
    model_type: string;
    confidence_threshold: number;
    nms_threshold: number;
    frame_skip: number;
    device: string;
  };
  recognition: {
    model_type: string;
    similarity_threshold: number;
    blur_threshold: number;
    min_face_size: number[];
  };
  tracking: {
    tracker_type: string;
    iou_threshold: number;
    min_hits_to_confirm: number;
    track_lost_timeout_seconds: number;
    max_lost_frames: number;
  };
}

export interface TemporalAnalytics {
  hourly_activity: Array<{ hour: string; entries: number; exits: number }>;
  session_comparison: Array<{ session: string; visitors: number; frames: number }>;
}
