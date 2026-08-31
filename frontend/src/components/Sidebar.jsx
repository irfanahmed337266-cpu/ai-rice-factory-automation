import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Warehouse,
  Truck,
  Users,
  ArrowDownToLine,
  ArrowUpFromLine,
  FileBarChart,
  MessageSquare,
  Settings,
  LogOut,
  Sparkles,
  Factory,
} from "lucide-react";

import { NavLink, useNavigate } from "react-router-dom";

function Sidebar() {
  const navigate = useNavigate();

  const menuItems = [
    { title: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { title: "Sales", path: "/sales", icon: ShoppingCart },
    { title: "Purchases", path: "/purchases", icon: Package },
    { title: "Stock", path: "/stock", icon: Warehouse },
    { title: "Production", path: "/production", icon: Factory },
    { title: "Suppliers", path: "/suppliers", icon: Truck },
    { title: "Buyers", path: "/buyers", icon: Users },
    { title: "Receivables", path: "/receivables", icon: ArrowDownToLine },
    { title: "Payables", path: "/payables", icon: ArrowUpFromLine },
    { title: "Reports", path: "/reports", icon: FileBarChart },
    { title: "AI Assistant", path: "/ai-chat", icon: MessageSquare },
  ];

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login", { replace: true });
  };

  return (
    <aside
      style={{
        width: "260px",
        minHeight: "100vh",
        background:
          "linear-gradient(180deg, #111827 0%, #172554 55%, #1e1b4b 100%)",
        color: "#ffffff",
        display: "flex",
        flexDirection: "column",
        padding: "22px 14px",
        boxSizing: "border-box",
        boxShadow: "4px 0 20px rgba(15, 23, 42, 0.12)",
        position: "sticky",
        top: 0,
        left: 0,
        flexShrink: 0,
      }}
    >
      {/* BRAND */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          padding: "4px 10px 24px",
          borderBottom: "1px solid rgba(255,255,255,0.10)",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            width: "42px",
            height: "42px",
            borderRadius: "12px",
            background: "linear-gradient(135deg, #22c55e, #06b6d4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 8px 20px rgba(34,197,94,0.25)",
          }}
        >
          <Sparkles size={23} strokeWidth={2.3} />
        </div>

        <div>
          <div
            style={{
              fontSize: "17px",
              fontWeight: "800",
              letterSpacing: "-0.3px",
            }}
          >
            AI Rice Factory
          </div>

          <div
            style={{
              fontSize: "11px",
              color: "#94a3b8",
              marginTop: "3px",
            }}
          >
            Intelligent Management
          </div>
        </div>
      </div>

      {/* SECTION TITLE */}
      <div
        style={{
          fontSize: "10px",
          fontWeight: "700",
          color: "#64748b",
          letterSpacing: "1.2px",
          padding: "0 12px 10px",
          textTransform: "uppercase",
        }}
      >
        Main Menu
      </div>

      {/* MENU */}
      <nav
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "5px",
        }}
      >
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "11px 12px",
                borderRadius: "10px",
                textDecoration: "none",
                color: isActive ? "#ffffff" : "#cbd5e1",
                background: isActive
                  ? "linear-gradient(90deg, #2563eb, #4f46e5)"
                  : "transparent",
                fontSize: "14px",
                fontWeight: isActive ? "700" : "500",
                transition: "all 0.2s ease",
                boxShadow: isActive
                  ? "0 6px 18px rgba(37,99,235,0.25)"
                  : "none",
              })}
            >
              <Icon size={19} strokeWidth={2} />
              <span>{item.title}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* SPACER */}
      <div style={{ flex: 1 }} />

      {/* AI STATUS */}
      <div
        style={{
          margin: "12px 4px",
          padding: "14px",
          borderRadius: "12px",
          background:
            "linear-gradient(135deg, rgba(34,197,94,0.14), rgba(6,182,212,0.14))",
          border: "1px solid rgba(148,163,184,0.12)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "7px",
          }}
        >
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: "#22c55e",
              boxShadow: "0 0 10px #22c55e",
            }}
          />

          <span
            style={{
              fontSize: "12px",
              fontWeight: "700",
              color: "#e2e8f0",
            }}
          >
            AI System Online
          </span>
        </div>

        <div
          style={{
            fontSize: "11px",
            color: "#94a3b8",
            lineHeight: "1.5",
          }}
        >
          Factory intelligence is ready.
        </div>
      </div>

      {/* BOTTOM MENU */}
      <div
        style={{
          borderTop: "1px solid rgba(255,255,255,0.10)",
          paddingTop: "12px",
        }}
      >
        <NavLink
          to="/settings"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "10px 12px",
            color: "#94a3b8",
            textDecoration: "none",
            fontSize: "13px",
            borderRadius: "8px",
          }}
        >
          <Settings size={18} />
          Settings
        </NavLink>

        <button
          type="button"
          onClick={handleLogout}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "10px 12px",
            marginTop: "2px",
            border: "none",
            background: "transparent",
            color: "#94a3b8",
            fontSize: "13px",
            cursor: "pointer",
            textAlign: "left",
            borderRadius: "8px",
          }}
          onMouseEnter={(event) => {
            event.currentTarget.style.background =
              "rgba(255,255,255,0.06)";
            event.currentTarget.style.color = "#ffffff";
          }}
          onMouseLeave={(event) => {
            event.currentTarget.style.background = "transparent";
            event.currentTarget.style.color = "#94a3b8";
          }}
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;