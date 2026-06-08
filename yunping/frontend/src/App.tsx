import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import AppLayout from './components/Layout';
import LoginPage from './pages/Login';
import { useAppStore } from './store';
import { getMe } from './api';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

function App() {
  const { token, setUserInfo } = useAppStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (token) {
      getMe().then((user: any) => { setUserInfo(user); setChecking(false); }).catch(() => setChecking(false));
    } else {
      setChecking(false);
    }
  }, [token]);

  if (checking) return null;

  return (
    <QueryClientProvider client={queryClient}>
      {token ? <AppLayout /> : <LoginPage />}
    </QueryClientProvider>
  );
}

export default App;
