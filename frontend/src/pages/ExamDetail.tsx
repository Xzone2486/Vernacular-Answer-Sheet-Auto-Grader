import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { ExamDetail as ExamDetailType } from '../types';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { ArrowLeft, BookOpen, UploadCloud, CheckCircle } from 'lucide-react';
import { BatchUpload } from './BatchUpload';

export const ExamDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'questions' | 'uploads' | 'results'>('uploads');

  const { data: exam, isLoading } = useQuery<ExamDetailType>({
    queryKey: ['exam', id],
    queryFn: () => apiClient.get(`/api/v1/exams/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading exam details...</div>;
  if (!exam) return <div className="p-8 text-center text-red-500">Exam not found.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/">
          <Button variant="ghost" size="sm" className="px-2">
            <ArrowLeft size={18} />
          </Button>
        </Link>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{exam.name}</h2>
          <p className="text-gray-500">Manage questions and upload answer sheets.</p>
        </div>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('questions')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'questions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BookOpen size={18} /> Questions
          </button>
          <button
            onClick={() => setActiveTab('uploads')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'uploads'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <UploadCloud size={18} /> Batch Upload
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'results'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CheckCircle size={18} /> Review & Results
          </button>
        </nav>
      </div>

      <div className="mt-6">
        {activeTab === 'questions' && (
          <Card className="p-6 text-center text-gray-500">
            {/* We'll implement Questions Manager here if time permits. For now it's stubbed out. */}
            Questions Manager (Placeholder)
          </Card>
        )}
        
        {activeTab === 'uploads' && <BatchUpload examId={exam.id} />}
        
        {activeTab === 'results' && (
          <div className="text-center p-8 bg-white rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to grade?</h3>
            <p className="text-gray-500 mb-6">Review the auto-scored answers and override if necessary.</p>
            <Link to={`/exams/${exam.id}/review`}>
              <Button size="lg">Start Grading Session</Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
