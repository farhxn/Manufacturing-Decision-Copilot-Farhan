'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, AlertCircle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
      <div className="p-3 bg-[#FAEEEE] text-[#B54747] rounded-xl">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h2 className="text-xl font-bold text-[#17202B]">Page Not Found</h2>
      <p className="text-xs text-[#536170] max-w-sm">
        The decision workspace page you requested does not exist or has been moved.
      </p>
      <Link
        href="/dashboard"
        className="inline-flex items-center px-4 py-2 text-xs font-semibold bg-[#315E9B] text-white rounded-lg hover:bg-[#274F87] transition-all"
      >
        <ArrowLeft className="w-3.5 h-3.5 mr-2" />
        Return to Workspace Overview
      </Link>
    </div>
  );
}
