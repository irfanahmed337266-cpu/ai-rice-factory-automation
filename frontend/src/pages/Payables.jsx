import { useCallback, useEffect, useState } from "react";
import {
  RefreshCw,
  Wallet,
  CircleDollarSign,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

function Payables() {
  const [payables, setPayables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const getToken = () => {
    return localStorage.getItem("access_token");
  };

  const loadPayables = useCallback(async () => {
    const token = getToken();

    if (!token) {
      setError("Authentication required. Please login again.");
      setLoading(false);
      return;
    }

    try {
      setError("");

      const response = await fetch(`${API_URL}/payables/`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        setError("Session expired. Please login again.");
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || `Failed to load payables (${response.status})`
        );
      }

      setPayables(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load payables");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadPayables();
  }, [loadPayables]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadPayables();
  };

  const formatCurrency = (value) => {
    const amount = Number(value || 0);

    return `Rs. ${amount.toLocaleString("en-PK", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const totalAmount = payables.reduce(
    (sum, item) => sum + Number(item.total_amount || 0),
    0
  );

  const paidAmount = payables.reduce(
    (sum, item) => sum + Number(item.paid_amount || 0),
    0
  );

  const payableAmount = payables.reduce(
    (sum, item) => sum + Number(item.payable_amount || 0),
    0
  );

  const pendingCount = payables.filter(
    (item) => String(item.status).toLowerCase() === "pending"
  ).length;

  const partialCount = payables.filter(
    (item) => String(item.status).toLowerCase() === "partial"
  ).length;

  const getStatusClass = (status) => {
    const value = String(status || "").toLowerCase();

    if (value === "partial") return "status-partial";
    if (value === "pending") return "status-pending";
    if (value === "paid" || value === "completed") return "status-paid";

    return "status-unknown";
  };

  return (
    <div className="page-container">
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "25px",
          gap: "20px",
        }}
      >
        <div>
          <p
            style={{
              margin: 0,
              fontSize: "13px",
              fontWeight: "700",
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Factory Management
          </p>

          <h1
            style={{
              margin: "6px 0",
              fontSize: "30px",
              color: "#0f172a",
            }}
          >
            Payables
          </h1>

          <p
            style={{
              margin: 0,
              color: "#64748b",
            }}
          >
            Monitor money payable to suppliers and outstanding purchases.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            border: "1px solid #cbd5e1",
            background: "#ffffff",
            color: "#334155",
            padding: "10px 16px",
            borderRadius: "8px",
            cursor: refreshing ? "not-allowed" : "pointer",
            fontWeight: "600",
          }}
        >
          <RefreshCw
            size={17}
            style={{
              animation: refreshing ? "spin 1s linear infinite" : "none",
            }}
          />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div
          style={{
            marginBottom: "20px",
            padding: "14px 16px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#b91c1c",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <AlertCircle size={19} />
          {error}
        </div>
      )}

      {/* SUMMARY CARDS */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: "18px",
          marginBottom: "25px",
        }}
      >
        <div className="dashboard-card">
          <div style={{ display: "flex", gap: "14px", alignItems: "center" }}>
            <div
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "12px",
                background: "#eff6ff",
                color: "#2563eb",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Wallet size={22} />
            </div>

            <div>
              <small style={{ color: "#64748b" }}>Total Purchases</small>
              <h2 style={{ margin: "4px 0", color: "#0f172a" }}>
                {formatCurrency(totalAmount)}
              </h2>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div style={{ display: "flex", gap: "14px", alignItems: "center" }}>
            <div
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "12px",
                background: "#ecfdf5",
                color: "#059669",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CheckCircle2 size={22} />
            </div>

            <div>
              <small style={{ color: "#64748b" }}>Paid Amount</small>
              <h2 style={{ margin: "4px 0", color: "#0f172a" }}>
                {formatCurrency(paidAmount)}
              </h2>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div style={{ display: "flex", gap: "14px", alignItems: "center" }}>
            <div
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "12px",
                background: "#fff7ed",
                color: "#ea580c",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CircleDollarSign size={22} />
            </div>

            <div>
              <small style={{ color: "#64748b" }}>Outstanding</small>
              <h2 style={{ margin: "4px 0", color: "#0f172a" }}>
                {formatCurrency(payableAmount)}
              </h2>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div style={{ display: "flex", gap: "14px", alignItems: "center" }}>
            <div
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "12px",
                background: "#fef2f2",
                color: "#dc2626",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AlertCircle size={22} />
            </div>

            <div>
              <small style={{ color: "#64748b" }}>Pending Purchases</small>
              <h2 style={{ margin: "4px 0", color: "#0f172a" }}>
                {pendingCount}
              </h2>
              <small style={{ color: "#64748b" }}>
                {partialCount} partial payment(s)
              </small>
            </div>
          </div>
        </div>
      </div>

      {/* TABLE */}
      <div className="dashboard-card">
        <div style={{ marginBottom: "20px" }}>
          <h2 style={{ margin: 0, color: "#0f172a" }}>
            Payable Records
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#64748b",
            }}
          >
            Live payable data from the factory database.
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
            Loading payables...
          </div>
        ) : payables.length === 0 ? (
          <div
            style={{
              padding: "50px",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            No payable records found.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "850px",
              }}
            >
              <thead>
                <tr
                  style={{
                    borderBottom: "1px solid #e2e8f0",
                    textAlign: "left",
                  }}
                >
                  <th style={thStyle}>Purchase ID</th>
                  <th style={thStyle}>Supplier ID</th>
                  <th style={thStyle}>Total Amount</th>
                  <th style={thStyle}>Paid Amount</th>
                  <th style={thStyle}>Payable Amount</th>
                  <th style={thStyle}>Status</th>
                </tr>
              </thead>

              <tbody>
                {payables.map((item) => (
                  <tr
                    key={item.purchase_id}
                    style={{
                      borderBottom: "1px solid #f1f5f9",
                    }}
                  >
                    <td style={tdStyle}>
                      <strong>#{item.purchase_id}</strong>
                    </td>

                    <td style={tdStyle}>
                      #{item.supplier_id}
                    </td>

                    <td style={tdStyle}>
                      {formatCurrency(item.total_amount)}
                    </td>

                    <td style={tdStyle}>
                      {formatCurrency(item.paid_amount)}
                    </td>

                    <td style={tdStyle}>
                      <strong>
                        {formatCurrency(item.payable_amount)}
                      </strong>
                    </td>

                    <td style={tdStyle}>
                      <span
                        className={getStatusClass(item.status)}
                        style={{
                          display: "inline-block",
                          padding: "5px 10px",
                          borderRadius: "20px",
                          fontSize: "12px",
                          fontWeight: "700",
                        }}
                      >
                        {item.status || "Unknown"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        .page-container {
          padding: 30px;
        }

        .dashboard-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 14px;
          padding: 20px;
          box-shadow: 0 4px 15px rgba(15, 23, 42, 0.04);
        }

        .status-pending {
          background: #fff7ed;
          color: #c2410c;
        }

        .status-partial {
          background: #fef3c7;
          color: #92400e;
        }

        .status-paid {
          background: #dcfce7;
          color: #166534;
        }

        .status-unknown {
          background: #f1f5f9;
          color: #475569;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }

          to {
            transform: rotate(360deg);
          }
        }

        @media (max-width: 1000px) {
          .page-container {
            padding: 20px;
          }

          .page-container > div:nth-child(2) {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          }
        }

        @media (max-width: 650px) {
          .page-container > div:nth-child(2) {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}

const thStyle = {
  padding: "13px 12px",
  fontSize: "13px",
  color: "#64748b",
  fontWeight: "700",
  whiteSpace: "nowrap",
};

const tdStyle = {
  padding: "14px 12px",
  fontSize: "14px",
  color: "#334155",
  whiteSpace: "nowrap",
};

export default Payables;