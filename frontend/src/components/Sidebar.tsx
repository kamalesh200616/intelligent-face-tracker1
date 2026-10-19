import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  Camera,
  ClipboardList,
  Users,
  Activity,
  Settings,
  ShieldCheck,
  Cpu,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  isJobRunning: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isJobRunning,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload Video', icon: UploadCloud },
    { id: 'live', label: 'Live Camera', icon: Camera },
    { id: 'events', label: 'Visitor Events', icon: ClipboardList },
    { id: 'identities', label: 'Registered Identities', icon: Users },
    { id: 'history', label: 'Processing History', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-screen border-r border-slate-800 shadow-xl select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-bold text-base text-white tracking-tight leading-tight">
            Intelligent Face Tracker
          </h1>
          <span className="text-xs text-indigo-400 font-medium">
            AI Vision & Visitor Analytics
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span className="flex-1 text-left">{item.label}</span>
              {item.id === 'upload' && isJobRunning && (
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Subsystem Status Card */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/70 rounded-xl p-3 border border-slate-700/60 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> AI Pipeline
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Online
            </span>
          </div>
          <div className="text-[11px] text-slate-400 leading-relaxed">
            <span className="font-semibold text-slate-300">Models:</span> YOLOv8-face + ArcFace
          </div>
          <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-700/50">
            Katomaran Hackathon v1.0.0
          </div>
        </div>
      </div>
    </aside>
  );
};
