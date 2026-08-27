import { useEffect, useState } from "react";
import {
  Package,
  RefreshCw,
  TrendingUp,
  Database,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

function Stock() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // =========================================================
  // GET AUTH TOKEN
  // =========================================================

  const getToken = () => {
    return localStorage.getItem("access_token");
  };

  // =========================================================
  // LOAD INVENTORY
  // =========================================================

  const loadInventory = async () => {
    setLoading(true);
    setError("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const response = await fetch(`${API_URL}/inventory/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            `Failed to load inventory (${response.status})`
        );
      }

      setInventory(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load inventory");
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {
    loadInventory();
  }, []);

  // =========================================================
  // CALCULATIONS
  // =========================================================

  const totalQuantity = inventory.reduce(
    (sum, item) => sum + Number(item.quantity || 0),
    0
  );

  const totalStockValue = inventory.reduce(
    (sum, item) => sum + Number(item.stock_value || 0),
    0
  );

  const totalMaterials = inventory.length;

  const averageStockRate =
    totalQuantity > 0
      ? totalStockValue / totalQuantity
      : 0;

  // =========================================================
  // FORMAT NUMBER
  // =========================================================

  const formatNumber = (value, decimals = 0) => {
    const number = Number(value || 0);

    return number.toLocaleString("en-PK", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatCurrency = (value) => {
    return `Rs. ${formatNumber(value, 2)}`;
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div
      style={{
        padding: "30px",
        maxWidth: "1400px",
        margin: "0 auto",
      }}
    >
      {/* =====================================================
          HEADER
      ===================================================== */}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "20px",
          marginBottom: "28px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p
            style={{
              margin: "0 0 6px",
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
              color: "#111827",
              fontSize: "30px",
              fontWeight: "800",
            }}
          >
            Stock
          </h1>

          <p
            style={{
              marginTop: "8px",
              marginBottom: 0,
              color: "#64748b",
              fontSize: "14px",
            }}
          >
            Monitor raw material inventory and stock valuation.
          </p>
        </div>

        <button
          onClick={loadInventory}
          disabled={loading}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 16px",
            border: "1px solid #e2e8f0",
            borderRadius: "9px",
            background: "#ffffff",
            color: "#334155",
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: "600",
          }}
        >
          <RefreshCw
            size={16}
            style={{
              animation: loading
                ? "spin 1s linear infinite"
                : "none",
            }}
          />

          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <div
          style={{
            marginBottom: "20px",
            padding: "14px 16px",
            borderRadius: "9px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#b91c1c",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {/* =====================================================
          SUMMARY CARDS
      ===================================================== */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "18px",
          marginBottom: "24px",
        }}
      >
        {/* Total Quantity */}

        <div className="stock-summary-card">
          <div className="summary-icon blue">
            <Package size={21} />
          </div>

          <div>
            <p>Total Stock</p>

            <h2>
              {formatNumber(totalQuantity)} kg
            </h2>

            <span>Current inventory quantity</span>
          </div>
        </div>

        {/* Stock Value */}

        <div className="stock-summary-card">
          <div className="summary-icon purple">
            <TrendingUp size={21} />
          </div>

          <div>
            <p>Stock Value</p>

            <h2>
              {formatCurrency(totalStockValue)}
            </h2>

            <span>Total inventory valuation</span>
          </div>
        </div>

        {/* Materials */}

        <div className="stock-summary-card">
          <div className="summary-icon green">
            <Database size={21} />
          </div>

          <div>
            <p>Materials</p>

            <h2>{totalMaterials}</h2>

            <span>Inventory material records</span>
          </div>
        </div>

        {/* Average Rate */}

        <div className="stock-summary-card">
          <div className="summary-icon orange">
            <TrendingUp size={21} />
          </div>

          <div>
            <p>Average Rate</p>

            <h2>
              {formatCurrency(averageStockRate)}
            </h2>

            <span>Average stock rate per kg</span>
          </div>
        </div>
      </div>

      {/* =====================================================
          INVENTORY TABLE
      ===================================================== */}

      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow:
            "0 8px 25px rgba(15,23,42,0.05)",
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
              fontSize: "18px",
              color: "#172033",
            }}
          >
            Inventory Records
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#94a3b8",
              fontSize: "12px",
            }}
          >
            Live inventory data from the factory database.
          </p>
        </div>

        {loading && inventory.length === 0 ? (
          <div
            style={{
              padding: "45px",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            Loading inventory...
          </div>
        ) : inventory.length === 0 ? (
          <div
            style={{
              padding: "45px",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            No inventory records found.
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
                    background: "#f8fafc",
                  }}
                >
                  <th>ID</th>
                  <th>Material ID</th>
                  <th>Quantity</th>
                  <th>Average Rate</th>
                  <th>Stock Value</th>
                  <th>Last Updated</th>
                </tr>
              </thead>

              <tbody>
                {inventory.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>

                    <td>
                      <span className="material-badge">
                        Material #{item.material_id}
                      </span>
                    </td>

                    <td>
                      <strong>
                        {formatNumber(item.quantity)} kg
                      </strong>
                    </td>

                    <td>
                      {formatCurrency(item.average_rate)}
                    </td>

                    <td>
                      <strong>
                        {formatCurrency(item.stock_value)}
                      </strong>
                    </td>

                    <td>
                      {item.updated_at
                        ? new Date(
                            item.updated_at
                          ).toLocaleString()
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* =====================================================
          STYLES
      ===================================================== */}

      <style>{`
        .stock-summary-card {
          display: flex;
          align-items: center;
          gap: 14px;
          min-height: 105px;
          padding: 20px;
          box-sizing: border-box;
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          box-shadow: 0 8px 25px rgba(15,23,42,0.05);
        }

        .stock-summary-card p {
          margin: 0 0 5px;
          color: #64748b;
          font-size: 12px;
          font-weight: 600;
        }

        .stock-summary-card h2 {
          margin: 0;
          color: #172033;
          font-size: 20px;
          font-weight: 800;
        }

        .stock-summary-card span {
          display: block;
          margin-top: 4px;
          color: #94a3b8;
          font-size: 10px;
        }

        .summary-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 44px;
          height: 44px;
          border-radius: 12px;
        }

        .summary-icon.blue {
          color: #2563eb;
          background: #eff6ff;
        }

        .summary-icon.purple {
          color: #7c3aed;
          background: #f5f3ff;
        }

        .summary-icon.green {
          color: #059669;
          background: #ecfdf5;
        }

        .summary-icon.orange {
          color: #ea580c;
          background: #fff7ed;
        }

        th {
          padding: 14px;
          text-align: left;
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }

        td {
          padding: 15px 14px;
          border-top: 1px solid #eef1f6;
          color: #334155;
          font-size: 13px;
          white-space: nowrap;
        }

        tbody tr:hover {
          background: #fafbff;
        }

        .material-badge {
          display: inline-block;
          padding: 5px 9px;
          border-radius: 7px;
          background: #eef2ff;
          color: #4f46e5;
          font-size: 11px;
          font-weight: 700;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }

          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}

export default Stock;