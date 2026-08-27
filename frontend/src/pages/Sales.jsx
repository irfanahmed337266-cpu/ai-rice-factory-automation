import { useEffect, useState } from "react";
import { Pencil, Trash2, X } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

const EMPTY_FORM = {
  buyer_id: "",
  product_id: "",
  quantity: "",
  selling_rate: "",
  transport_cost: "",
  payment_status: "unpaid",
  status: "completed",
  notes: "",
};

function Sales() {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editingId, setEditingId] = useState(null);

  const [form, setForm] = useState(EMPTY_FORM);

  const loadSales = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("access_token");

      if (!token) {
        throw new Error("Authentication token not found. Please login again.");
      }

      const response = await fetch(`${API_URL}/sales/`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401 || response.status === 403) {
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        throw new Error(`Failed to load sales (${response.status})`);
      }

      const data = await response.json();

      setSales(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Sales loading error:", err);
      setError(err.message || "Failed to load sales");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSales();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const createSale = async (event) => {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const token = localStorage.getItem("access_token");

      const payload = {
        buyer_id: Number(form.buyer_id),
        product_id: Number(form.product_id),
        quantity: Number(form.quantity),
        selling_rate:
          form.selling_rate === ""
            ? null
            : Number(form.selling_rate),
        transport_cost:
          form.transport_cost === ""
            ? null
            : Number(form.transport_cost),
        payment_status: form.payment_status,
        status: form.status,
        notes: form.notes === "" ? null : form.notes,
      };

      if (!payload.buyer_id) {
        throw new Error("Buyer ID is required.");
      }

      if (!payload.product_id) {
        throw new Error("Product ID is required.");
      }

      if (!payload.quantity || payload.quantity <= 0) {
        throw new Error("Quantity must be greater than 0.");
      }

      const response = await fetch(`${API_URL}/sales/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const backendMessage =
          data?.detail ||
          data?.message ||
          "Failed to create sale.";

        throw new Error(
          typeof backendMessage === "string"
            ? backendMessage
            : JSON.stringify(backendMessage)
        );
      }

      setSuccess("Sale created successfully.");

      resetForm();

      await loadSales();
    } catch (err) {
      console.error("Create sale error:", err);
      setError(err.message || "Failed to create sale.");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (sale) => {
    setEditingId(sale.id);

    setForm({
      buyer_id: sale.buyer_id ?? "",
      product_id: sale.product_id ?? "",
      quantity: sale.quantity ?? "",
      selling_rate: sale.selling_rate ?? "",
      transport_cost: sale.transport_cost ?? "",
      payment_status: sale.payment_status ?? "unpaid",
      status: sale.status ?? "completed",
      notes: sale.notes ?? "",
    });

    setError("");
    setSuccess("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const updateSale = async (event) => {
    event.preventDefault();

    if (!editingId) {
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const token = localStorage.getItem("access_token");

      const payload = {
        buyer_id: Number(form.buyer_id),
        product_id: Number(form.product_id),
        quantity: Number(form.quantity),
        selling_rate:
          form.selling_rate === ""
            ? null
            : Number(form.selling_rate),
        transport_cost:
          form.transport_cost === ""
            ? null
            : Number(form.transport_cost),
        payment_status: form.payment_status,
        status: form.status,
        notes: form.notes === "" ? null : form.notes,
      };

      if (!payload.buyer_id) {
        throw new Error("Buyer ID is required.");
      }

      if (!payload.product_id) {
        throw new Error("Product ID is required.");
      }

      if (!payload.quantity || payload.quantity <= 0) {
        throw new Error("Quantity must be greater than 0.");
      }

      const response = await fetch(
        `${API_URL}/sales/${editingId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const backendMessage =
          data?.detail ||
          data?.message ||
          "Failed to update sale.";

        throw new Error(
          typeof backendMessage === "string"
            ? backendMessage
            : JSON.stringify(backendMessage)
        );
      }

      setSuccess(`Sale #${editingId} updated successfully.`);

      resetForm();

      await loadSales();
    } catch (err) {
      console.error("Update sale error:", err);
      setError(err.message || "Failed to update sale.");
    } finally {
      setSaving(false);
    }
  };

  const deleteSale = async (sale) => {
    const confirmed = window.confirm(
      `Delete Sale #${sale.id}?\n\n` +
        `Quantity: ${sale.quantity ?? 0}\n` +
        `Buyer ID: ${sale.buyer_id ?? "-"}\n\n` +
        `This action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");

    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        throw new Error("Authentication token not found.");
      }

      const response = await fetch(
        `${API_URL}/sales/${sale.id}`,
        {
          method: "DELETE",
          headers: {
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const backendMessage =
          data?.detail ||
          data?.message ||
          "Failed to delete sale.";

        throw new Error(
          typeof backendMessage === "string"
            ? backendMessage
            : JSON.stringify(backendMessage)
        );
      }

      setSuccess(
        `Sale #${sale.id} deleted successfully. ` +
          `Stock returned: ${data?.stock_returned ?? 0} kg.`
      );

      if (editingId === sale.id) {
        resetForm();
      }

      await loadSales();
    } catch (err) {
      console.error("Delete sale error:", err);
      setError(err.message || "Failed to delete sale.");
    }
  };

  const formatNumber = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "-";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return value;
    }

    return number.toLocaleString();
  };

  return (
    <div
      style={{
        padding: "30px",
        background: "#f6f8fc",
        minHeight: "100vh",
        color: "#172033",
      }}
    >
      {/* HEADER */}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "25px",
          gap: "15px",
        }}
      >
        <div>
          <p
            style={{
              margin: 0,
              color: "#6366f1",
              fontSize: "11px",
              fontWeight: "800",
              letterSpacing: "0.15em",
            }}
          >
            FACTORY MANAGEMENT
          </p>

          <h1
            style={{
              margin: "7px 0 5px",
              fontSize: "30px",
            }}
          >
            Sales
          </h1>

          <p
            style={{
              margin: 0,
              color: "#64748b",
            }}
          >
            Manage customer sales and transactions.
          </p>
        </div>

        <button
          onClick={loadSales}
          disabled={loading}
          style={{
            padding: "10px 16px",
            border: "1px solid #dbe1ea",
            borderRadius: "10px",
            background: "white",
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: "600",
          }}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {/* MESSAGES */}

      {error && (
        <div
          style={{
            marginBottom: "18px",
            padding: "13px 16px",
            borderRadius: "10px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#b91c1c",
          }}
        >
          {error}
        </div>
      )}

      {success && (
        <div
          style={{
            marginBottom: "18px",
            padding: "13px 16px",
            borderRadius: "10px",
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            color: "#15803d",
          }}
        >
          {success}
        </div>
      )}

      {/* CREATE / EDIT SALE */}

      <div
        style={{
          background: "white",
          border: "1px solid #e8ecf3",
          borderRadius: "18px",
          padding: "24px",
          marginBottom: "22px",
          boxShadow: "0 8px 25px rgba(15,23,42,0.05)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px",
            gap: "10px",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "18px",
            }}
          >
            {editingId
              ? `Edit Sale #${editingId}`
              : "Create New Sale"}
          </h2>

          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 12px",
                border: "1px solid #e2e8f0",
                borderRadius: "9px",
                background: "#f8fafc",
                color: "#475569",
                cursor: "pointer",
                fontWeight: "600",
              }}
            >
              <X size={16} />
              Cancel Edit
            </button>
          )}
        </div>

        <form
          onSubmit={editingId ? updateSale : createSale}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "15px",
            }}
          >
            <div>
              <label>Buyer ID</label>
              <input
                name="buyer_id"
                type="number"
                value={form.buyer_id}
                onChange={handleChange}
                placeholder="e.g. 1"
                required
              />
            </div>

            <div>
              <label>Product ID</label>
              <input
                name="product_id"
                type="number"
                value={form.product_id}
                onChange={handleChange}
                placeholder="e.g. 1"
                required
              />
            </div>

            <div>
              <label>Quantity</label>
              <input
                name="quantity"
                type="number"
                min="1"
                value={form.quantity}
                onChange={handleChange}
                placeholder="Quantity"
                required
              />
            </div>

            <div>
              <label>Selling Rate</label>
              <input
                name="selling_rate"
                type="number"
                step="0.01"
                value={form.selling_rate}
                onChange={handleChange}
                placeholder="Selling rate"
              />
            </div>

            <div>
              <label>Transport Cost</label>
              <input
                name="transport_cost"
                type="number"
                step="0.01"
                value={form.transport_cost}
                onChange={handleChange}
                placeholder="Transport cost"
              />
            </div>

            <div>
              <label>Payment Status</label>
              <select
                name="payment_status"
                value={form.payment_status}
                onChange={handleChange}
              >
                <option value="unpaid">Unpaid</option>
                <option value="partial">Partial</option>
                <option value="paid">Paid</option>
              </select>
            </div>

            <div>
              <label>Status</label>
              <select
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="completed">Completed</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            <div>
              <label>Notes</label>
              <input
                name="notes"
                type="text"
                value={form.notes}
                onChange={handleChange}
                placeholder="Optional notes"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            style={{
              marginTop: "20px",
              padding: "12px 22px",
              border: 0,
              borderRadius: "10px",
              background: editingId
                ? "#059669"
                : "#4f46e5",
              color: "white",
              fontWeight: "700",
              cursor: saving
                ? "not-allowed"
                : "pointer",
            }}
          >
            {saving
              ? editingId
                ? "Updating..."
                : "Creating..."
              : editingId
              ? "Update Sale"
              : "Create Sale"}
          </button>
        </form>
      </div>

      {/* SALES TABLE */}

      <div
        style={{
          background: "white",
          border: "1px solid #e8ecf3",
          borderRadius: "18px",
          overflow: "hidden",
          boxShadow: "0 8px 25px rgba(15,23,42,0.05)",
        }}
      >
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid #eef1f6",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "17px",
            }}
          >
            Sales Transactions
          </h2>
        </div>

        {loading ? (
          <div
            style={{
              padding: "40px",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            Loading sales...
          </div>
        ) : sales.length === 0 ? (
          <div
            style={{
              padding: "50px",
              textAlign: "center",
              color: "#94a3b8",
            }}
          >
            No sales found.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "1000px",
              }}
            >
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <th style={thStyle}>ID</th>
                  <th style={thStyle}>Buyer</th>
                  <th style={thStyle}>Product</th>
                  <th style={thStyle}>Quantity</th>
                  <th style={thStyle}>Selling Rate</th>
                  <th style={thStyle}>Transport</th>
                  <th style={thStyle}>Payment</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>

              <tbody>
                {sales.map((sale) => (
                  <tr key={sale.id}>
                    <td style={tdStyle}>{sale.id}</td>

                    <td style={tdStyle}>
                      {sale.buyer_id ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      {sale.product_id ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      {formatNumber(sale.quantity)}
                    </td>

                    <td style={tdStyle}>
                      Rs. {formatNumber(sale.selling_rate)}
                    </td>

                    <td style={tdStyle}>
                      Rs. {formatNumber(sale.transport_cost)}
                    </td>

                    <td style={tdStyle}>
                      {sale.payment_status ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      {sale.status ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => startEdit(sale)}
                          title="Edit sale"
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "5px",
                            padding: "7px 10px",
                            border: "1px solid #c7d2fe",
                            borderRadius: "8px",
                            background: "#eef2ff",
                            color: "#4338ca",
                            cursor: "pointer",
                            fontWeight: "700",
                            fontSize: "11px",
                          }}
                        >
                          <Pencil size={14} />
                          Edit
                        </button>

                        <button
                          type="button"
                          onClick={() => deleteSale(sale)}
                          title="Delete sale"
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "5px",
                            padding: "7px 10px",
                            border: "1px solid #fecaca",
                            borderRadius: "8px",
                            background: "#fef2f2",
                            color: "#dc2626",
                            cursor: "pointer",
                            fontWeight: "700",
                            fontSize: "11px",
                          }}
                        >
                          <Trash2 size={14} />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        label {
          display: block;
          margin-bottom: 7px;
          color: #475569;
          font-size: 12px;
          font-weight: 700;
        }

        input,
        select {
          width: 100%;
          box-sizing: border-box;
          padding: 11px 12px;
          border: 1px solid #dbe1ea;
          border-radius: 9px;
          background: #fff;
          color: #1e293b;
          outline: none;
          font-size: 13px;
        }

        input:focus,
        select:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99,102,241,0.10);
        }
      `}</style>
    </div>
  );
}

const thStyle = {
  padding: "13px 16px",
  textAlign: "left",
  fontSize: "11px",
  color: "#64748b",
  fontWeight: "800",
  borderBottom: "1px solid #e8ecf3",
  whiteSpace: "nowrap",
};

const tdStyle = {
  padding: "14px 16px",
  fontSize: "12px",
  color: "#334155",
  borderBottom: "1px solid #f0f2f6",
  whiteSpace: "nowrap",
};

export default Sales;