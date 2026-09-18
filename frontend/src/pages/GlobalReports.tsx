import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Exam } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { BarChart2, ArrowRight } from 'lucide-react';

export const GlobalReports = () => {
  const { data: exams, isLoading } = useQuery<Exam[]>({
    queryKey: ['exams'],
    queryFn: () => apiClient.get('/api/v1/exams'),
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Reports</h2>
          <p className="text-gray-500">View and export reports for all exams.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select an Exam to view Report</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading exams...</div>
          ) : !exams || exams.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No exams available.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Exam ID</TableHead>
                  <TableHead>Exam Name</TableHead>
                  <TableHead>Created At</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {exams.map(exam => (
                  <TableRow key={exam.id}>
                    <TableCell className="font-medium">#{exam.id}</TableCell>
                    <TableCell>{exam.name}</TableCell>
                    <TableCell>{new Date(exam.created_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      <Link to={`/exams/${exam.id}/report`}>
                        <Button variant="primary" size="sm">
                          <BarChart2 size={16} className="mr-2" />
                          View Report
                          <ArrowRight size={16} className="ml-2" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
