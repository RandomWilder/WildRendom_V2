// src/App.tsx

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './lib/auth/auth-context';
import { AppRouter } from './routes/AppRouter';
import { AppLayout } from './components/layout/AppLayout';
import { AdminRoutes } from './admin/routes/AdminRoutes';

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true }}>
      <AuthProvider>
        <Routes>
          {/* Admin Routes */}
          <Route path="/admin/*" element={<AdminRoutes />} />
          
          {/* Main App Routes */}
          <Route path="/*" element={
            <AppLayout>
              <AppRouter />
            </AppLayout>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;