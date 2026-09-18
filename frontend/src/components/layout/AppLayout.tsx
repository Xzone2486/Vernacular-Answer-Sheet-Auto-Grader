import { NavLink, Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FileText, Users, BarChart2, LogOut, LayoutDashboard } from 'lucide-react';
import { cn } from '../../lib/utils';

export const AppLayout = () => {
  const { isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const navItems = [
    { label: 'Exams', path: '/', icon: FileText },
    { label: 'Students', path: '/students', icon: Users },
    { label: 'Reports', path: '/reports', icon: BarChart2 },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-white border-r border-gray-200 shadow-sm flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <div className="flex items-center gap-2 text-blue-600">
            <LayoutDashboard size={24} />
            <span className="font-bold text-lg">AutoGrader</span>
          </div>
        </div>
        
        <nav className="flex-1 py-6 px-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-gray-200 px-8 flex items-center justify-between sticky top-0 z-10 shadow-sm">
          <h1 className="text-xl font-semibold text-gray-800 truncate">
            {/* Could inject dynamic page title here, but we'll let pages handle their own headers for now */}
            Dashboard
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-600">Evaluator Profile</span>
            <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
              EV
            </div>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-6xl mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
