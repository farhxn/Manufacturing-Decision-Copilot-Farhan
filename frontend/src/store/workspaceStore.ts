import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { projectApi } from '@/services/api/projectApi';
import type { ProjectSummary } from '@/types';

interface WorkspaceState {
  workspaces: ProjectSummary[];
  activeWorkspaceId: string | null;
  isLoading: boolean;
  error: string | null;
  
  fetchWorkspaces: () => Promise<void>;
  setActiveWorkspace: (id: string) => void;
  createWorkspace: (name: string, description?: string) => Promise<ProjectSummary>;
  updateWorkspace: (id: string, name: string, description?: string) => Promise<ProjectSummary>;
  deleteWorkspace: (id: string) => Promise<void>;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      workspaces: [],
      activeWorkspaceId: null,
      isLoading: false,
      error: null,

      fetchWorkspaces: async () => {
        set({ isLoading: true, error: null });
        try {
          const workspaces = await projectApi.list();
          const { activeWorkspaceId } = get();
          
          let newActiveId = activeWorkspaceId;
          
          // If no active workspace or the active one was deleted, pick the first one
          if (!activeWorkspaceId || !workspaces.find(w => w.id === activeWorkspaceId)) {
            newActiveId = workspaces.length > 0 ? workspaces[0].id : null;
          }
          
          set({ workspaces, activeWorkspaceId: newActiveId, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch workspaces', isLoading: false });
        }
      },

      setActiveWorkspace: (id: string) => {
        set({ activeWorkspaceId: id });
      },

      createWorkspace: async (name: string, description?: string) => {
        set({ isLoading: true, error: null });
        try {
          const newWorkspace = await projectApi.create({ name, description });
          const { workspaces } = get();
          set({ 
            workspaces: [...workspaces, newWorkspace], 
            activeWorkspaceId: newWorkspace.id,
            isLoading: false 
          });
          return newWorkspace;
        } catch (error: any) {
          set({ error: error.message || 'Failed to create workspace', isLoading: false });
          throw error;
        }
      },

      updateWorkspace: async (id: string, name: string, description?: string) => {
        set({ isLoading: true, error: null });
        try {
          const updatedWorkspace = await projectApi.update(id, { name, description });
          const { workspaces } = get();
          set({
            workspaces: workspaces.map(w => w.id === id ? updatedWorkspace : w),
            isLoading: false
          });
          return updatedWorkspace;
        } catch (error: any) {
          set({ error: error.message || 'Failed to update workspace', isLoading: false });
          throw error;
        }
      },

      deleteWorkspace: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          await projectApi.delete(id);
          const { workspaces, activeWorkspaceId } = get();
          const newWorkspaces = workspaces.filter(w => w.id !== id);
          
          let newActiveId = activeWorkspaceId;
          if (activeWorkspaceId === id) {
            newActiveId = newWorkspaces.length > 0 ? newWorkspaces[0].id : null;
          }
          
          set({
            workspaces: newWorkspaces,
            activeWorkspaceId: newActiveId,
            isLoading: false
          });
        } catch (error: any) {
          set({ error: error.message || 'Failed to delete workspace', isLoading: false });
          throw error;
        }
      }
    }),
    {
      name: 'workspace-storage',
      // Only persist activeWorkspaceId, not the fetched workspaces
      partialize: (state) => ({ activeWorkspaceId: state.activeWorkspaceId }),
    }
  )
);

export const getActiveWorkspaceId = () => {
  return useWorkspaceStore.getState().activeWorkspaceId || '00000000-0000-4000-a000-000000000002';
};
