import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/useAuth";

const EMPTY_FORM = {
    amount: "",
    type: "expense",
    category: "",
    date: "",
    notes: "",
};

function toApiPayload(form) {
    return {
        amount: Number(form.amount),
        type: form.type,
        category: form.category,
        date: form.date ? new Date(`${form.date}T00:00:00`).toISOString() : undefined,
        notes: form.notes || null,
    };
}

function TransactionsPage() {
    const { role } = useAuth();
    const canManage = role === "admin";

    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [form, setForm] = useState(EMPTY_FORM);
    const [editingId, setEditingId] = useState(null);

    const [filters, setFilters] = useState({
        type: "",
        search: "",
        category: "",
        skip: 0,
        limit: 10,
        sort_by: "date",
        sort_order: "desc",
    });

    const page = Math.floor(filters.skip / filters.limit) + 1;
    const totalPages = Math.max(1, Math.ceil(total / filters.limit));

    const queryParams = useMemo(() => {
        const params = {
            skip: filters.skip,
            limit: filters.limit,
            sort_by: filters.sort_by,
            sort_order: filters.sort_order,
        };

        if (filters.type) {
            params.type = filters.type;
        }
        if (filters.search) {
            params.search = filters.search;
        }
        if (filters.category) {
            params.category = filters.category;
        }

        return params;
    }, [filters]);

    async function loadTransactions(withLoading = true) {
        if (withLoading) {
            setLoading(true);
        }
        setError("");
        try {
            const response = await api.get("/transactions", { params: queryParams });
            setItems(response.data.items || []);
            setTotal(response.data.total || 0);
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to load transactions.");
        } finally {
            if (withLoading) {
                setLoading(false);
            }
        }
    }

    useEffect(() => {
        let active = true;

        async function syncTransactions() {
            try {
                const response = await api.get("/transactions", { params: queryParams });
                if (!active) {
                    return;
                }
                setItems(response.data.items || []);
                setTotal(response.data.total || 0);
                setError("");
            } catch (err) {
                if (!active) {
                    return;
                }
                setError(err?.response?.data?.detail || "Unable to load transactions.");
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        syncTransactions();
        return () => {
            active = false;
        };
    }, [queryParams]);

    function onFilterChange(event) {
        const { name, value } = event.target;
        setFilters((current) => ({ ...current, [name]: value, skip: 0 }));
    }

    function onFormChange(event) {
        const { name, value } = event.target;
        setForm((current) => ({ ...current, [name]: value }));
    }

    function startEdit(item) {
        setEditingId(item.id);
        setForm({
            amount: String(item.amount),
            type: item.type,
            category: item.category,
            date: item.date ? new Date(item.date).toISOString().slice(0, 10) : "",
            notes: item.notes || "",
        });
    }

    function resetForm() {
        setEditingId(null);
        setForm(EMPTY_FORM);
    }

    async function onSubmit(event) {
        event.preventDefault();
        setError("");

        try {
            if (!canManage) {
                setError("Only admin can create or update transactions in this backend setup.");
                return;
            }

            const payload = toApiPayload(form);
            if (editingId) {
                await api.put(`/transactions/${editingId}`, payload);
            } else {
                await api.post("/transactions", payload);
            }
            resetForm();
            await loadTransactions();
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to save transaction.");
        }
    }

    async function onDelete(id) {
        if (!canManage) {
            setError("Only admin can delete transactions in this backend setup.");
            return;
        }

        const confirmed = window.confirm("Delete this transaction?");
        if (!confirmed) {
            return;
        }

        try {
            await api.delete(`/transactions/${id}`);
            await loadTransactions();
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to delete transaction.");
        }
    }

    async function onExportCsv() {
        try {
            const response = await api.get("/transactions/export", {
                params: queryParams,
                responseType: "blob",
            });
            const blobUrl = URL.createObjectURL(new Blob([response.data], { type: "text/csv" }));
            const link = document.createElement("a");
            link.href = blobUrl;
            link.download = "transactions.csv";
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(blobUrl);
        } catch {
            setError("Unable to export CSV.");
        }
    }

    async function onImportCsv(event) {
        const file = event.target.files?.[0];
        if (!file) {
            return;
        }

        const data = new FormData();
        data.append("file", file);

        try {
            await api.post("/transactions/import", data, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            await loadTransactions();
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to import CSV.");
        } finally {
            event.target.value = "";
        }
    }

    return (
        <div className="stack gap-20">
            <header className="row between wrap gap-10">
                <div>
                    <h1>Transactions</h1>
                    <p className="subtext">Track, filter, and manage all records.</p>
                </div>

                <div className="row gap-10">
                    <button type="button" className="btn btn-outline" onClick={onExportCsv}>
                        Export CSV
                    </button>
                    <label className="btn btn-outline file-btn">
                        Import CSV
                        <input type="file" accept=".csv" onChange={onImportCsv} />
                    </label>
                </div>
            </header>

            <section className="panel">
                <div className="filters-grid">
                    <label className="field">
                        <span>Type</span>
                        <select name="type" value={filters.type} onChange={onFilterChange}>
                            <option value="">All</option>
                            <option value="income">Income</option>
                            <option value="expense">Expense</option>
                        </select>
                    </label>

                    <label className="field">
                        <span>Category</span>
                        <input
                            type="text"
                            name="category"
                            value={filters.category}
                            onChange={onFilterChange}
                            placeholder="groceries"
                        />
                    </label>

                    <label className="field">
                        <span>Search</span>
                        <input
                            type="text"
                            name="search"
                            value={filters.search}
                            onChange={onFilterChange}
                            placeholder="notes or category"
                        />
                    </label>

                    <label className="field">
                        <span>Sort</span>
                        <select name="sort_by" value={filters.sort_by} onChange={onFilterChange}>
                            <option value="date">Date</option>
                            <option value="amount">Amount</option>
                            <option value="category">Category</option>
                            <option value="type">Type</option>
                            <option value="id">ID</option>
                        </select>
                    </label>

                    <label className="field">
                        <span>Order</span>
                        <select name="sort_order" value={filters.sort_order} onChange={onFilterChange}>
                            <option value="desc">Descending</option>
                            <option value="asc">Ascending</option>
                        </select>
                    </label>
                </div>
            </section>

            <section className="panel">
                <h3>{editingId ? "Edit Transaction" : "Add Transaction"}</h3>
                <form onSubmit={onSubmit} className="transaction-form">
                    <label className="field">
                        <span>Amount</span>
                        <input type="number" min="0.01" step="0.01" name="amount" value={form.amount} onChange={onFormChange} required />
                    </label>

                    <label className="field">
                        <span>Type</span>
                        <select name="type" value={form.type} onChange={onFormChange}>
                            <option value="income">Income</option>
                            <option value="expense">Expense</option>
                        </select>
                    </label>

                    <label className="field">
                        <span>Category</span>
                        <input type="text" name="category" value={form.category} onChange={onFormChange} minLength={2} required />
                    </label>

                    <label className="field">
                        <span>Date</span>
                        <input
                            type="date"
                            name="date"
                            value={form.date}
                            onChange={onFormChange}
                            max={new Date().toISOString().slice(0, 10)}
                        />
                    </label>

                    <label className="field form-span-2">
                        <span>Notes</span>
                        <textarea name="notes" value={form.notes} onChange={onFormChange} rows={3} />
                    </label>

                    <div className="row gap-10">
                        <button className="btn btn-primary" type="submit" disabled={!canManage}>
                            {editingId ? "Update" : "Add"}
                        </button>
                        {editingId ? (
                            <button type="button" className="btn btn-outline" onClick={resetForm}>
                                Cancel
                            </button>
                        ) : null}
                    </div>
                </form>
                {!canManage ? (
                    <p className="muted">Current backend permits create/update/delete only for admin users.</p>
                ) : null}
            </section>

            <section className="panel">
                {loading ? <p className="status">Loading transactions...</p> : null}
                {error ? <p className="status error">{error}</p> : null}

                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Category</th>
                                <th>Amount</th>
                                <th>Notes</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item) => (
                                <tr key={item.id}>
                                    <td>{item.id}</td>
                                    <td>{new Date(item.date).toLocaleDateString()}</td>
                                    <td>
                                        <span className={`pill ${item.type}`}>{item.type}</span>
                                    </td>
                                    <td>{item.category}</td>
                                    <td>${Number(item.amount).toFixed(2)}</td>
                                    <td>{item.notes || "-"}</td>
                                    <td>
                                        <div className="row gap-8">
                                            <button type="button" className="btn-inline" onClick={() => startEdit(item)}>
                                                Edit
                                            </button>
                                            <button type="button" className="btn-inline danger" onClick={() => onDelete(item.id)}>
                                                Delete
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {!items.length && !loading ? <p className="muted">No transactions found.</p> : null}

                <footer className="row between wrap gap-10">
                    <p className="muted">
                        Page {page} of {totalPages} | Total {total}
                    </p>
                    <div className="row gap-10">
                        <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => setFilters((current) => ({ ...current, skip: Math.max(0, current.skip - current.limit) }))}
                            disabled={filters.skip === 0}
                        >
                            Previous
                        </button>
                        <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() =>
                                setFilters((current) => ({
                                    ...current,
                                    skip: current.skip + current.limit,
                                }))
                            }
                            disabled={filters.skip + filters.limit >= total}
                        >
                            Next
                        </button>
                    </div>
                </footer>
            </section>
        </div>
    );
}

export default TransactionsPage;
