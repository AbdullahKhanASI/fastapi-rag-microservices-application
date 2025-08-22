'use client';

import React, { useState, useCallback } from 'react';
import { Upload, X, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { chatApi } from '@/lib/api';
import { DocumentFile } from '@/types';

interface FileUploadProps {
  onFileUploaded: (file: DocumentFile) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileUploaded,
  isOpen,
  onClose,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Only PDF, TXT, and DOCX files are supported.');
      setIsUploading(false);
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size must be less than 10MB.');
      setIsUploading(false);
      return;
    }

    try {
      const result = await chatApi.uploadFile(file);
      setUploadSuccess(`File "${file.name}" uploaded successfully with ${result.chunks_count} chunks!`);
      onFileUploaded(result);
      
      // Auto-close after success
      setTimeout(() => {
        onClose();
        setUploadSuccess(null);
      }, 2000);
    } catch (error: any) {
      setUploadError(error.detail || 'Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-md w-full p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Upload Document
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            disabled={isUploading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div
          className={`
            border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200
            ${isDragging
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
            }
            ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            className="hidden"
            accept=".pdf,.txt,.docx"
            onChange={handleFileSelect}
            disabled={isUploading}
          />

          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Processing your document...
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className="w-8 h-8 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Drop your file here or click to browse
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  PDF, TXT, DOCX up to 10MB
                </p>
              </div>
            </div>
          )}
        </div>

        {uploadError && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-700 dark:text-red-300">{uploadError}</p>
            </div>
          </div>
        )}

        {uploadSuccess && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
              <p className="text-sm text-green-700 dark:text-green-300">{uploadSuccess}</p>
            </div>
          </div>
        )}

        <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-1 mb-1">
            <FileText className="w-3 h-3" />
            <span>Supported formats: PDF, TXT, DOCX</span>
          </div>
          <p>Your documents will be processed and indexed for AI-powered search.</p>
        </div>
      </div>
    </div>
  );
};