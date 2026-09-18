import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { JobStatusResponse } from '../types';
import { Card, CardContent } from '../components/ui/card';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Badge } from '../components/ui/badge';

interface JobProgressProps {
  jobId: string;
  onComplete?: () => void;
}

export const JobProgress: React.FC<JobProgressProps> = ({ jobId, onComplete }) => {
  const { data: job, isError } = useQuery<JobStatusResponse>({
    queryKey: ['job', jobId],
    queryFn: () => apiClient.get(`/api/v1/jobs/${jobId}`),
    refetchInterval: (query) => {
      // Stop polling if completed or failed
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 1500; // poll every 1.5s
    },
  });

  useEffect(() => {
    if (job?.status === 'completed' && onComplete) {
      onComplete();
    }
  }, [job?.status, onComplete]);

  if (isError) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-6 flex items-center gap-3 text-red-700">
          <AlertCircle size={24} />
          <div>
            <h3 className="font-semibold">Error checking job status</h3>
            <p className="text-sm opacity-80">Could not retrieve job progress.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!job) return null;

  const percentage = job.total > 0 ? Math.round((job.processed / job.total) * 100) : 0;
  
  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {job.status === 'running' || job.status === 'pending' ? (
              <Loader2 className="animate-spin text-blue-500" size={24} />
            ) : job.status === 'completed' ? (
              <CheckCircle className="text-green-500" size={24} />
            ) : (
              <AlertCircle className="text-red-500" size={24} />
            )}
            <div>
              <h3 className="font-medium text-gray-900">{job.description}</h3>
              <p className="text-sm text-gray-500">
                {job.status === 'pending' && 'Queued...'}
                {job.status === 'running' && `Processing ${job.processed} of ${job.total}`}
                {job.status === 'completed' && 'Completed successfully'}
                {job.status === 'failed' && `Failed: ${job.error}`}
              </p>
            </div>
          </div>
          <Badge 
            variant={
              job.status === 'completed' ? 'success' : 
              job.status === 'failed' ? 'destructive' : 
              'default'
            }
          >
            {job.status.toUpperCase()}
          </Badge>
        </div>

        {/* Progress bar */}
        <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${
              job.status === 'failed' ? 'bg-red-500' : 'bg-blue-600'
            }`}
            style={{ width: `${job.status === 'completed' ? 100 : percentage}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
};
