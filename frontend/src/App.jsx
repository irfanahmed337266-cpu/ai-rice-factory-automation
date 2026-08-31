import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Sales from "./pages/Sales";
import Purchases from "./pages/Purchases";
import Stock from "./pages/Stock";
import Production from "./pages/Production";
import Suppliers from "./pages/Suppliers";
import Buyers from "./pages/Buyers";
import Receivables from "./pages/Receivables";
import Payables from "./pages/Payables";
import Reports from "./pages/Reports";
import AIChat from "./pages/AIChat";
import Settings from "./pages/Settings";



function ProtectedLayout({ children }) {
  const token = localStorage.getItem("access_token");
  const location = useLocation();

  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        backgroundColor: "#f8fafc",
      }}
    >
      <Sidebar />

      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Navbar />

        <main
          style={{
            flex: 1,
            minWidth: 0,
            padding: "24px",
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}


function ProtectedRoute({ children }) {
  return (
    <ProtectedLayout>
      {children}
    </ProtectedLayout>
  );
}


function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* =====================================================
            LOGIN
        ====================================================== */}

        <Route
          path="/login"
          element={
            localStorage.getItem("access_token") ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Login />
            )
          }
        />


        {/* =====================================================
            DASHBOARD
        ====================================================== */}

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            SALES
        ====================================================== */}

        <Route
          path="/sales"
          element={
            <ProtectedRoute>
              <Sales />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            PURCHASES
        ====================================================== */}

        <Route
          path="/purchases"
          element={
            <ProtectedRoute>
              <Purchases />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            PRODUCTION
        ====================================================== */}

        <Route
          path="/production"
          element={
            <ProtectedRoute>
              <Production />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            STOCK
        ====================================================== */}

        <Route
          path="/stock"
          element={
            <ProtectedRoute>
              <Stock />
            </ProtectedRoute>
          }
        />

        <Route
          path="/production"
          element={
            <ProtectedRoute>
              <Production />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            SUPPLIERS
        ====================================================== */}

        <Route
          path="/suppliers"
          element={
            <ProtectedRoute>
              <Suppliers />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            BUYERS
        ====================================================== */}

        <Route
          path="/buyers"
          element={
            <ProtectedRoute>
              <Buyers />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            RECEIVABLES
        ====================================================== */}

        <Route
          path="/receivables"
          element={
            <ProtectedRoute>
              <Receivables />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            PAYABLES
        ====================================================== */}

        <Route
          path="/payables"
          element={
            <ProtectedRoute>
              <Payables />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            REPORTS
        ====================================================== */}

        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <Reports />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            AI FACTORY ASSISTANT
        ====================================================== */}

        <Route
          path="/ai-chat"
          element={
            <ProtectedRoute>
              <AIChat />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            SETTINGS
        ====================================================== */}

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />


        {/* =====================================================
            DEFAULT
        ====================================================== */}

        <Route
          path="/"
          element={
            <Navigate to="/dashboard" replace />
          }
        />


        {/* =====================================================
            UNKNOWN ROUTE
        ====================================================== */}

        <Route
          path="*"
          element={
            <Navigate to="/dashboard" replace />
          }
        />

      </Routes>
    </BrowserRouter>
  );
}


export default App;