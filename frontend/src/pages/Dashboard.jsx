import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import StatCard from "../components/StatCard";

import {
  TrendingUp,
  ShoppingCart,
  Wallet,
  Package,
  Users,
  Truck,
  Bot,
  ArrowUpRight,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

import "./Dashboard.css";

const API_URL = "http://127.0.0.1:8000";

function Dashboard() {
  const navigate = useNavigate();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("access_token");

      if (!token) {
        navigate("/login");
        return;
      }

      const response = await fetch(`${API_URL}/dashboard/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401 || response.status === 403) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("token_type");
        localStorage.removeItem("user_id");
        localStorage.removeItem("username");
        localStorage.removeItem("role");

        navigate("/login");
        return;
      }

      if (!response.ok) {
        throw new Error(`Dashboard request failed: ${response.status}`);
      }

      const data = await response.json();

      setDashboard(data);
    } catch (err) {
      console.error("Dashboard error:", err);
      setError("Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const formatCurrency = (value) => {
    const number = Number(value || 0);

    return `Rs. ${number.toLocaleString("en-PK", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    })}`;
  };

  const formatNumber = (value) => {
    return Number(value || 0).toLocaleString("en-PK");
  };

  const totalStock =
    Number(dashboard?.raw_material_stock || 0) +
    Number(dashboard?.finished_product_stock || 0);

  const inventoryPercentage =
    totalStock > 0
      ? Math.min(
          Math.round(
            (Number(dashboard?.finished_product_stock || 0) / totalStock) *
              100
          ),
          100
        )
      : 0;

  return (
    <div className="dashboard-page">

      {/* =====================================================
          TOP HEADER
          ===================================================== */}

      <div className="dashboard-top">

        <div>
          <p className="dashboard-label">FACTORY OVERVIEW</p>

          <h1>
            Welcome back, <span>Factory Owner</span> 👋
          </h1>

          <p className="dashboard-subtitle">
            Monitor your rice factory operations, sales, purchases and
            financial performance from one place.
          </p>
        </div>

        <div className="ai-online">

          <div className="ai-online-icon">
            <Bot size={20} />
          </div>

          <div>
            <strong>AI System Online</strong>
            <small>Factory intelligence is ready</small>
          </div>

          <span className="online-indicator"></span>

        </div>

      </div>


      {/* =====================================================
          LOADING
          ===================================================== */}

      {loading && (
        <div
          style={{
            padding: "18px",
            marginBottom: "20px",
            borderRadius: "14px",
            background: "#eef2ff",
            color: "#4f46e5",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <RefreshCw size={18} />
          Loading factory data...
        </div>
      )}


      {/* =====================================================
          ERROR
          ===================================================== */}

      {error && !loading && (
        <div
          style={{
            padding: "18px",
            marginBottom: "20px",
            borderRadius: "14px",
            background: "#fef2f2",
            color: "#b91c1c",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "15px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <AlertCircle size={18} />
            {error}
          </div>

          <button
            onClick={fetchDashboard}
            style={{
              border: "1px solid #fecaca",
              background: "#ffffff",
              color: "#b91c1c",
              padding: "8px 12px",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
            }}
          >
            Retry
          </button>
        </div>
      )}


      {/* =====================================================
          STAT CARDS
          ===================================================== */}

      <div className="stats-grid">

        <StatCard
          title="Total Sales"
          value={formatCurrency(dashboard?.total_sales)}
          subtitle="Total sales revenue"
          icon={<TrendingUp size={21} />}
          gradient="from-blue-500 to-indigo-600"
        />

        <StatCard
          title="Total Purchases"
          value={formatCurrency(dashboard?.total_purchases)}
          subtitle="Total purchase cost"
          icon={<ShoppingCart size={21} />}
          gradient="from-violet-500 to-purple-700"
        />

        <StatCard
          title="Receivables"
          value={formatCurrency(dashboard?.total_receivables)}
          subtitle="Money to receive"
          icon={<Wallet size={21} />}
          gradient="from-emerald-500 to-teal-600"
        />

        <StatCard
          title="Payables"
          value={formatCurrency(dashboard?.total_payables)}
          subtitle="Money owed to suppliers"
          icon={<Package size={21} />}
          gradient="from-orange-500 to-red-500"
        />

      </div>


      {/* =====================================================
          MAIN GRID
          ===================================================== */}

      <div className="dashboard-main-grid">

        {/* ===================================================
            SALES / PROFIT OVERVIEW
            =================================================== */}

        <div className="dashboard-card sales-card">

          <div className="card-heading">

            <div>
              <h2>Financial Overview</h2>

              <p>
                Current factory financial performance
              </p>
            </div>

            <button onClick={fetchDashboard}>
              Refresh
            </button>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: "16px",
              padding: "24px",
            }}
          >

            <div
              style={{
                padding: "18px",
                borderRadius: "14px",
                background: "#f8fafc",
              }}
            >
              <small
                style={{
                  color: "#94a3b8",
                  display: "block",
                  marginBottom: "7px",
                }}
              >
                Gross Profit
              </small>

              <strong
                style={{
                  fontSize: "21px",
                  color: "#16a34a",
                }}
              >
                {formatCurrency(dashboard?.gross_profit)}
              </strong>
            </div>


            <div
              style={{
                padding: "18px",
                borderRadius: "14px",
                background: "#f8fafc",
              }}
            >
              <small
                style={{
                  color: "#94a3b8",
                  display: "block",
                  marginBottom: "7px",
                }}
              >
                Net Profit
              </small>

              <strong
                style={{
                  fontSize: "21px",
                  color:
                    Number(dashboard?.net_profit || 0) >= 0
                      ? "#16a34a"
                      : "#dc2626",
                }}
              >
                {formatCurrency(dashboard?.net_profit)}
              </strong>
            </div>


            <div
              style={{
                padding: "18px",
                borderRadius: "14px",
                background: "#f8fafc",
              }}
            >
              <small
                style={{
                  color: "#94a3b8",
                  display: "block",
                  marginBottom: "7px",
                }}
              >
                Cash Received
              </small>

              <strong
                style={{
                  fontSize: "21px",
                  color: "#2563eb",
                }}
              >
                {formatCurrency(dashboard?.total_received)}
              </strong>
            </div>


            <div
              style={{
                padding: "18px",
                borderRadius: "14px",
                background: "#f8fafc",
              }}
            >
              <small
                style={{
                  color: "#94a3b8",
                  display: "block",
                  marginBottom: "7px",
                }}
              >
                Expenses
              </small>

              <strong
                style={{
                  fontSize: "21px",
                  color: "#dc2626",
                }}
              >
                {formatCurrency(dashboard?.total_expenses)}
              </strong>
            </div>

          </div>

        </div>


        {/* ===================================================
            STOCK OVERVIEW
            =================================================== */}

        <div className="dashboard-card">

          <div className="card-heading">

            <div>
              <h2>Stock Overview</h2>
              <p>Current inventory status</p>
            </div>

            <Package size={21} />

          </div>


          <div className="stock-items">

            {/* RAW MATERIAL */}

            <div className="stock-item">

              <div className="stock-left">

                <div className="stock-icon blue">
                  <Package size={18} />
                </div>

                <div>
                  <strong>Raw Material</strong>

                  <small>
                    Rice materials
                  </small>
                </div>

              </div>

              <strong>
                {formatNumber(dashboard?.raw_material_stock)} kg
              </strong>

            </div>


            {/* FINISHED PRODUCT */}

            <div className="stock-item">

              <div className="stock-left">

                <div className="stock-icon purple">
                  <Package size={18} />
                </div>

                <div>
                  <strong>Finished Product</strong>

                  <small>
                    Ready stock
                  </small>
                </div>

              </div>

              <strong>
                {formatNumber(dashboard?.finished_product_stock)} kg
              </strong>

            </div>


            {/* INVENTORY PROGRESS */}

            <div className="stock-progress">

              <div className="progress-header">

                <span>
                  Inventory Distribution
                </span>

                <strong>
                  {inventoryPercentage}%
                </strong>

              </div>

              <div className="progress-bar">
                <div
                  style={{
                    width: `${inventoryPercentage}%`,
                  }}
                ></div>
              </div>

            </div>

          </div>

        </div>

      </div>


      {/* =====================================================
          FACTORY SUMMARY
          ===================================================== */}

      <div className="dashboard-bottom-grid">

        {/* FACTORY PERFORMANCE */}

        <div className="dashboard-card">

          <div className="card-heading">

            <div>
              <h2>Factory Performance</h2>

              <p>
                Overall operational summary
              </p>
            </div>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: "14px",
              padding: "20px 24px 24px",
            }}
          >

            <div
              style={{
                padding: "16px",
                borderRadius: "13px",
                background: "#f8fafc",
              }}
            >
              <small style={{ color: "#94a3b8" }}>
                Total COGS
              </small>

              <strong
                style={{
                  display: "block",
                  marginTop: "7px",
                  color: "#334155",
                  fontSize: "18px",
                }}
              >
                {formatCurrency(dashboard?.total_cogs)}
              </strong>
            </div>


            <div
              style={{
                padding: "16px",
                borderRadius: "13px",
                background: "#f8fafc",
              }}
            >
              <small style={{ color: "#94a3b8" }}>
                Production
              </small>

              <strong
                style={{
                  display: "block",
                  marginTop: "7px",
                  color: "#334155",
                  fontSize: "18px",
                }}
              >
                {formatNumber(dashboard?.total_production)} kg
              </strong>
            </div>

          </div>

        </div>


        {/* QUICK ACTIONS */}

        <div className="dashboard-card">

          <div className="card-heading">

            <div>
              <h2>Quick Actions</h2>

              <p>
                Frequently used operations
              </p>
            </div>

          </div>


          <div className="quick-actions">

            <button onClick={() => navigate("/sales")}>
              <TrendingUp size={19} />
              <span>New Sale</span>
            </button>


            <button onClick={() => navigate("/purchases")}>
              <ShoppingCart size={19} />
              <span>New Purchase</span>
            </button>


            <button onClick={() => navigate("/buyers")}>
              <Users size={19} />
              <span>Add Buyer</span>
            </button>


            <button onClick={() => navigate("/suppliers")}>
              <Truck size={19} />
              <span>Add Supplier</span>
            </button>

          </div>

        </div>

      </div>


      {/* =====================================================
          AI ASSISTANT BANNER
          ===================================================== */}

      <div className="ai-banner">

        <div className="ai-banner-icon">
          <Bot size={24} />
        </div>


        <div className="ai-banner-content">

          <strong>
            AI Factory Assistant
          </strong>

          <p>
            Ask about sales, purchases, stock, profit,
            receivables, payables and factory performance.
          </p>

        </div>


        <button
          onClick={() => navigate("/ai-chat")}
        >
          Open AI Assistant
          <ArrowUpRight size={16} />
        </button>

      </div>

    </div>
  );
}

export default Dashboard;