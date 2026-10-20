import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { ToastProvider } from '@/components/Toast';
import { LanguageProvider } from '@/i18n/LanguageContext';
import { AdminPage } from '@/pages/AdminPage';
import { AppointmentsPage } from '@/pages/AppointmentsPage';
import { DoctorPage } from '@/pages/DoctorPage';
import { DoctorsPage } from '@/pages/DoctorsPage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<DoctorsPage />} />
                <Route path="doctors/:id" element={<DoctorPage />} />
                <Route path="appointments" element={<AppointmentsPage />} />
                <Route path="admin" element={<AdminPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </LanguageProvider>
    </QueryClientProvider>
  );
}
