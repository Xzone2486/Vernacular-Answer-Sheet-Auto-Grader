import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Exam } from '../types';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { useToast } from '../components/ui/toast';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Plus, Search, Trash2, ArrowRight } from 'lucide-react';

export const ExamsList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [newExamName, setNewExamName] = useState('');
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<Exam[]>({
    queryKey: ['exams'],
    queryFn: () => apiClient.get('/api/v1/exams'),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => apiClient.post('/api/v1/exams', { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      setNewExamName('');
      toast('success', 'Exam created successfully');
    },
    onError: (err: any) => {
      toast('error', err.message || 'Failed to create exam');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v1/exams/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast('success', 'Exam deleted');
    },
    onError: (err: any) => {
      toast('error', err.message || 'Failed to delete exam');
    },
  });

  const filteredExams = data?.filter(exam => 
    exam.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Exams</h2>
          <p className="text-gray-500">Manage all assessment exams.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader className="pb-3 border-b border-gray-100 flex flex-row items-center justify-between">
            <CardTitle>All Exams</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search exams..."
                className="pl-9 h-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">Loading exams...</div>
            ) : filteredExams.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No exams found.</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredExams.map((exam) => (
                    <TableRow key={exam.id}>
                      <TableCell className="font-medium">#{exam.id}</TableCell>
                      <TableCell>{exam.name}</TableCell>
                      <TableCell>{new Date(exam.created_at).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right space-x-2">
                        <Link to={`/exams/${exam.id}`}>
                          <Button variant="outline" size="sm">
                            Manage <ArrowRight className="ml-2" size={14} />
                          </Button>
                        </Link>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => {
                            if (window.confirm('Are you sure you want to delete this exam?')) {
                              deleteMutation.mutate(exam.id);
                            }
                          }}
                        >
                          <Trash2 size={16} />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Create Exam</CardTitle>
          </CardHeader>
          <CardContent>
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                if (newExamName.trim()) createMutation.mutate(newExamName);
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <label className="text-sm font-medium">Exam Name</label>
                <Input 
                  placeholder="e.g. Midterm History" 
                  value={newExamName}
                  onChange={(e) => setNewExamName(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                <Plus size={16} className="mr-2" />
                {createMutation.isPending ? 'Creating...' : 'Create Exam'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
