'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Search, Command, CheckCircle2, Moon, Sun, HelpCircle,
  ChevronRight, Plus, FolderSync, Menu, X,
} from 'lucide-react';
import { OnboardingWalkthrough } from '@/components/common/OnboardingWalkthrough';
import { useWorkspaceStore } from '@/store/workspaceStore';

interface TopbarProps {
  onMenuClick?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onMenuClick }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [showWorkspaceDropdown, setShowWorkspaceDropdown] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMobileSearch, setShowMobileSearch] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');

  const dropdownRef = useRef<HTMLDivElement>(null);

  const {
    workspaces, activeWorkspaceId, fetchWorkspaces,
    setActiveWorkspace, createWorkspace, isLoading,
  } = useWorkspaceStore();

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  // Close workspace dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowWorkspaceDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const activeWorkspace = workspaces.find(w => w.id === activeWorkspaceId);

  const toggleDarkMode = () => {
    const next = !isDarkMode;
    setIsDarkMode(next);
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', next);
    }
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkspaceName.trim()) return;
    try {
      await createWorkspace(newWorkspaceName);
      setNewWorkspaceName('');
      setShowCreateModal(false);
      setShowWorkspaceDropdown(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <>
      <header className="h-14 sm:h-16 bg-[var(--surface)] border-b border-[var(--border)] px-3 sm:px-6 lg:px-8 flex items-center gap-2 sm:gap-3 sticky top-0 z-20 select-none">

        {/* ── Hamburger — mobile only ──────────────────────────────── */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg hover:bg-[var(--surface-subtle)] text-[var(--text-secondary)] transition-colors shrink-0"
          aria-label="Open navigation"
        >
          <Menu className="w-4 h-4" />
        </button>

        {/* ── Left: breadcrumb + workspace selector ────────────────── */}
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] font-mono relative min-w-0" ref={dropdownRef}>
          <img src="/logo.png" alt="Logo" className="w-6 h-6 object-contain mr-1 sm:mr-2" />
          
          {/* "Workspace /" label — hidden on very small screens */}
          <span className="text-[var(--text-muted)] hidden sm:inline whitespace-nowrap">Workspace</span>
          <ChevronRight className="w-3 h-3 text-[var(--text-muted)] hidden sm:block shrink-0" />

          {/* Workspace Selector button */}
          <div className="relative flex items-center">
            <button
              onClick={() => setShowWorkspaceDropdown(!showWorkspaceDropdown)}
              className="text-[var(--brand)] font-bold flex items-center gap-1 hover:bg-[var(--surface-subtle)] px-2 py-1 rounded transition-colors max-w-[120px] sm:max-w-[180px] truncate"
              title={activeWorkspace?.name}
            >
              <span className="truncate">{activeWorkspace?.name || 'Loading…'}</span>
              <FolderSync className="w-3 h-3 shrink-0" />
            </button>

            {showWorkspaceDropdown && (
              <div className="absolute top-full left-0 mt-1 w-56 bg-[var(--surface)] border border-[var(--border)] rounded-lg shadow-lg overflow-hidden z-50">
                <div className="max-h-64 overflow-y-auto">
                  {workspaces.map(w => (
                    <button
                      key={w.id}
                      onClick={() => {
                        setActiveWorkspace(w.id);
                        setShowWorkspaceDropdown(false);
                      }}
                      className={`w-full text-left px-4 py-2.5 text-xs flex items-center hover:bg-[var(--surface-subtle)] transition-colors ${
                        w.id === activeWorkspaceId
                          ? 'bg-[var(--brand-subtle)] text-[var(--brand)] font-bold'
                          : 'text-[var(--text-primary)]'
                      }`}
                    >
                      <span className="truncate">{w.name}</span>
                      {w.id === activeWorkspaceId && (
                        <CheckCircle2 className="w-3.5 h-3.5 ml-auto shrink-0 text-[var(--brand)]" />
                      )}
                    </button>
                  ))}
                </div>
                <div className="border-t border-[var(--border)] p-1.5">
                  <button
                    onClick={() => {
                      setShowCreateModal(true);
                      setShowWorkspaceDropdown(false);
                    }}
                    className="w-full flex items-center justify-center text-xs text-[var(--brand)] font-semibold hover:bg-[var(--brand-subtle)] py-2 rounded transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5 mr-1" />
                    New Workspace
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Page label — md+ only */}
          <ChevronRight className="w-3 h-3 text-[var(--text-muted)] hidden md:block shrink-0" />
          <span className="text-[var(--text-primary)] font-semibold hidden md:inline whitespace-nowrap">
            Decision Dashboard
          </span>
        </div>

        {/* ── Center search — hidden on mobile, shown inline on sm+ ── */}
        <div className="hidden sm:flex items-center flex-1 mx-2 md:mx-4 max-w-xs lg:max-w-sm">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search suppliers, certs, evidence…"
              className="w-full bg-[var(--surface-subtle)] text-xs text-[var(--text-primary)] pl-9 pr-10 py-1.5 rounded-lg border border-[var(--border)] focus:bg-[var(--surface)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)] transition-all placeholder:text-[var(--text-muted)]"
            />
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 hidden lg:flex px-1.5 py-0.5 rounded bg-[var(--border)]/50 text-[10px] font-mono text-[var(--text-secondary)] items-center gap-0.5">
              <Command className="w-2.5 h-2.5" /> K
            </div>
          </div>
        </div>

        {/* ── Right controls ───────────────────────────────────────── */}
        <div className="flex items-center gap-1.5 sm:gap-2 ml-auto text-xs">

          {/* Mobile search toggle */}
          <button
            onClick={() => setShowMobileSearch(s => !s)}
            className="sm:hidden p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-subtle)] text-[var(--text-secondary)] transition-all"
            aria-label="Toggle search"
          >
            {showMobileSearch ? <X className="w-4 h-4" /> : <Search className="w-4 h-4" />}
          </button>

          {/* Help */}
          <button
            onClick={() => setShowHelpModal(true)}
            className="p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all flex items-center gap-1"
            title="Open Guided Tour & Glossary"
          >
            <HelpCircle className="w-4 h-4 text-[var(--brand)]" />
            <span className="hidden sm:inline font-semibold">Help</span>
          </button>

          {/* Dark mode */}
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-subtle)] text-[var(--text-secondary)] transition-all flex items-center gap-1.5"
            title="Toggle Dark Mode"
          >
            {isDarkMode ? (
              <>
                <Sun className="w-3.5 h-3.5 text-[var(--brand)]" />
                <span className="hidden sm:inline text-[11px] font-semibold text-[var(--text-primary)]">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                <span className="hidden sm:inline text-[11px] font-semibold text-[var(--text-primary)]">Dark</span>
              </>
            )}
          </button>

          {/* Connected badge — lg+ only */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--success-subtle)] text-[var(--success)] border border-[var(--success)]/30 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Connected</span>
          </div>
        </div>

        {/* Onboarding Tour */}
        {showHelpModal && (
          <OnboardingWalkthrough forceOpen={true} onClose={() => setShowHelpModal(false)} />
        )}
      </header>

      {/* ── Mobile search bar — drops below header ──────────────────── */}
      {showMobileSearch && (
        <div className="sm:hidden px-3 py-2 bg-[var(--surface)] border-b border-[var(--border)] sticky top-14 z-20">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              autoFocus
              type="text"
              placeholder="Search suppliers, certs, evidence…"
              className="w-full bg-[var(--surface-subtle)] text-xs text-[var(--text-primary)] pl-9 pr-4 py-2 rounded-lg border border-[var(--border)] focus:bg-[var(--surface)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)] transition-all placeholder:text-[var(--text-muted)]"
            />
          </div>
        </div>
      )}

      {/* ── Create Workspace Modal ───────────────────────────────────── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-[var(--border)]">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Create New Workspace</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                A workspace organizes your documents, suppliers, and decision scenarios.
              </p>
            </div>

            <form onSubmit={handleCreateWorkspace} className="p-5 space-y-4">
              <div>
                <label
                  htmlFor="workspace-name"
                  className="block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wide"
                >
                  Workspace Name <span className="text-[var(--danger)]">*</span>
                </label>
                <input
                  id="workspace-name"
                  type="text"
                  required
                  value={newWorkspaceName}
                  onChange={e => setNewWorkspaceName(e.target.value)}
                  placeholder="e.g. Project Alpha Q4"
                  className="w-full bg-[var(--surface-subtle)] text-sm text-[var(--text-primary)] px-3 py-2 rounded-lg border border-[var(--border)] focus:bg-[var(--surface)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)] transition-all placeholder:text-[var(--text-muted)]"
                  autoFocus
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowCreateModal(false); setNewWorkspaceName(''); }}
                  className="px-4 py-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newWorkspaceName.trim() || isLoading}
                  className="px-4 py-2 bg-[var(--brand)] text-white text-xs font-semibold rounded-lg hover:bg-[var(--brand-hover)] transition-colors disabled:opacity-50 flex items-center"
                >
                  {isLoading && (
                    <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  )}
                  Create Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
