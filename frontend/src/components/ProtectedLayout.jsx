import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useCurrentUser } from '../hooks/useAuth';

const ProtectedLayout = () => {
  const token = useAuthStore((state) => state.token);
  
  // Attempt to fetch user profile if we have a token
  // This validates the token is actually still valid on the server
  useCurrentUser();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="font-bold text-xl tracking-tight text-blue-500">
            RainGripper <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded ml-2">v0.2</span>
          </div>
          <button 
            onClick={() => useAuthStore.getState().logout()}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Sign Out
          </button>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto p-4 py-8">
        <Outlet />
      </main>
    </div>
  );
};

export default ProtectedLayout;