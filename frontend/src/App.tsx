import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/Common/AppShell";
import { ErrorBoundary } from "@/components/Common/ErrorBoundary";
import { ToastHost } from "@/components/Common/ToastHost";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { AdminPage } from "@/pages/AdminPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { ProjectDetailPage } from "@/pages/ProjectDetailPage";
import { ProjectUploadPage } from "@/pages/ProjectUploadPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { RunDetailPage } from "@/pages/RunDetailPage";

const App = () => (
  <ErrorBoundary>
    <BrowserRouter>
      <ToastHost />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/upload" element={<ProjectUploadPage />} />
          <Route path="/runs/:runId" element={<RunDetailPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  </ErrorBoundary>
);

export default App;
