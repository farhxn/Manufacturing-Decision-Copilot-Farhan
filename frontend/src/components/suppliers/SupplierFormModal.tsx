import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import type { SupplierCreateRequest, SupplierSummary } from '@/types';

interface SupplierFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: SupplierCreateRequest) => Promise<void>;
  initialData?: SupplierSummary;
  isEditing?: boolean;
}

export function SupplierFormModal({ isOpen, onClose, onSubmit, initialData, isEditing = false }: SupplierFormModalProps) {
  const [formData, setFormData] = useState<SupplierCreateRequest>({
    name: '',
    country: '',
    city: '',
    status: 'Active',
    unit_price: 0,
    landed_cost: 0,
    currency: 'USD',
    lead_time_days: 0,
    moq: 0,
    risk_level: 'Medium',
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && initialData && isEditing) {
      setFormData({
        name: initialData.name,
        country: initialData.country,
        city: initialData.city,
        status: initialData.status,
        unit_price: initialData.unit_price,
        landed_cost: initialData.landed_cost,
        currency: initialData.currency,
        lead_time_days: initialData.lead_time_days,
        moq: initialData.moq,
        risk_level: initialData.risk_level,
      });
    } else if (isOpen && !isEditing) {
      setFormData({
        name: '',
        country: '',
        city: '',
        status: 'Active',
        unit_price: 0,
        landed_cost: 0,
        currency: 'USD',
        lead_time_days: 0,
        moq: 0,
        risk_level: 'Medium',
      });
    }
  }, [isOpen, initialData, isEditing]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit(formData);
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred while saving the supplier.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    let parsedValue: any = value;
    if (type === 'number') {
      parsedValue = parseFloat(value);
      if (isNaN(parsedValue)) parsedValue = 0;
    }

    setFormData(prev => ({
      ...prev,
      [name]: parsedValue
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-[var(--surface)] w-full max-w-2xl rounded-2xl shadow-[var(--shadow-modal)] border border-[var(--border)] overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)] bg-[var(--surface-subtle)]/50">
          <h2 className="text-lg font-bold text-[var(--text-primary)]">
            {isEditing ? 'Edit Supplier' : 'New Supplier'}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto custom-scrollbar">
          {error && (
            <div className="mb-4 p-3 bg-[var(--danger-subtle)] text-[var(--danger)] text-sm rounded-lg border border-[var(--danger-border)]">
              {error}
            </div>
          )}
          
          <form id="supplier-form" onSubmit={handleSubmit} className="space-y-4">
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Supplier Name *</label>
                <input
                  required
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                  placeholder="Acme Corp"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                  <option value="Pending Review">Pending Review</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Country *</label>
                <input
                  required
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                  placeholder="USA"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">City</label>
                <input
                  type="text"
                  name="city"
                  value={formData.city || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                  placeholder="New York"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Unit Price *</label>
                <input
                  required
                  type="number"
                  name="unit_price"
                  min="0"
                  step="0.01"
                  value={formData.unit_price}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Landed Cost *</label>
                <input
                  required
                  type="number"
                  name="landed_cost"
                  min="0"
                  step="0.01"
                  value={formData.landed_cost}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Currency</label>
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Lead Time (Days) *</label>
                <input
                  required
                  type="number"
                  name="lead_time_days"
                  min="0"
                  value={formData.lead_time_days}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">MOQ *</label>
                <input
                  required
                  type="number"
                  name="moq"
                  min="0"
                  value={formData.moq}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[var(--text-secondary)]">Risk Level</label>
                <select
                  name="risk_level"
                  value={formData.risk_level}
                  onChange={handleChange}
                  className="w-full px-3 py-2 text-sm bg-[var(--surface-subtle)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand)]"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
            </div>

          </form>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[var(--border)] flex justify-end gap-3 bg-[var(--surface-subtle)]/50">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-semibold rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface)] border border-transparent hover:border-[var(--border)] transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="supplier-form"
            disabled={loading}
            className="px-4 py-2 text-sm font-semibold rounded-lg bg-[var(--brand)] text-white hover:bg-[var(--brand-dark)] transition-all shadow-[var(--shadow-button)] disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Supplier'}
          </button>
        </div>
      </div>
    </div>
  );
}
