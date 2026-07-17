import { useState, type FormEvent } from "react";
import { useAuth } from "@/auth/AuthContext";
import { errorMessage } from "@/api/client";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <h1>Levantamiento Eléctrico</h1>
        <p className="sub">Plataforma de Administración</p>
        {error && <div className="error">⚠ {error}</div>}
        <label>Usuario</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
        <label>Contraseña</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="btn" style={{ width: "100%" }} disabled={busy}>
          {busy ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
