import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { AnswerSheet, Score } from '../types';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { useToast } from '../components/ui/toast';
import { ArrowLeft, ChevronLeft, ChevronRight, Save, AlertTriangle } from 'lucide-react';

export const GradingReview = () => {
  const { id } = useParams<{ id: string }>();
  const [currentSheetIndex, setCurrentSheetIndex] = useState(0);
  const [overrideScore, setOverrideScore] = useState<string>('');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch all answer sheets for this exam
  const { data: sheets, isLoading } = useQuery<{items: AnswerSheet[]}>({
    queryKey: ['answer-sheets', id],
    queryFn: () => apiClient.get(`/api/v1/answer-sheets`, { exam_id: id || '' }),
    enabled: !!id,
  });

  // We are assuming one question per sheet for simplicity in this MVP flow,
  // or we just show the first student answer.
  const currentSheet = sheets?.items?.[currentSheetIndex];
  const currentAnswer = currentSheet?.student_answers?.[0];

  // Fetch score for current answer
  const { data: score } = useQuery<Score>({
    queryKey: ['score', currentAnswer?.id],
    queryFn: () => apiClient.get(`/api/v1/student-answers/${currentAnswer?.id}/score`),
    enabled: !!currentAnswer?.id,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      // Stub for updating score: PUT /api/v1/scores/{score_id} (Assuming this endpoint exists)
      // If it doesn't, we'd need to add it to the backend. Let's assume the user can update the score via an endpoint.
      if (!score?.id) throw new Error("No score found to update");
      return apiClient.put(`/api/v1/scores/${score.id}`, {
        final_score: parseFloat(overrideScore),
        override_reason: overrideReason
      });
    },
    onSuccess: () => {
      toast('success', 'Score updated successfully');
      queryClient.invalidateQueries({ queryKey: ['score', currentAnswer?.id] });
      setOverrideScore('');
      setOverrideReason('');
    },
    onError: (err: any) => {
      toast('error', `Failed to update score: ${err.message}`);
    }
  });

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading answers...</div>;
  if (!sheets?.items || sheets.items.length === 0) return <div className="p-8 text-center">No answer sheets found for this exam.</div>;

  const handleNext = () => {
    if (currentSheetIndex < sheets.items.length - 1) setCurrentSheetIndex(prev => prev + 1);
  };

  const handlePrev = () => {
    if (currentSheetIndex > 0) setCurrentSheetIndex(prev => prev - 1);
  };

  const handleSave = () => {
    if (overrideScore && !overrideReason) {
      toast('error', 'You must provide a reason when overriding a score.');
      return;
    }
    saveMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to={`/exams/${id}`}>
            <Button variant="ghost" size="sm" className="px-2">
              <ArrowLeft size={18} />
            </Button>
          </Link>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Grading Review</h2>
            <p className="text-gray-500">Review OCR and semantic scoring results.</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-500">
            Student {currentSheetIndex + 1} of {sheets.items.length} (ID: {currentSheet?.student_id})
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handlePrev} disabled={currentSheetIndex === 0}>
              <ChevronLeft size={18} className="mr-1" /> Prev
            </Button>
            <Button variant="outline" size="sm" onClick={handleNext} disabled={currentSheetIndex === sheets.items.length - 1}>
              Next <ChevronRight size={18} className="ml-1" />
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[700px]">
        {/* Left Pane: Image viewer */}
        <Card className="flex flex-col h-full overflow-hidden">
          <CardHeader className="py-4 border-b border-gray-100 bg-gray-50">
            <CardTitle className="text-base">Original Scanned Image</CardTitle>
          </CardHeader>
          <div className="flex-1 bg-gray-200 overflow-auto flex items-center justify-center p-4">
            {currentSheet?.image_path ? (
              <img 
                src={apiClient.uploadUrl(currentSheet.image_path)} 
                alt="Student Answer" 
                className="max-w-full max-h-full object-contain shadow-sm bg-white"
              />
            ) : (
              <span className="text-gray-400">No image available</span>
            )}
          </div>
        </Card>

        {/* Right Pane: OCR & Scoring Data */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-2">
          <Card>
            <CardHeader className="py-4 border-b border-gray-100 flex flex-row items-center justify-between">
              <CardTitle className="text-base">Extracted Text</CardTitle>
              {currentAnswer?.ocr_confidence != null && (
                <Badge variant={currentAnswer.ocr_confidence > 0.8 ? 'success' : 'warning'}>
                  {Math.round(currentAnswer.ocr_confidence * 100)}% Confidence
                </Badge>
              )}
            </CardHeader>
            <CardContent className="py-4">
              <p className="text-gray-800 font-serif whitespace-pre-wrap leading-relaxed">
                {currentAnswer?.ocr_text || <span className="text-gray-400 italic">No text extracted.</span>}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-4 border-b border-gray-100 bg-gray-50 flex flex-row items-center justify-between">
              <CardTitle className="text-base">Auto-Scoring Results</CardTitle>
              {score?.similarity_score != null && (
                <Badge variant={score.similarity_score > 0.7 ? 'success' : 'destructive'}>
                  {Math.round(score.similarity_score * 100)}% Match
                </Badge>
              )}
            </CardHeader>
            <CardContent className="py-4 space-y-4">
              {score ? (
                <>
                  <div className="flex items-center justify-between p-4 rounded-lg bg-blue-50 border border-blue-100">
                    <div>
                      <p className="text-sm text-blue-600 font-semibold uppercase tracking-wider">Awarded Marks</p>
                      <p className="text-3xl font-bold text-blue-900">
                        {score.final_score !== null ? score.final_score : score.auto_score}
                        <span className="text-lg text-blue-500 font-normal"> / max</span>
                      </p>
                    </div>
                    {score.final_score !== null && (
                      <Badge variant="warning">Manually Overridden</Badge>
                    )}
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-1">AI Explanation</h4>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md border border-gray-200">
                      {score.explanation || 'No explanation provided.'}
                    </p>
                  </div>
                </>
              ) : (
                <div className="text-center p-4 text-gray-500">
                  <AlertTriangle className="mx-auto mb-2 text-yellow-500" size={24} />
                  <p>Not scored yet.</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-4 border-b border-gray-100">
              <CardTitle className="text-base">Override Score</CardTitle>
            </CardHeader>
            <CardContent className="py-4 space-y-4">
              <div className="flex gap-4">
                <div className="w-1/3">
                  <label className="text-sm font-medium text-gray-700">New Score</label>
                  <Input 
                    type="number" 
                    step="0.5" 
                    placeholder="e.g. 8.5"
                    value={overrideScore}
                    onChange={(e) => setOverrideScore(e.target.value)}
                  />
                </div>
                <div className="w-2/3">
                  <label className="text-sm font-medium text-gray-700">Override Reason (Required)</label>
                  <Input 
                    placeholder="Why are you changing this score?"
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                  />
                </div>
              </div>
              <Button 
                onClick={handleSave} 
                className="w-full"
                disabled={!overrideScore || saveMutation.isPending}
              >
                <Save className="mr-2" size={16} />
                {saveMutation.isPending ? 'Saving...' : 'Save Override'}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
