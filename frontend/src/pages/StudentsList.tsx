import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { useToast } from '../components/ui/toast';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Plus, Search, Trash2, Edit2, X } from 'lucide-react';

interface Student {
  id: number;
  name: string;
  roll_no: string;
  created_at: string;
}

interface PaginatedStudents {
  items: Student[];
  total: number;
  limit: number;
  offset: number;
}

export const StudentsList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [newStudentName, setNewStudentName] = useState('');
  const [newStudentRoll, setNewStudentRoll] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<PaginatedStudents>({
    queryKey: ['students'],
    queryFn: () => apiClient.get('/api/v1/students?limit=1000'),
  });

  const createMutation = useMutation({
    mutationFn: (student: { name: string; roll_no: string }) => apiClient.post('/api/v1/students', student),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setNewStudentName('');
      setNewStudentRoll('');
      toast('success', 'Student created successfully');
    },
    onError: (err: any) => {
      toast('error', err.message || 'Failed to create student');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number; name: string; roll_no: string }) => 
      apiClient.put(`/api/v1/students/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setEditingId(null);
      toast('success', 'Student updated successfully');
    },
    onError: (err: any) => {
      toast('error', err.message || 'Failed to update student');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v1/students/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      toast('success', 'Student deleted');
    },
    onError: (err: any) => {
      toast('error', err.message || 'Failed to delete student');
    },
  });

  const filteredStudents = data?.items.filter(student => 
    student.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    student.roll_no.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Students</h2>
          <p className="text-gray-500">Manage all registered students.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader className="pb-3 border-b border-gray-100 flex flex-row items-center justify-between">
            <CardTitle>All Students</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search students..."
                className="pl-9 h-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">Loading students...</div>
            ) : filteredStudents.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No students found.</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Roll No</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStudents.map((student) => (
                    <TableRow key={student.id}>
                      <TableCell className="font-medium">#{student.id}</TableCell>
                      <TableCell>
                        {editingId === student.id ? (
                          <Input 
                            defaultValue={student.roll_no} 
                            id={`roll-${student.id}`} 
                            className="h-8 w-24"
                          />
                        ) : student.roll_no}
                      </TableCell>
                      <TableCell>
                        {editingId === student.id ? (
                          <Input 
                            defaultValue={student.name} 
                            id={`name-${student.id}`} 
                            className="h-8"
                          />
                        ) : student.name}
                      </TableCell>
                      <TableCell>{new Date(student.created_at).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right space-x-2">
                        {editingId === student.id ? (
                          <>
                            <Button 
                              variant="primary" 
                              size="sm" 
                              onClick={() => {
                                const roll = (document.getElementById(`roll-${student.id}`) as HTMLInputElement).value;
                                const name = (document.getElementById(`name-${student.id}`) as HTMLInputElement).value;
                                updateMutation.mutate({ id: student.id, name, roll_no: roll });
                              }}
                            >
                              Save
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => setEditingId(null)}>
                              <X size={16} />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button variant="outline" size="sm" onClick={() => setEditingId(student.id)}>
                              <Edit2 size={14} />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              onClick={() => {
                                if (window.confirm('Delete this student?')) {
                                  deleteMutation.mutate(student.id);
                                }
                              }}
                            >
                              <Trash2 size={16} />
                            </Button>
                          </>
                        )}
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
            <CardTitle>Add Student</CardTitle>
          </CardHeader>
          <CardContent>
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                if (newStudentName.trim() && newStudentRoll.trim()) {
                  createMutation.mutate({ name: newStudentName, roll_no: newStudentRoll });
                }
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <label className="text-sm font-medium">Roll No</label>
                <Input 
                  placeholder="e.g. 101" 
                  value={newStudentRoll}
                  onChange={(e) => setNewStudentRoll(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Student Name</label>
                <Input 
                  placeholder="e.g. Rahul Kumar" 
                  value={newStudentName}
                  onChange={(e) => setNewStudentName(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                <Plus size={16} className="mr-2" />
                {createMutation.isPending ? 'Adding...' : 'Add Student'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
