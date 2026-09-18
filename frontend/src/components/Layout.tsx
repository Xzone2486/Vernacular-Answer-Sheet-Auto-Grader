import React from 'react';

type Page = 'dashboard' | 'ocr-test';

interface LayoutProps {
  children: React.ReactNode;
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, currentPage, onNavigate }) => {
  const navItems: { label: string; page: Page }[] = [
    { label: 'Dashboard', page: 'dashboard' },
    { label: 'OCR Test', page: 'ocr-test' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-2xl font-bold">Vernacular Auto-Grader</h1>
      </header>
      <div className="flex flex-1">
        <aside className="w-64 bg-white border-r p-4 shadow-sm hidden md:block">
          <nav className="space-y-2">
            {navItems.map((item) => (
              <button
                key={item.page}
                onClick={() => onNavigate(item.page)}
                className={`block w-full text-left p-2 rounded-md font-medium transition-colors ${
                  currentPage === item.page
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {item.label}
              </button>
            ))}
            <span className="block p-2 text-gray-400 cursor-not-allowed">Exams</span>
            <span className="block p-2 text-gray-400 cursor-not-allowed">Answer Sheets</span>
          </nav>
        </aside>
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
};
