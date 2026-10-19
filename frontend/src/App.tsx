import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { LiveCameraPage } from './pages/LiveCameraPage';
import { EventsPage } from './pages/EventsPage';
import { IdentitiesPage } from './pages/IdentitiesPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { JobStatus } from './types';
import { fetchJobStatus, stopProcessingJob } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [jobStatus, setJobStatus] = useState<JobStatus | undefined>(undefined);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const pollStatus = async () => {
    try {
      const status = await fetchJobStatus();
      setJobStatus(status);
    } catch (e) {
      // Ignore background network errors
    }
  };

  useEffect(() => {
    pollStatus();
    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsLoading(true);
    await pollStatus();
    // Brief visual delay for spinner
    setTimeout(() => setIsLoading(false), 500);
  };

  const handleStopJob = async () => {
    try {
      await stopProcessingJob();
      await pollStatus();
    } catch (err: any) {
      alert(err.message || 'Failed to stop job');
    }
  };

  const getPageInfo = () => {
    switch (currentTab) {
      case 'dashboard':
        return {
          title: 'Analytics Dashboard',
          subtitle: 'Real-time overview of visitor volume, unique identities, and recent detections',
        };
      case 'upload':
        return {
          title: 'Video Upload & Processing',
          subtitle: 'Ingest and process local MP4/AVI videos with YOLOv8-face and ArcFace',
        };
      case 'live':
        return {
          title: 'Live Camera Feed',
          subtitle: 'Stream, detect, and track from IP security cameras with reconnect resilience',
        };
      case 'events':
        return {
          title: 'Visitor Audit Events',
          subtitle: 'Complete chronological audit log of confirmed Entry and Exit events with face crops',
        };
      case 'identities':
        return {
          title: 'Registered Identities Directory',
          subtitle: 'Unique visitors enrolled into database with persistent biometric representations',
        };
      case 'history':
        return {
          title: 'Processing Run History',
          subtitle: 'Audit log of previous video processing jobs, execution times, and metrics',
        };
      case 'settings':
        return {
          title: 'Pipeline Configuration',
          subtitle: 'Adjust detection skip intervals, recognition thresholds, and tracking timeouts',
        };
      default:
        return { title: 'Intelligent Face Tracker', subtitle: 'AI Computer Vision' };
    }
  };

  const pageInfo = getPageInfo();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
      {/* Dark Navy Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        isJobRunning={jobStatus?.status === 'running'}
      />

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header */}
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          jobStatus={jobStatus}
          onRefresh={handleRefresh}
          onStopJob={handleStopJob}
          isLoading={isLoading}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-8">
          {currentTab === 'dashboard' && <DashboardPage onNavigate={setCurrentTab} />}
          {currentTab === 'upload' && <UploadPage onNavigate={setCurrentTab} />}
          {currentTab === 'live' && <LiveCameraPage />}
          {currentTab === 'events' && <EventsPage />}
          {currentTab === 'identities' && <IdentitiesPage />}
          {currentTab === 'history' && <HistoryPage />}
          {currentTab === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
