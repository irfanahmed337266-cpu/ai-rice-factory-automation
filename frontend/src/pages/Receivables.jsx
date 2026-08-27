import { useEffect, useMemo, useState } from "react";
import {
  RefreshCw,
  Wallet,
  TrendingUp,
  CheckCircle,
  Clock,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

function Receivables() {
  const [receivables, setReceivables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const getToken = () => {
    return localStorage.getItem("access_token");
  };

  const fetchReceivables = async () => {
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error("Authentication token not found. Please login again.");
      }

      const response = await fetch(`${API_URL}/receivables/`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Session expired. Please login again.");
        }

        throw new Error(
          data.detail || `Failed to load receivables (${response.status})`
        );
      }

      setReceivables(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load receivables.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReceivables();
  }, []);

  const summary = useMemo(() => {
    return receivables.reduce(
      (acc, item) => {
        acc.total += Number(item.total_amount || 0);
        acc.paid += Number(item.paid_amount || 0);
        acc.receivable += Number(item.receivable_amount || 0);

        if (String(item.status).toLowerCase() === "partial") {
          acc.partial += 1;
        }

        if (String(item.status).toLowerCase() === "pending") {
          acc.pending += 1;
        }

        return acc;
      },
      {
        total: 0,
        paid: 0,
        receivable: 0,
        partial: 0,
        pending: 0,
      }
    );
  }, [receivables]);

  const formatCurrency = (value) => {
    return `Rs. ${Number(value || 0).toLocaleString("en-PK", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const statusClass = (status) => {
    const normalized = String(status || "").toLowerCase();

    if (normalized === "paid") return "status-paid";
    if (normalized === "partial") return "status-partial";

    return "status-pending";
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "30px",
        background: "#f6f8fc",
        color: "#172033",
        boxSizing: "border-box",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "20px",
          marginBottom: "25px",
        }}
      >
        <div>
          <p
            style={{
              margin: "0 0 8px",
              color: "#6366f1",
              fontSize: "11px",
              fontWeight: "800",
              letterSpacing: "0.16em",
            }}
          >
            FACTORY MANAGEMENT
          </p>

          <h1
            style={{
              margin: 0,
              fontSize: "32px",
              fontWeight: "800",
              color: "#111827",
            }}
          >
            Receivables
          </h1>

          <p
            style={{
              margin: "8px 0 0",
              color: "#64748b",
              fontSize: "14px",
            }}
          >
            Monitor money receivable from customers and outstanding sales.
          </p>
        </div>

        <button
          onClick={fetchReceivables}
          disabled={loading}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 15px",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            background: "#ffffff",
            color: "#475569",
            fontWeight: "600",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          <RefreshCw
            size={16}
            style={{
              animation: loading ? "spin 1s linear infinite" : "none",
            }}
          />
          Refresh
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div
          style={{
            marginBottom: "20px",
            padding: "13px 16px",
            borderRadius: "10px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#b91c1c",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {/* SUCCESS */}
      {success && (
        <div
          style={{
            marginBottom: "20px",
            padding: "13px 16px",
            borderRadius: "10px",
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            color: "#15803d",
            fontSize: "14px",
          }}
        >
          {success}
        </div>
      )}

      {/* SUMMARY CARDS */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: "18px",
          marginBottom: "22px",
        }}
      >
        <SummaryCard
          title="Total Sales"
          value={formatCurrency(summary.total)}
          subtitle="Sales on receivable records"
          icon={<TrendingUp size={21} />}
          background="#eef2ff"
          color="#4f46e5"
        />

        <SummaryCard
          title="Paid Amount"
          value={formatCurrency(summary.paid)}
          subtitle="Amount already received"
          icon={<CheckCircle size={21} />}
          background="#ecfdf5"
          color="#059669"
        />

        <SummaryCard
          title="Outstanding"
          value={formatCurrency(summary.receivable)}
          subtitle="Money to receive"
          icon={<Wallet size={21} />}
          background="#fff7ed"
          color="#ea580c"
        />

        <SummaryCard
          title="Pending Sales"
          value={summary.pending}
          subtitle={`${summary.partial} partial payment(s)`}
          icon={<Clock size={21} />}
          background="#f5f3ff"
          color="#7c3aed"
        />
      </div>

      {/* TABLE */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e8ecf3",
          borderRadius: "20px",
          overflow: "hidden",
          boxShadow: "0 10px 35px rgba(15, 23, 42, 0.055)",
        }}
      >
        <div
          style={{
            padding: "22px 24px",
            borderBottom: "1px solid #eef1f6",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "16px",
              color: "#172033",
            }}
          >
            Receivable Records
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#94a3b8",
              fontSize: "12px",
            }}
          >
            Live receivables data from the factory database.
          </p>
        </div>

        {loading ? (
          <div
            style={{
              padding: "60px 20px",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            Loading receivables...
          </div>
        ) : receivables.length === 0 ? (
          <div
            style={{
              padding: "60px 20px",
              textAlign: "center",
              color: "#94a3b8",
            }}
          >
            No receivable records found.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "800px",
              }}
            >
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <TableHeader>Sale ID</TableHeader>
                  <TableHeader>Buyer ID</TableHeader>
                  <TableHeader>Total Amount</TableHeader>
                  <TableHeader>Paid Amount</TableHeader>
                  <TableHeader>Receivable Amount</TableHeader>
                  <TableHeader>Status</TableHeader>
                </tr>
              </thead>

              <tbody>
                {receivables.map((item) => (
                  <tr
                    key={item.sale_id}
                    style={{
                      borderTop: "1px solid #eef1f6",
                    }}
                  >
                    <TableCell>
                      <strong>#{item.sale_id}</strong>
                    </TableCell>

                    <TableCell>#{item.buyer_id}</TableCell>

                    <TableCell>
                      {formatCurrency(item.total_amount)}
                    </TableCell>

                    <TableCell>
                      {formatCurrency(item.paid_amount)}
                    </TableCell>

                    <TableCell>
                      <strong style={{ color: "#ea580c" }}>
                        {formatCurrency(item.receivable_amount)}
                      </strong>
                    </TableCell>

                    <TableCell>
                      <span className={`status-badge ${statusClass(item.status)}`}>
                        {item.status}
                      </span>
                    </TableCell>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          padding: 5px 10px;
          border-radius: 999px;
          font-size: 11px;
          font-weight: 700;
        }

        .status-paid {
          background: #dcfce7;
          color: #15803d;
        }

        .status-partial {
          background: #fef3c7;
          color: #b45309;
        }

        .status-pending {
          background: #fee2e2;
          color: #b91c1c;
        }

        @media (max-width: 1000px) {
          .receivables-page {
            padding: 20px !important;
          }
        }

        @media (max-width: 800px) {
          div[style*="repeat(4, minmax(0, 1fr))"] {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          }
        }

        @media (max-width: 550px) {
          div[style*="repeat(4, minmax(0, 1fr))"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  subtitle,
  icon,
  background,
  color,
}) {
  return (
    <div
      style={{
        minHeight: "130px",
        padding: "20px",
        boxSizing: "border-box",
        border: "1px solid #e8ecf3",
        borderRadius: "18px",
        background: "#ffffff",
        boxShadow: "0 8px 25px rgba(15, 23, 42, 0.045)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "42px",
            height: "42px",
            borderRadius: "12px",
            background,
            color,
          }}
        >
          {icon}
        </div>
      </div>

      <p
        style={{
          margin: "15px 0 5px",
          color: "#64748b",
          fontSize: "12px",
          fontWeight: "600",
        }}
      >
        {title}
      </p>

      <h2
        style={{
          margin: 0,
          color: "#172033",
          fontSize: "20px",
          fontWeight: "800",
        }}
      >
        {value}
      </h2>

      <small
        style={{
          display: "block",
          marginTop: "5px",
          color: "#94a3b8",
          fontSize: "10px",
        }}
      >
        {subtitle}
      </small>
    </div>
  );
}

function TableHeader({ children }) {
  return (
    <th
      style={{
        padding: "14px 18px",
        textAlign: "left",
        color: "#64748b",
        fontSize: "11px",
        fontWeight: "750",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </th>
  );
}

function TableCell({ children }) {
  return (
    <td
      style={{
        padding: "15px 18px",
        color: "#334155",
        fontSize: "12px",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </td>
  );
}

export default Receivables;