import React, { createContext, useContext, useState, useCallback } from 'react';
import { cn } from '../../lib/utils';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextType {
  toast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              'flex items-center gap-3 min-w-[300px] rounded-lg p-4 shadow-lg border transition-all animate-in slide-in-from-bottom-5',
              {
                'bg-white border-gray-200': t.type === 'info',
                'bg-green-50 border-green-200 text-green-800': t.type === 'success',
                'bg-red-50 border-red-200 text-red-800': t.type === 'error',
              }
            )}
          >
            {t.type === 'success' && <CheckCircle className="text-green-500" size={20} />}
            {t.type === 'error' && <AlertCircle className="text-red-500" size={20} />}
            {t.type === 'info' && <Info className="text-blue-500" size={20} />}
            <p className="flex-1 text-sm font-medium">{t.message}</p>
            <button
              onClick={() => removeToast(t.id)}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
