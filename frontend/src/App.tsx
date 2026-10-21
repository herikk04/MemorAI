import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ThemeProvider } from "@/components/theme/theme-provider";
import { registerUnauthorizedHandler } from "@/api/api";
import { tokenService } from "@/lib/token-service";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import ReviewPage from "@/pages/ReviewPage";
import DeckPage from "@/pages/DeckPage";
import ReportPage from "@/pages/ReportPage";

// Handler global de 401 após falha de refresh: limpa e manda pra /login.
registerUnauthorizedHandler(() => {
  tokenService.clear();
  if (!["/login", "/register"].includes(window.location.pathname)) {
    window.location.assign("/login");
  }
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!tokenService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <ThemeProvider defaultTheme="system">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute>
                <ReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/decks/:deckId"
            element={
              <ProtectedRoute>
                <DeckPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/report"
            element={
              <ProtectedRoute>
                <ReportPage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
