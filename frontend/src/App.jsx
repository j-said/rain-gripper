import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import ProtectedLayout from './components/ProtectedLayout';

const Dashboard = () => <div className="text-center mt-20">Dashboard Coming Soon...</div>;

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Dashboard />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;