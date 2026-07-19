import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Works from "@/pages/Works";
import Devices from "@/pages/Devices";
import Users from "@/pages/Users";
import Quality from "@/pages/Quality";
import Reports from "@/pages/Reports";
import Consolidation from "@/pages/Consolidation";
import History from "@/pages/History";
import Audit from "@/pages/Audit";
import { Loading } from "@/components/ui";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;
  if (!user) return <Login />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="works" element={<Works />} />
        <Route path="devices" element={<Devices />} />
        {user.role === "ADMIN" && <Route path="users" element={<Users />} />}
        <Route path="quality" element={<Quality />} />
        <Route path="reports" element={<Reports />} />
        <Route path="consolidation" element={<Consolidation />} />
        <Route path="history" element={<History />} />
        <Route path="audit" element={<Audit />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
