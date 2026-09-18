import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { AnswerSheet } from '../types';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ArrowLeft, Download } from 'lucide-react';
import { Badge } from '../components/ui/badge';

export const ExamReport = () => {
  const { id } = useParams<{ id: string }>();

  const { data: sheets, isLoading } = useQuery<{items: AnswerSheet[]}>({
    queryKey: ['answer-sheets', id],
    queryFn: () => apiClient.get(`/api/v1/answer-sheets`, { exam_id: id || '' }),
    enabled: !!id,
  });

  // Removed unused rows mapping

  const handleExportCSV = () => {
    if (!sheets?.items) return;
    
    const headers = ['Student ID', 'Answer Sheet ID', 'Upload Time'];
    const csvContent = [
      headers.join(','),
      ...sheets.items.map(s => 
        [s.student_id, s.id, new Date(s.upload_time).toLocaleString()].join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `exam_${id}_report.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading report...</div>;

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
            <h2 className="text-2xl font-bold tracking-tight">Exam Results Report</h2>
            <p className="text-gray-500">Overview of all graded answer sheets.</p>
          </div>
        </div>
        <Button onClick={handleExportCSV}>
          <Download size={16} className="mr-2" /> Export to CSV
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Student Results</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student ID</TableHead>
                <TableHead>Answer Sheet ID</TableHead>
                <TableHead>Upload Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sheets?.items.map((sheet) => (
                <TableRow key={sheet.id}>
                  <TableCell className="font-medium">{sheet.student_id}</TableCell>
                  <TableCell>#{sheet.id}</TableCell>
                  <TableCell>{new Date(sheet.upload_time).toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant={sheet.student_answers.length > 0 ? 'success' : 'warning'}>
                      {sheet.student_answers.length > 0 ? 'Processed' : 'Pending OCR'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
              {(!sheets?.items || sheets.items.length === 0) && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                    No answer sheets found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};
