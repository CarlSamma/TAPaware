import { Dashboard } from './pages/Dashboard';
import { TopBar } from './components/layout/TopBar';
import { ToastProvider } from './components/toast/ToastContainer';

export default function App() {
  return (
    <ToastProvider>
      <div className="min-h-screen bg-[var(--bg-base)] flex flex-col">
        <TopBar />
        <Dashboard />
      </div>
    </ToastProvider>
  );
}