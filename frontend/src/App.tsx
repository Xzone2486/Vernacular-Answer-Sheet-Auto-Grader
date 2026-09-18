import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components/ui/toast';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { ExamsList } from './pages/ExamsList';
import { ExamDetail } from './pages/ExamDetail';
import { GradingReview } from './pages/GradingReview';

import { StudentsList } from './pages/StudentsList';
import { GlobalReports } from './pages/GlobalReports';
import { ExamReport } from './pages/ExamReport';

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route element={<AppLayout />}>
              <Route path="/" element={<ExamsList />} />
              <Route path="/exams/:id" element={<ExamDetail />} />
              <Route path="/exams/:id/review" element={<GradingReview />} />
              <Route path="/exams/:id/report" element={<ExamReport />} />
              <Route path="/students" element={<StudentsList />} />
              <Route path="/reports" element={<GlobalReports />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
