import { useEffect, useState } from "react";
import {
  RefreshCw,
  Plus,
  Users,
  X,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

function Buyers() {
  const [buyers, setBuyers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    name: "",
    phone: "",
    address: "",
    notes: "",
  });

  const getToken = () => localStorage.getItem("access_token");

  const getHeaders = () => ({
    Authorization: `Bearer ${getToken()}`,
    Accept: "application/json",
  });

  const loadBuyers = async () => {
    setLoading(true);
    setError("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error("Authentication token not found. Please login again.");
      }

      const response = await fetch(`${API_URL}/buyers/`, {
        method: "GET",
        headers: getHeaders(),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail || `Failed to load buyers (${response.status})`
        );
      }

      setBuyers(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load buyers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBuyers();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleCreateBuyer = async (e) => {
    e.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error("Authentication token not found. Please login again.");
      }

      const payload = {
        name: form.name.trim(),
        phone: form.phone.trim() || null,
        address: form.address.trim() || null,
        notes: form.notes.trim() || null,
      };

      const response = await fetch(`${API_URL}/buyers/`, {
        method: "POST",
        headers: {
          ...getHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail || `Failed to create buyer (${response.status})`
        );
      }

      setSuccess("Buyer created successfully.");

      setForm({
        name: "",
        phone: "",
        address: "",
        notes: "",
      });

      setShowForm(false);

      await loadBuyers();
    } catch (err) {
      setError(err.message || "Failed to create buyer");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "30px",
        background: "#f6f8fc",
        color: "#172033",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "20px",
          marginBottom: "25px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p
            style={{
              margin: "0 0 7px",
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
              margin: 0,
              fontSize: "32px",
              color: "#111827",
            }}
          >
            Buyers
          </h1>

          <p
            style={{
              marginTop: "8px",
              color: "#64748b",
              fontSize: "14px",
            }}
          >
            Manage customers and buyer information.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={loadBuyers}
            disabled={loading}
            style={secondaryButton}
          >
            <RefreshCw size={16} />
            Refresh
          </button>

          <button
            onClick={() => {
              setError("");
              setSuccess("");
              setShowForm(true);
            }}
            style={primaryButton}
          >
            <Plus size={17} />
            Add Buyer
          </button>
        </div>
      </div>

      {/* MESSAGES */}
      {error && (
        <div
          style={{
            marginBottom: "18px",
            padding: "13px 15px",
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
            padding: "13px 15px",
            borderRadius: "10px",
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            color: "#15803d",
          }}
        >
          {success}
        </div>
      )}

      {/* CREATE FORM */}
      {showForm && (
        <div
          style={{
            marginBottom: "22px",
            padding: "24px",
            border: "1px solid #e5e7eb",
            borderRadius: "18px",
            background: "#fff",
            boxShadow: "0 8px 25px rgba(15,23,42,0.05)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "20px",
            }}
          >
            <h2 style={{ margin: 0, fontSize: "18px" }}>
              Create New Buyer
            </h2>

            <button
              onClick={() => setShowForm(false)}
              style={{
                border: 0,
                background: "transparent",
                cursor: "pointer",
              }}
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleCreateBuyer}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "16px",
              }}
            >
              <div>
                <label style={labelStyle}>Buyer Name</label>

                <input
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                  placeholder="Enter buyer name"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Phone</label>

                <input
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  placeholder="Enter phone number"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Address</label>

                <input
                  name="address"
                  value={form.address}
                  onChange={handleChange}
                  placeholder="Enter address"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Notes</label>

                <input
                  name="notes"
                  value={form.notes}
                  onChange={handleChange}
                  placeholder="Optional notes"
                  style={inputStyle}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              style={{
                marginTop: "20px",
                padding: "12px 18px",
                border: 0,
                borderRadius: "10px",
                background: saving ? "#94a3b8" : "#4f46e5",
                color: "#fff",
                fontWeight: "700",
                cursor: saving ? "not-allowed" : "pointer",
              }}
            >
              {saving ? "Creating..." : "Create Buyer"}
            </button>
          </form>
        </div>
      )}

      {/* BUYERS TABLE */}
      <div
        style={{
          overflow: "hidden",
          border: "1px solid #e5e7eb",
          borderRadius: "18px",
          background: "#fff",
          boxShadow: "0 8px 30px rgba(15,23,42,0.04)",
        }}
      >
        <div
          style={{
            padding: "20px 22px",
            borderBottom: "1px solid #eef1f6",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "17px" }}>
            Buyer Records
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#94a3b8",
              fontSize: "12px",
            }}
          >
            Live buyer data from the factory database.
          </p>
        </div>

        {loading ? (
          <div
            style={{
              padding: "50px",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            Loading buyers...
          </div>
        ) : buyers.length === 0 ? (
          <div
            style={{
              padding: "50px",
              textAlign: "center",
              color: "#94a3b8",
            }}
          >
            <Users
              size={35}
              style={{ marginBottom: "10px" }}
            />

            <div style={{ color: "#334155", fontWeight: "700" }}>
              No buyers found
            </div>

            <div style={{ marginTop: "5px", fontSize: "12px" }}>
              Add your first buyer.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                minWidth: "700px",
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <th style={thStyle}>ID</th>
                  <th style={thStyle}>Name</th>
                  <th style={thStyle}>Phone</th>
                  <th style={thStyle}>Address</th>
                  <th style={thStyle}>Notes</th>
                </tr>
              </thead>

              <tbody>
                {buyers.map((buyer) => (
                  <tr key={buyer.id}>
                    <td style={tdStyle}>
                      {buyer.id}
                    </td>

                    <td
                      style={{
                        ...tdStyle,
                        fontWeight: "700",
                      }}
                    >
                      {buyer.name ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      {buyer.phone ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      {buyer.address ?? "-"}
                    </td>

                    <td style={tdStyle}>
                      {buyer.notes ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

const labelStyle = {
  display: "block",
  color: "#334155",
  fontSize: "13px",
  fontWeight: "600",
};

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  marginTop: "7px",
  padding: "11px 13px",
  border: "1px solid #cbd5e1",
  borderRadius: "9px",
  fontSize: "14px",
  outline: "none",
};

const secondaryButton = {
  display: "flex",
  alignItems: "center",
  gap: "7px",
  padding: "10px 14px",
  border: "1px solid #dbe2ea",
  borderRadius: "10px",
  background: "#fff",
  cursor: "pointer",
};

const primaryButton = {
  display: "flex",
  alignItems: "center",
  gap: "7px",
  padding: "10px 15px",
  border: 0,
  borderRadius: "10px",
  background: "#4f46e5",
  color: "#fff",
  fontWeight: "700",
  cursor: "pointer",
};

const thStyle = {
  padding: "13px 16px",
  textAlign: "left",
  color: "#64748b",
  fontSize: "11px",
  fontWeight: "800",
  borderBottom: "1px solid #e5e7eb",
};

const tdStyle = {
  padding: "14px 16px",
  color: "#334155",
  fontSize: "13px",
  borderBottom: "1px solid #f1f5f9",
};

export default Buyers;