'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';
import UploadZone from '@/components/business/UploadZone';

export default function UploadPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold text-slate-900">
              Upload PDF for Conversion
            </h1>
            <p className="text-slate-600">
              Upload your PDF file to convert it to EPUB format with AI-powered layout analysis
            </p>
          </div>

          {/* Upload Zone */}
          <div className="flex justify-center">
            <UploadZone />
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="text-center">
              <div className="text-2xl mb-2">📊</div>
              <h3 className="font-semibold mb-1">Table Detection</h3>
              <p className="text-sm text-slate-600">
                AI identifies and preserves complex table structures
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2">🖼️</div>
              <h3 className="font-semibold mb-1">Image Extraction</h3>
              <p className="text-sm text-slate-600">
                Automatically extracts and positions images correctly
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2">📖</div>
              <h3 className="font-semibold mb-1">Structure Recognition</h3>
              <p className="text-sm text-slate-600">
                Detects chapters, headings, and document hierarchy
              </p>
            </div>
          </div>

          {/* Help Text */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-8">
            <h3 className="font-semibold text-blue-900 mb-2">Tips for best results:</h3>
            <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
              <li>Use high-quality PDF files with clear text</li>
              <li>Ensure images are embedded (not scanned as one large image)</li>
              <li>Complex academic papers and technical documents work best</li>
              <li>Free tier supports files up to 50MB</li>
            </ul>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
