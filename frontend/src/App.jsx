import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard'; 
import ProtectedLayout from './components/ProtectedLayout';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      {/* Protected Routes (Only accessible if logged in) */}
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Dashboard />} />
      </Route>
      
      {/* Redirect unknown paths to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;