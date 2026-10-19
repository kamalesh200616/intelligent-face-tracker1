import {
  ConfigSettings,
  EventItem,
  IdentityItem,
  JobStatus,
  SessionItem,
  Stats,
  TemporalAnalytics,
  UploadedVideoItem,
} from '../types';

const API_BASE = '/api';

export async function fetchUploadedVideos(): Promise<{ total: number; videos: UploadedVideoItem[] }> {
  const res = await fetch(`${API_BASE}/uploads`);
  if (!res.ok) throw new Error('Failed to load available uploaded videos');
  return res.json();
}

export async function deleteIdentity(faceId: string): Promise<{ success: boolean; message: string; face_id: string }> {
  const res = await fetch(`${API_BASE}/identities/${faceId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete identity ${faceId}`);
  }
  return res.json();
}

export async function resetJobStatus(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/jobs/reset`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reset job status');
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to load dashboard statistics');
  return res.json();
}

export async function fetchEvents(params?: {
  face_id?: string;
  event_type?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; events: EventItem[] }> {
  const query = new URLSearchParams();
  if (params?.face_id) query.set('face_id', params.face_id);
  if (params?.event_type) query.set('event_type', params.event_type);
  if (params?.search) query.set('search', params.search);
  if (params?.limit) query.set('limit', params.limit.toString());
  if (params?.offset !== undefined) query.set('offset', params.offset.toString());

  const res = await fetch(`${API_BASE}/events?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load events');
  return res.json();
}

export async function fetchIdentities(): Promise<{ total: number; identities: IdentityItem[] }> {
  const res = await fetch(`${API_BASE}/identities`);
  if (!res.ok) throw new Error('Failed to load registered identities');
  return res.json();
}

export async function fetchIdentityDetail(faceId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/identities/${faceId}`);
  if (!res.ok) throw new Error(`Failed to load identity detail for ${faceId}`);
  return res.json();
}

export async function fetchSessions(): Promise<{ total: number; sessions: SessionItem[] }> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error('Failed to load processing sessions');
  return res.json();
}

export async function uploadVideoFile(file: File): Promise<{
  success: boolean;
  filename: string;
  file_path: string;
  preview_url: string;
  size_bytes: number;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload video file');
  }
  return res.json();
}

export async function startProcessingJob(payload: {
  source_type: 'file' | 'rtsp';
  file_path?: string;
  rtsp_url?: string;
  frame_skip?: number;
  similarity_threshold?: number;
}): Promise<{ success: boolean; job_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/jobs/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start processing job');
  }
  return res.json();
}

export async function fetchJobStatus(): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/jobs/status`);
  if (!res.ok) throw new Error('Failed to fetch job status');
  return res.json();
}

export async function stopProcessingJob(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/jobs/stop`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to stop processing job');
  return res.json();
}

export async function fetchConfig(): Promise<ConfigSettings> {
  const res = await fetch(`${API_BASE}/config`);
  if (!res.ok) throw new Error('Failed to load configuration');
  return res.json();
}

export async function updateConfig(payload: {
  frame_skip?: number;
  confidence_threshold?: number;
  similarity_threshold?: number;
  track_lost_timeout_seconds?: number;
  blur_threshold?: number;
}): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update configuration');
  }
  return res.json();
}

export async function fetchTemporalAnalytics(): Promise<TemporalAnalytics> {
  const res = await fetch(`${API_BASE}/analytics/temporal`);
  if (!res.ok) throw new Error('Failed to load temporal analytics');
  return res.json();
}
