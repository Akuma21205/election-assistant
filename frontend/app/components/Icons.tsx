"use client";

export const BotIcon = () => (
  <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
    <rect width="32" height="32" rx="8" fill="url(#botGrad)" />
    <path d="M10 20c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <circle cx="12.5" cy="13.5" r="1.5" fill="white" />
    <circle cx="19.5" cy="13.5" r="1.5" fill="white" />
    <path d="M16 8v2M13 8.5l1 1.732M19 8.5l-1 1.732" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
    <defs>
      <linearGradient id="botGrad" x1="0" y1="0" x2="32" y2="32">
        <stop stopColor="#6366f1" />
        <stop offset="1" stopColor="#8b5cf6" />
      </linearGradient>
    </defs>
  </svg>
);

export const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
    <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const HistoryIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <path d="M12 8v4l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <path d="M3.05 11a9 9 0 1 0 .5-3M3 4v4h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const MicIcon = ({ active }: { active?: boolean }) => (
  <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
    <rect x="9" y="2" width="6" height="12" rx="3" stroke={active ? "#ef4444" : "currentColor"} strokeWidth="2" />
    <path d="M5 10a7 7 0 0014 0" stroke={active ? "#ef4444" : "currentColor"} strokeWidth="2" strokeLinecap="round" />
    <path d="M12 17v4M8 21h8" stroke={active ? "#ef4444" : "currentColor"} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const GlobeIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" />
    <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" stroke="currentColor" strokeWidth="1.5" />
  </svg>
);

export const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <path d="M12 2l2.09 6.26L20 10l-5.91 1.74L12 18l-2.09-6.26L4 10l5.91-1.74L12 2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
  </svg>
);

export const CheckIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
    <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" />
  </svg>
);

export const CalendarIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
    <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const UserIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.5" />
    <path d="M4 21v-1a6 6 0 0112 0v1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const SettingsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const SpeakerIcon = ({ active }: { active?: boolean }) => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <path d="M11 5L6 9H2v6h4l5 4V5z" stroke={active ? "#8b5cf6" : "currentColor"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill={active ? "rgba(139,92,246,0.15)" : "none"} />
    <path d="M15.54 8.46a5 5 0 010 7.07" stroke={active ? "#8b5cf6" : "currentColor"} strokeWidth="1.8" strokeLinecap="round" />
    <path d="M19.07 4.93a10 10 0 010 14.14" stroke={active ? "#8b5cf6" : "currentColor"} strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export const SpeakerOffIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M23 9l-6 6M17 9l6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export const StopCircleIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8" />
    <rect x="9" y="9" width="6" height="6" rx="1" fill="currentColor" />
  </svg>
);
