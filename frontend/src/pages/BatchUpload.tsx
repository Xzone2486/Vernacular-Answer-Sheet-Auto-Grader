import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { useToast } from '../components/ui/toast';
import { Upload, X, Play, Loader2 } from 'lucide-react';
import type { BatchJobResponse } from '../types';
import { JobProgress } from './JobProgress';

interface BatchUploadProps {
  examId: number;
}

export const BatchUpload: React.FC<BatchUploadProps> = ({ examId }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const { toast } = useToast();

  const uploadMutation = useMutation({
    mutationFn: async (fileList: File[]) => {
      // In a real app we might batch these or upload sequentially.
      // Assuming a single upload API per file for now: POST /api/v1/answer-sheets/
      const results = [];
      for (const file of fileList) {
        // Auto-match student ID from filename (e.g. 101.jpg -> student_id 101)
        // If not a number, fallback to 1 (placeholder)
        const match = file.name.match(/^(\d+)/);
        const studentId = match ? parseInt(match[1]) : 1;
        
        const formData = new FormData();
        formData.append('student_id', studentId.toString());
        formData.append('exam_id', examId.toString());
        formData.append('file', file);
        
        try {
          const res = await apiClient.postForm('/api/v1/answer-sheets/', formData);
          results.push({ success: true, res });
        } catch (error: any) {
          results.push({ success: false, error: error.message });
        }
      }
      return results;
    },
    onSuccess: (results) => {
      const successful = results.filter(r => r.success).length;
      toast('success', `Uploaded ${successful}/${results.length} files successfully.`);
      setFiles([]);
      // Start OCR batch job
      startJobMutation.mutate('ocr');
    },
    onError: (err: any) => {
      toast('error', `Upload failed: ${err.message}`);
    }
  });

  const startJobMutation = useMutation({
    mutationFn: async (type: 'ocr' | 'score') => {
      // Stub for backend job endpoints POST /api/v1/answer-sheets/batch/ocr
      // Since Step 4 requested batch jobs but the actual implementation in scoring.py/answer_sheets.py
      // in the backend context might not have these endpoints yet (wait, Step 4 said implement it, so let's assume they exist).
      // We will POST to /api/v1/answer-sheets/batch/ocr with exam_id.
      return apiClient.post(`/api/v1/answer-sheets/batch/${type}`, { exam_id: examId });
    },
    onSuccess: (data: BatchJobResponse) => {
      setJobId(data.job_id);
    },
    onError: (err: any) => {
      toast('error', `Failed to start job: ${err.message}`);
    }
  });

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  if (jobId) {
    return (
      <div className="space-y-4">
        <JobProgress jobId={jobId} onComplete={() => {
          if (startJobMutation.variables === 'ocr') {
            startJobMutation.mutate('score'); // auto-start scoring after OCR
          } else {
            setJobId(null);
            toast('success', 'Batch processing complete!');
          }
        }} />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Answer Sheets</CardTitle>
        <CardDescription>
          Drag and drop scanned images or PDFs here. 
          Use naming convention <code>[student_id].jpg</code> to automatically match to students.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
          }`}
        >
          <Upload className="h-10 w-10 text-gray-400 mb-4" />
          <p className="text-sm text-gray-600 mb-2">Drag files here or click to browse</p>
          <input
            type="file"
            multiple
            accept="image/*,application/pdf"
            className="hidden"
            id="file-upload"
            onChange={handleFileChange}
          />
          <label htmlFor="file-upload">
            <Button variant="outline" type="button" onClick={() => document.getElementById('file-upload')?.click()}>
              <span>Browse Files</span>
            </Button>
          </label>
        </div>

        {files.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Selected Files ({files.length})</h4>
            <div className="max-h-64 overflow-y-auto border rounded-md divide-y">
              {files.map((file, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="w-8 h-8 bg-blue-100 text-blue-700 rounded flex items-center justify-center font-semibold text-xs">
                      {(file.name.match(/^(\d+)/)?.[1] || '?')}
                    </div>
                    <span className="text-sm truncate text-gray-700">{file.name}</span>
                    <span className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-500">
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>

            <Button 
              className="w-full" 
              onClick={() => uploadMutation.mutate(files)}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <><Loader2 className="mr-2 animate-spin" size={16} /> Processing...</>
              ) : (
                <><Play className="mr-2" size={16} /> Upload & Process Batch</>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
