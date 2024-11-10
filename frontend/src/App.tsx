// src/App.tsx

import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './lib/auth/auth-context';
import { AppRouter } from './routes/AppRouter';
import { AppLayout } from './components/layout/AppLayout';

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true }}>
      <AuthProvider>
        <AppLayout>
          <AppRouter />
        </AppLayout>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;