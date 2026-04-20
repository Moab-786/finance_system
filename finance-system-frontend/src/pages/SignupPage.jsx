import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

const ROLES = [
    { label: "Admin", value: "admin" },
    { label: "Analyst", value: "analyst" },
    { label: "Viewer", value: "viewer" },
];

function SignupPage() {
    const { signup, isAuthLoading } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({
        username: "",
        email: "",
        password: "",
        role: "admin",
    });
    const [error, setError] = useState("");

    function onChange(event) {
        const { name, value } = event.target;
        setForm((current) => ({ ...current, [name]: value }));
    }

    async function onSubmit(event) {
        event.preventDefault();
        setError("");

        try {
            await signup(form);
            navigate("/dashboard", { replace: true });
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to create account.");
        }
    }

    return (
        <main className="auth-shell">
            <section className="auth-card">
                <p className="eyebrow">FinTrack</p>
                <h1>Create Account</h1>
                <p className="subtext">Sign up and start tracking money in minutes.</p>

                <form onSubmit={onSubmit} className="stack gap-16">
                    <label className="field">
                        <span>Username</span>
                        <input
                            type="text"
                            name="username"
                            value={form.username}
                            onChange={onChange}
                            minLength={3}
                            required
                        />
                    </label>

                    <label className="field">
                        <span>Email</span>
                        <input type="email" name="email" value={form.email} onChange={onChange} required />
                    </label>

                    <label className="field">
                        <span>Password</span>
                        <input
                            type="password"
                            name="password"
                            value={form.password}
                            onChange={onChange}
                            minLength={8}
                            required
                        />
                    </label>

                    <label className="field">
                        <span>Role</span>
                        <select name="role" value={form.role} onChange={onChange}>
                            {ROLES.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </label>

                    {error ? <p className="form-error">{error}</p> : null}

                    <button type="submit" className="btn btn-primary" disabled={isAuthLoading}>
                        {isAuthLoading ? "Creating account..." : "Sign Up"}
                    </button>
                </form>

                <p className="muted">
                    Already have an account? <Link to="/login">Sign in</Link>
                </p>
            </section>
        </main>
    );
}

export default SignupPage;
