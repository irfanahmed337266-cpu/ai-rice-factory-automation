import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function Reports() {
  const [reports, setReports] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReports = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${API_URL}/reports/`);

      if (!response.ok) {
        throw new Error("Failed to load reports");
      }

      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err.message || "Unable to load reports");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const money = (value) =>
    `Rs. ${Number(value || 0).toLocaleString("en-PK", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;

  if (loading) {
    return (
      <div>
        <h1>Reports</h1>
        <p>Loading reports...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1>Reports</h1>

        <p>{error}</p>

        <button onClick={loadReports}>
          Refresh
        </button>
      </div>
    );
  }

  const financial = reports?.financial_summary || {};
  const cashFlow = reports?.cash_flow || {};
  const outstanding = reports?.outstanding || {};
  const operations = reports?.operations || {};

  return (
    <div>
      <h1>Reports</h1>

      <p>
        Factory financial, cash flow and operational reports.
      </p>

      <button onClick={loadReports}>
        Refresh
      </button>

      {/* =====================================================
          FINANCIAL SUMMARY
      ====================================================== */}

      <section>
        <h2>Financial Summary</h2>

        <div>
          <h3>Total Sales</h3>
          <strong>{money(financial.total_sales)}</strong>
        </div>

        <div>
          <h3>Total Purchases</h3>
          <strong>{money(financial.total_purchases)}</strong>
        </div>

        <div>
          <h3>Total COGS</h3>
          <strong>{money(financial.total_cogs)}</strong>
        </div>

        <div>
          <h3>Gross Profit</h3>
          <strong>{money(financial.gross_profit)}</strong>
        </div>

        <div>
          <h3>Total Expenses</h3>
          <strong>{money(financial.total_expenses)}</strong>
        </div>

        <div>
          <h3>Net Profit</h3>
          <strong>{money(financial.net_profit)}</strong>
        </div>

        <div>
          <h3>Profit Margin</h3>
          <strong>
            {Number(financial.profit_margin || 0).toFixed(2)}%
          </strong>
        </div>
      </section>

      {/* =====================================================
          CASH FLOW
      ====================================================== */}

      <section>
        <h2>Cash Flow</h2>

        <div>
          <h3>Customer Payments</h3>
          <strong>{money(cashFlow.customer_payments)}</strong>
        </div>

        <div>
          <h3>Supplier Payments</h3>
          <strong>{money(cashFlow.supplier_payments)}</strong>
        </div>
      </section>

      {/* =====================================================
          OUTSTANDING
      ====================================================== */}

      <section>
        <h2>Outstanding</h2>

        <div>
          <h3>Receivables</h3>
          <strong>{money(outstanding.receivables)}</strong>
        </div>

        <div>
          <h3>Payables</h3>
          <strong>{money(outstanding.payables)}</strong>
        </div>
      </section>

      {/* =====================================================
          OPERATIONS
      ====================================================== */}

      <section>
        <h2>Operations</h2>

        <div>
          <h3>Sales Count</h3>
          <strong>{operations.sales_count || 0}</strong>
        </div>

        <div>
          <h3>Purchases Count</h3>
          <strong>{operations.purchases_count || 0}</strong>
        </div>

        <div>
          <h3>Expenses Count</h3>
          <strong>{operations.expenses_count || 0}</strong>
        </div>

        <div>
          <h3>Total Production</h3>
          <strong>{operations.total_production || 0} kg</strong>
        </div>

        <div>
          <h3>Raw Material Stock</h3>
          <strong>{operations.raw_material_stock || 0} kg</strong>
        </div>

        <div>
          <h3>Finished Product Stock</h3>
          <strong>{operations.finished_product_stock || 0} kg</strong>
        </div>
      </section>
    </div>
  );
}

export default Reports;