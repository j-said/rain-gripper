import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useCurrentUser } from '../hooks/useAuth';
import { Sprout, LogOut } from 'lucide-react';

const ProtectedLayout = () => {
  const token = useAuthStore((state) => state.token);

  // Validate session
  useCurrentUser();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-gray-900">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div className="bg-green-100 p-1.5 rounded-lg">
              <Sprout className="text-green-600 w-5 h-5" />
            </div>
            <span className="font-bold text-xl tracking-tight text-gray-900">
              Rain<span className="text-green-600">Gripper</span>
            </span>
            <span className="text-[10px] font-medium text-green-700 bg-green-50 border border-green-200 px-1.5 py-0.5 rounded ml-2">
              PRO
            </span>
          </div>

          {/* Actions */}
          <button
            onClick={() => useAuthStore.getState().logout()}
            className="flex items-center space-x-2 text-sm font-medium text-gray-500 hover:text-red-600 transition-colors px-3 py-2 rounded-lg hover:bg-red-50"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-4 py-8">
        <Outlet />
      </main>
    </div>
  );
};

export default ProtectedLayout;