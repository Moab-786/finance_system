import { useEffect, useMemo, useState } from "react";
import {
    ArcElement,
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LinearScale,
    Tooltip,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import { api } from "../api/client";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Legend, Tooltip);

function DashboardPage() {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function loadSummary() {
            try {
                setLoading(true);
                const response = await api.get("/analytics/summary");
                setSummary(response.data);
            } catch (err) {
                if (err?.response?.status === 403) {
                    setError("Your role cannot access analytics. Use analyst or admin.");
                } else {
                    setError("Unable to load dashboard summary.");
                }
            } finally {
                setLoading(false);
            }
        }

        loadSummary();
    }, []);

    const expenseVsIncomeData = useMemo(() => {
        if (!summary) {
            return null;
        }

        return {
            labels: ["Income", "Expenses"],
            datasets: [
                {
                    data: [summary.total_income || 0, summary.total_expenses || 0],
                    backgroundColor: ["#4caf50", "#ef5350"],
                    borderWidth: 0,
                },
            ],
        };
    }, [summary]);

    const categoryData = useMemo(() => {
        if (!summary) {
            return null;
        }

        const entries = Object.entries(summary.category_breakdown || {});
        return {
            labels: entries.map(([category]) => category),
            datasets: [
                {
                    label: "Category Spend",
                    data: entries.map(([, amount]) => amount),
                    backgroundColor: ["#e76f51", "#2a9d8f", "#f4a261", "#264653", "#8ab17d", "#d62828"],
                },
            ],
        };
    }, [summary]);

    if (loading) {
        return <p className="status">Loading dashboard...</p>;
    }

    if (error) {
        return <p className="status error">{error}</p>;
    }

    return (
        <div className="stack gap-20">
            <header>
                <h1>Dashboard</h1>
                <p className="subtext">Your finance overview at a glance.</p>
            </header>

            <section className="stats-grid">
                <article className="stat-card">
                    <p className="label">Total Income</p>
                    <p className="value">${(summary?.total_income || 0).toFixed(2)}</p>
                </article>
                <article className="stat-card">
                    <p className="label">Total Expenses</p>
                    <p className="value">${(summary?.total_expenses || 0).toFixed(2)}</p>
                </article>
                <article className="stat-card balance">
                    <p className="label">Balance</p>
                    <p className="value">${(summary?.balance || 0).toFixed(2)}</p>
                </article>
            </section>

            <section className="chart-grid">
                <article className="panel">
                    <h3>Income vs Expenses</h3>
                    {expenseVsIncomeData ? <Doughnut data={expenseVsIncomeData} /> : null}
                </article>
                <article className="panel">
                    <h3>Category Breakdown</h3>
                    {categoryData && categoryData.labels.length ? (
                        <Bar
                            data={categoryData}
                            options={{
                                plugins: { legend: { display: false } },
                                scales: { y: { beginAtZero: true } },
                            }}
                        />
                    ) : (
                        <p className="muted">No category data yet.</p>
                    )}
                </article>
            </section>
        </div>
    );
}

export default DashboardPage;
