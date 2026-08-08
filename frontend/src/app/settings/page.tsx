'use client';

import React, { useState, useEffect } from 'react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { Settings, Save, Trash2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { workspaces, activeWorkspaceId, updateWorkspace, deleteWorkspace, isLoading } = useWorkspaceStore();
  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (activeWorkspace) {
      setName(activeWorkspace.name);
      setDescription(activeWorkspace.description || '');
    }
  }, [activeWorkspace]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspaceId || !name.trim()) return;
    try {
      await updateWorkspace(activeWorkspaceId, name, description);
      toast.success('Workspace updated successfully');
    } catch (error) {
      toast.error('Failed to update workspace');
    }
  };

  const handleDelete = async () => {
    if (!activeWorkspaceId) return;
    if (workspaces.length <= 1) {
      toast.error('Cannot delete the last remaining workspace.');
      return;
    }
    
    if (window.confirm(`Are you sure you want to delete the workspace "${activeWorkspace?.name}"? This action cannot be undone and will delete all associated data.`)) {
      try {
        await deleteWorkspace(activeWorkspaceId);
        toast.success('Workspace deleted successfully');
      } catch (error) {
        toast.error('Failed to delete workspace');
      }
    }
  };

  if (!activeWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">System Settings</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Manage your workspace preferences, integrations, and data retention policies.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="space-y-4">
          {/* Navigation/Tabs could go here in the future */}
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-3 shadow-sm">
            <button className="w-full flex items-center px-3 py-2 text-sm font-semibold rounded-lg bg-[var(--brand-subtle)] text-[var(--brand)] transition-colors">
              <Settings className="w-4 h-4 mr-2" />
              Workspace Settings
            </button>
            <button className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text-primary)] transition-colors opacity-50 cursor-not-allowed" title="Coming soon">
              <ShieldCheck className="w-4 h-4 mr-2" />
              Security & API Keys
            </button>
          </div>
        </div>

        <div className="md:col-span-2 space-y-6">
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="p-5 border-b border-[var(--border)]">
              <h2 className="text-sm font-bold text-[var(--text-primary)]">General Settings</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Update your workspace details and basic configuration.
              </p>
            </div>
            
            <form onSubmit={handleSave} className="p-5 space-y-5">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wide">
                  Workspace Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[var(--surface-subtle)] text-sm text-[var(--text-primary)] px-3 py-2.5 rounded-lg border border-[var(--border)] focus:bg-[var(--surface)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)] transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wide">
                  Description <span className="text-[var(--text-muted)] font-normal">(Optional)</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full bg-[var(--surface-subtle)] text-sm text-[var(--text-primary)] px-3 py-2.5 rounded-lg border border-[var(--border)] focus:bg-[var(--surface)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)] transition-all resize-none"
                  placeholder="What is this workspace used for?"
                />
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isLoading || (name === activeWorkspace.name && description === (activeWorkspace.description || ''))}
                  className="px-5 py-2 bg-[var(--brand)] text-white text-xs font-semibold rounded-lg hover:bg-[var(--brand-hover)] transition-colors disabled:opacity-50 flex items-center"
                >
                  <Save className="w-3.5 h-3.5 mr-1.5" />
                  Save Changes
                </button>
              </div>
            </form>
          </div>

          <div className="bg-[var(--surface)] border border-red-200 dark:border-red-900/50 rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="p-5 border-b border-red-100 dark:border-red-900/30">
              <h2 className="text-sm font-bold text-red-600 dark:text-red-400 flex items-center">
                <AlertTriangle className="w-4 h-4 mr-1.5" />
                Danger Zone
              </h2>
            </div>
            <div className="p-5 bg-red-50/50 dark:bg-red-950/10">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-[var(--text-primary)]">Delete Workspace</h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">
                    Permanently delete this workspace and all of its data. This action cannot be reversed.
                  </p>
                </div>
                <button
                  onClick={handleDelete}
                  disabled={isLoading || workspaces.length <= 1}
                  className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 shrink-0 flex items-center justify-center"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                  Delete Workspace
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
