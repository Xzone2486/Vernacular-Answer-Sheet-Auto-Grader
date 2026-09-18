import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components/ui/toast';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { ExamsList } from './pages/ExamsList';
import { ExamDetail } from './pages/ExamDetail';
import { GradingReview } from './pages/GradingReview';

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
              <Route path="/students" element={<div className="p-4">Students Management (Coming Soon)</div>} />
              <Route path="/reports" element={<div className="p-4">Global Reports (Coming Soon)</div>} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
