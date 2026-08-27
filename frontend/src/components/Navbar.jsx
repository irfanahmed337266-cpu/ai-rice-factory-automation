function Navbar() {
  const username = localStorage.getItem("username") || "User";
  const role = localStorage.getItem("role") || "";

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    localStorage.removeItem("role");

    window.location.href = "/login";
  };

  return (
    <header
      style={{
        height: "64px",
        backgroundColor: "#ffffff",
        borderBottom: "1px solid #e2e8f0",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
      }}
    >
      <div>
        <h2
          style={{
            margin: 0,
            fontSize: "20px",
            color: "#0f172a",
          }}
        >
          AI Rice Factory Automation
        </h2>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "16px",
        }}
      >
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontWeight: "600",
              color: "#0f172a",
            }}
          >
            {username}
          </div>

          <div
            style={{
              fontSize: "12px",
              color: "#64748b",
              textTransform: "capitalize",
            }}
          >
            {role}
          </div>
        </div>

        <button
          onClick={handleLogout}
          style={{
            border: "1px solid #cbd5e1",
            background: "#ffffff",
            color: "#334155",
            padding: "8px 14px",
            borderRadius: "7px",
            cursor: "pointer",
            fontWeight: "600",
          }}
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default Navbar;