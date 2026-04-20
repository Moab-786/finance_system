import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

function LoginPage() {
    const { login, isAuthLoading } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [form, setForm] = useState({ username: "", password: "" });
    const [error, setError] = useState("");

    const redirectTo = location.state?.from?.pathname || "/dashboard";

    function onChange(event) {
        const { name, value } = event.target;
        setForm((current) => ({ ...current, [name]: value }));
    }

    async function onSubmit(event) {
        event.preventDefault();
        setError("");

        try {
            await login(form);
            navigate(redirectTo, { replace: true });
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to login. Please try again.");
        }
    }

    return (
        <main className="auth-shell">
            <section className="auth-card">
                <p className="eyebrow">FinTrack</p>
                <h1>Welcome Back</h1>
                <p className="subtext">Sign in to manage your finance records.</p>

                <form onSubmit={onSubmit} className="stack gap-16">
                    <label className="field">
                        <span>Username</span>
                        <input
                            type="text"
                            name="username"
                            value={form.username}
                            onChange={onChange}
                            placeholder="Enter username"
                            required
                        />
                    </label>

                    <label className="field">
                        <span>Password</span>
                        <input
                            type="password"
                            name="password"
                            value={form.password}
                            onChange={onChange}
                            placeholder="Enter password"
                            required
                        />
                    </label>

                    {error ? <p className="form-error">{error}</p> : null}

                    <button type="submit" className="btn btn-primary" disabled={isAuthLoading}>
                        {isAuthLoading ? "Signing in..." : "Sign In"}
                    </button>
                </form>

                <p className="muted">
                    No account yet? <Link to="/signup">Create one</Link>
                </p>
            </section>
        </main>
    );
}

export default LoginPage;
