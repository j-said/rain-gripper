import { useMutation, useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

export const useLogin = () => {
  const setToken = useAuthStore((state) => state.setToken);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ email, password }) => {
      // Backend expects x-www-form-urlencoded data
      const params = new URLSearchParams();
      params.append('username', email); // Map email to 'username'
      params.append('password', password);

      const { data } = await api.post('/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      return data; // Returns { access_token, token_type }
    },
    onSuccess: (data) => {
      setToken(data.access_token);
      navigate('/'); // Redirect to Dashboard
    },
  });
};

export const useRegister = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ email, password, username, name }) => {
      const { data } = await api.post('/api/v1/users/', {
        email,
        password,
        username,
        name
      });
      return data;
    },
    onSuccess: () => {
      // Auto-redirect to login after success
      navigate('/login?registered=true');
    },
  });
};

export const useCurrentUser = () => {
  const setUser = useAuthStore((state) => state.setUser);
  
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/users/me');
      setUser(data);
      return data;
    },
    // Only run this if we have a token
    enabled: !!localStorage.getItem('auth_token'),
    retry: false,
  });
};