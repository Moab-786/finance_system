import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

function AppLayout() {
    const { role, logout } = useAuth();
    const navigate = useNavigate();

    async function onLogout() {
        await logout();
        navigate("/login", { replace: true });
    }

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div>
                    <p className="eyebrow">FinTrack</p>
                    <h2>Control Center</h2>
                    <p className="muted">Role: {role || "unknown"}</p>
                </div>

                <nav className="stack gap-10">
                    <NavLink to="/dashboard" className="nav-item">
                        Dashboard
                    </NavLink>
                    <NavLink to="/transactions" className="nav-item">
                        Transactions
                    </NavLink>
                </nav>

                <button type="button" className="btn btn-ghost" onClick={onLogout}>
                    Logout
                </button>
            </aside>

            <section className="content-panel">
                <Outlet />
            </section>
        </div>
    );
}

export default AppLayout;
