import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

const EMPTY_FORM = {
  supplier_id: "",
  material_id: "",
  quantity: "",
  purchase_rate: "",
  transport_cost: "",
  payment_status: "Pending",
  availability_status: "Available",
  status: "Pending",
  notes: "",
};

function Purchases() {
  const [purchases, setPurchases] = useState([]);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const [editingId, setEditingId] = useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({ ...EMPTY_FORM });

  // =========================================================
  // AUTH
  // =========================================================

  const getToken = () => {
    return localStorage.getItem("access_token");
  };

  const getHeaders = () => {
    const token = getToken();

    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  // =========================================================
  // LOAD PURCHASES
  // =========================================================

  const loadPurchases = async () => {
    setLoading(true);
    setError("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const response = await fetch(`${API_URL}/purchases/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Failed to load purchases (${response.status})`
        );
      }

      setPurchases(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Load purchases error:", err);

      setError(
        err?.message || "Failed to load purchases."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPurchases();
  }, []);

  // =========================================================
  // FORM CHANGE
  // =========================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    setError("");
  };

  // =========================================================
  // RESET FORM
  // =========================================================

  const resetForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingId(null);
  };

  // =========================================================
  // EDIT PURCHASE
  // =========================================================

  const startEdit = (purchase) => {
    setError("");
    setSuccess("");

    setEditingId(purchase.id);

    setForm({
      supplier_id: purchase.supplier_id ?? "",
      material_id: purchase.material_id ?? "",
      quantity: purchase.quantity ?? "",
      purchase_rate: purchase.purchase_rate ?? "",
      transport_cost:
        purchase.transport_cost ?? "",
      payment_status:
        purchase.payment_status ?? "Pending",
      availability_status:
        purchase.availability_status ?? "Available",
      status:
        purchase.status ?? "Pending",
      notes: purchase.notes ?? "",
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // =========================================================
  // VALIDATE
  // =========================================================

  const validateForm = () => {
    if (
      form.supplier_id === "" ||
      form.supplier_id === null
    ) {
      throw new Error("Supplier ID is required.");
    }

    if (
      form.material_id === "" ||
      form.material_id === null
    ) {
      throw new Error("Material ID is required.");
    }

    const supplierId = Number(form.supplier_id);
    const materialId = Number(form.material_id);
    const quantity = Number(form.quantity);
    const purchaseRate = Number(form.purchase_rate);

    if (
      !Number.isInteger(supplierId) ||
      supplierId <= 0
    ) {
      throw new Error(
        "Supplier ID must be a valid positive number."
      );
    }

    if (
      !Number.isInteger(materialId) ||
      materialId <= 0
    ) {
      throw new Error(
        "Material ID must be a valid positive number."
      );
    }

    if (
      !Number.isInteger(quantity) ||
      quantity <= 0
    ) {
      throw new Error(
        "Quantity must be a positive whole number."
      );
    }

    if (
      form.purchase_rate === "" ||
      form.purchase_rate === null ||
      form.purchase_rate === undefined
    ) {
      throw new Error(
        "Purchase rate is required."
      );
    }

    if (
      !Number.isFinite(purchaseRate) ||
      purchaseRate < 0
    ) {
      throw new Error(
        "Purchase rate cannot be negative."
      );
    }

    if (form.transport_cost !== "") {
      const transportCost =
        Number(form.transport_cost);

      if (
        !Number.isFinite(transportCost) ||
        transportCost < 0
      ) {
        throw new Error(
          "Transport cost cannot be negative."
        );
      }
    }
  };

  // =========================================================
  // CREATE / UPDATE
  // =========================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      validateForm();

      // =====================================================
      // CREATE
      // =====================================================

      if (editingId === null) {
        const payload = {
          supplier_id: Number(form.supplier_id),
          material_id: Number(form.material_id),
          quantity: Number(form.quantity),
          purchase_rate: Number(form.purchase_rate),

          transport_cost:
            form.transport_cost === ""
              ? 0
              : Number(form.transport_cost),

          payment_status:
            form.payment_status,

          availability_status:
            form.availability_status,

          status: form.status,

          notes:
            form.notes.trim() || null,
        };

        const response = await fetch(
          `${API_URL}/purchases/`,
          {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(payload),
          }
        );

        const data =
          await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              data?.message ||
              `Failed to create purchase (${response.status})`
          );
        }

        setSuccess(
          `Purchase #${
            data?.id ?? ""
          } created successfully.`
        );

        resetForm();

        await loadPurchases();

        return;
      }

      // =====================================================
      // UPDATE
      // =====================================================
      //
      // IMPORTANT:
      // material_id is NOT sent during update.
      //
      // The material remains the same purchase material.
      // Backend is responsible for correcting stock when
      // quantity/rate/availability changes.
      // =====================================================

      const payload = {
        supplier_id: Number(form.supplier_id),
        quantity: Number(form.quantity),
        purchase_rate: Number(form.purchase_rate),

        transport_cost:
          form.transport_cost === ""
            ? 0
            : Number(form.transport_cost),

        payment_status:
          form.payment_status,

        availability_status:
          form.availability_status,

        status: form.status,

        notes:
          form.notes.trim() || null,
      };

      const response = await fetch(
        `${API_URL}/purchases/${editingId}`,
        {
          method: "PUT",
          headers: getHeaders(),
          body: JSON.stringify(payload),
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Failed to update purchase (${response.status})`
        );
      }

      setSuccess(
        `Purchase #${editingId} updated successfully.`
      );

      resetForm();

      await loadPurchases();
    } catch (err) {
      console.error(
        "Purchase save error:",
        err
      );

      setError(
        err?.message ||
          "Failed to save purchase."
      );
    } finally {
      setSaving(false);
    }
  };

  // =========================================================
  // DELETE PURCHASE
  // =========================================================

  const deletePurchase = async (purchase) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete Purchase #${purchase.id}?\n\n` +
        `Quantity: ${purchase.quantity}\n` +
        `Material ID: ${purchase.material_id}\n` +
        `Availability: ${
          purchase.availability_status || "-"
        }\n` +
        `Total: ${formatCurrency(
          purchase.total_amount
        )}\n\n` +
        `The backend will update the associated stock if required.`
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(purchase.id);
    setError("");
    setSuccess("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const response = await fetch(
        `${API_URL}/purchases/${purchase.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Failed to delete purchase (${response.status})`
        );
      }

      const stockRemoved =
        data?.stock_removed;

      if (
        stockRemoved !== undefined &&
        stockRemoved !== null
      ) {
        setSuccess(
          `Purchase #${purchase.id} deleted successfully. ` +
            `Stock removed: ${stockRemoved}.`
        );
      } else {
        setSuccess(
          `Purchase #${purchase.id} deleted successfully.`
        );
      }

      if (editingId === purchase.id) {
        resetForm();
      }

      await loadPurchases();
    } catch (err) {
      console.error(
        "Delete purchase error:",
        err
      );

      setError(
        err?.message ||
          "Failed to delete purchase."
      );
    } finally {
      setDeletingId(null);
    }
  };

  // =========================================================
  // CURRENCY
  // =========================================================

  const formatCurrency = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "-";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "-";
    }

    return `Rs. ${number.toLocaleString(
      "en-PK",
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }
    )}`;
  };

  // =========================================================
  // STATUS BADGE
  // =========================================================

  const statusBadge = (value, type) => {
    let background = "#f1f5f9";
    let color = "#475569";

    if (type === "payment") {
      if (value === "Paid") {
        background = "#dcfce7";
        color = "#166534";
      } else if (value === "Partial") {
        background = "#fef3c7";
        color = "#92400e";
      } else {
        background = "#fee2e2";
        color = "#991b1b";
      }
    }

    if (type === "availability") {
      if (value === "Available") {
        background = "#dcfce7";
        color = "#166534";
      } else {
        background = "#fee2e2";
        color = "#991b1b";
      }
    }

    if (type === "status") {
      if (value === "Completed") {
        background = "#dcfce7";
        color = "#166534";
      } else if (value === "Cancelled") {
        background = "#fee2e2";
        color = "#991b1b";
      } else {
        background = "#fef3c7";
        color = "#92400e";
      }
    }

    return (
      <span
        style={{
          display: "inline-block",
          padding: "5px 9px",
          borderRadius: "999px",
          background,
          color,
          fontSize: "11px",
          fontWeight: "700",
        }}
      >
        {value || "-"}
      </span>
    );
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div
      style={{
        padding: "30px",
        maxWidth: "1500px",
        margin: "0 auto",
        background: "#f6f8fc",
        minHeight: "100vh",
        color: "#172033",
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
          marginBottom: "25px",
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
            }}
          >
            Purchases
          </h1>

          <p
            style={{
              marginTop: "8px",
              color: "#64748b",
            }}
          >
            Manage supplier purchases and raw
            material procurement.
          </p>
        </div>

        <button
          type="button"
          onClick={loadPurchases}
          disabled={loading || saving}
          style={refreshButtonStyle}
        >
          {loading
            ? "Refreshing..."
            : "Refresh"}
        </button>
      </div>

      {/* =====================================================
          MESSAGES
      ===================================================== */}

      {error && (
        <div style={errorStyle}>
          {error}
        </div>
      )}

      {success && (
        <div style={successStyle}>
          {success}
        </div>
      )}

      {/* =====================================================
          FORM
      ===================================================== */}

      <div style={cardStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px",
            gap: "15px",
          }}
        >
          <h2
            style={{
              margin: 0,
              color: "#172033",
              fontSize: "18px",
            }}
          >
            {editingId !== null
              ? `Edit Purchase #${editingId}`
              : "Create New Purchase"}
          </h2>

          {editingId !== null && (
            <button
              type="button"
              onClick={() => {
                resetForm();
                setError("");
                setSuccess("");
              }}
              style={cancelButtonStyle}
            >
              Cancel Edit
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "16px",
            }}
          >
            {/* SUPPLIER */}

            <div>
              <label>Supplier ID</label>

              <input
                type="number"
                name="supplier_id"
                value={form.supplier_id}
                onChange={handleChange}
                required
                min="1"
                step="1"
                placeholder="e.g. 1"
              />
            </div>

            {/* MATERIAL */}

            <div>
              <label>
                Material ID

                {editingId !== null && (
                  <span
                    style={{
                      color: "#64748b",
                      fontWeight: "400",
                      marginLeft: "5px",
                    }}
                  >
                    (cannot change)
                  </span>
                )}
              </label>

              <input
                type="number"
                name="material_id"
                value={form.material_id}
                onChange={handleChange}
                required
                min="1"
                step="1"
                disabled={editingId !== null}
                placeholder="e.g. 1"
              />
            </div>

            {/* QUANTITY */}

            <div>
              <label>Quantity</label>

              <input
                type="number"
                name="quantity"
                value={form.quantity}
                onChange={handleChange}
                required
                min="1"
                step="1"
                placeholder="e.g. 100"
              />
            </div>

            {/* PURCHASE RATE */}

            <div>
              <label>Purchase Rate</label>

              <input
                type="number"
                name="purchase_rate"
                value={form.purchase_rate}
                onChange={handleChange}
                required
                min="0"
                step="0.01"
                placeholder="e.g. 250"
              />
            </div>

            {/* TRANSPORT */}

            <div>
              <label>Transport Cost</label>

              <input
                type="number"
                name="transport_cost"
                value={form.transport_cost}
                onChange={handleChange}
                min="0"
                step="0.01"
                placeholder="e.g. 500"
              />
            </div>

            {/* PAYMENT */}

            <div>
              <label>Payment Status</label>

              <select
                name="payment_status"
                value={form.payment_status}
                onChange={handleChange}
              >
                <option value="Pending">
                  Pending
                </option>

                <option value="Partial">
                  Partial
                </option>

                <option value="Paid">
                  Paid
                </option>
              </select>
            </div>

            {/* AVAILABILITY */}

            <div>
              <label>
                Availability Status
              </label>

              <select
                name="availability_status"
                value={
                  form.availability_status
                }
                onChange={handleChange}
              >
                <option value="Available">
                  Available
                </option>

                <option value="Unavailable">
                  Unavailable
                </option>
              </select>
            </div>

            {/* STATUS */}

            <div>
              <label>Status</label>

              <select
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="Pending">
                  Pending
                </option>

                <option value="Completed">
                  Completed
                </option>

                <option value="Cancelled">
                  Cancelled
                </option>
              </select>
            </div>
          </div>

          {/* NOTES */}

          <div
            style={{
              marginTop: "16px",
            }}
          >
            <label>Notes</label>

            <textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              rows="3"
              placeholder="Purchase notes..."
            />
          </div>

          {/* BUTTONS */}

          <div
            style={{
              display: "flex",
              gap: "10px",
              marginTop: "18px",
            }}
          >
            <button
              type="submit"
              disabled={saving || deletingId !== null}
              style={{
                padding: "12px 22px",
                border: "none",
                borderRadius: "9px",
                background: saving
                  ? "#94a3b8"
                  : "#4f46e5",
                color: "#ffffff",
                fontWeight: "700",
                cursor: saving
                  ? "not-allowed"
                  : "pointer",
              }}
            >
              {saving
                ? editingId !== null
                  ? "Updating..."
                  : "Creating..."
                : editingId !== null
                ? "Update Purchase"
                : "Create Purchase"}
            </button>

            {editingId !== null && (
              <button
                type="button"
                onClick={resetForm}
                disabled={saving}
                style={cancelButtonStyle}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* =====================================================
          PURCHASE TABLE
      ===================================================== */}

      <div style={cardStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingBottom: "20px",
            borderBottom:
              "1px solid #eef1f6",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "18px",
              color: "#172033",
            }}
          >
            Purchase Transactions
          </h2>

          <span
            style={{
              color: "#64748b",
              fontSize: "13px",
              fontWeight: "600",
            }}
          >
            {purchases.length}{" "}
            {purchases.length === 1
              ? "purchase"
              : "purchases"}
          </span>
        </div>

        {loading &&
        purchases.length === 0 ? (
          <div style={emptyStyle}>
            Loading purchases...
          </div>
        ) : purchases.length === 0 ? (
          <div style={emptyStyle}>
            No purchases found.
          </div>
        ) : (
          <div
            style={{
              overflowX: "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "1250px",
              }}
            >
              <thead>
                <tr
                  style={{
                    background: "#f8fafc",
                  }}
                >
                  <th>ID</th>
                  <th>Supplier</th>
                  <th>Material</th>
                  <th>Quantity</th>
                  <th>Purchase Rate</th>
                  <th>Transport</th>
                  <th>Total</th>
                  <th>Payment</th>
                  <th>Availability</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {purchases.map((purchase) => (
                  <tr
                    key={purchase.id}
                  >
                    <td>
                      <strong>
                        #{purchase.id}
                      </strong>
                    </td>

                    <td>
                      {purchase.supplier_id ??
                        "-"}
                    </td>

                    <td>
                      {purchase.material_id ??
                        "-"}
                    </td>

                    <td>
                      <strong>
                        {purchase.quantity ??
                          "-"}
                      </strong>
                    </td>

                    <td>
                      {formatCurrency(
                        purchase.purchase_rate
                      )}
                    </td>

                    <td>
                      {formatCurrency(
                        purchase.transport_cost
                      )}
                    </td>

                    <td>
                      <strong>
                        {formatCurrency(
                          purchase.total_amount
                        )}
                      </strong>
                    </td>

                    <td>
                      {statusBadge(
                        purchase.payment_status,
                        "payment"
                      )}
                    </td>

                    <td>
                      {statusBadge(
                        purchase.availability_status,
                        "availability"
                      )}
                    </td>

                    <td>
                      {statusBadge(
                        purchase.status,
                        "status"
                      )}
                    </td>

                    <td>
                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          alignItems:
                            "center",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() =>
                            startEdit(
                              purchase
                            )
                          }
                          disabled={
                            saving ||
                            deletingId !==
                              null
                          }
                          style={
                            editButtonStyle
                          }
                        >
                          ✏️ Edit
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            deletePurchase(
                              purchase
                            )
                          }
                          disabled={
                            saving ||
                            deletingId !==
                              null
                          }
                          style={
                            deleteButtonStyle
                          }
                        >
                          {deletingId ===
                          purchase.id
                            ? "Deleting..."
                            : "🗑️ Delete"}
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

      {/* =====================================================
          LOCAL STYLES
      ===================================================== */}

      <style>{`
        label {
          display: block;
          margin-bottom: 7px;
          color: #334155;
          font-size: 13px;
          font-weight: 600;
        }

        input,
        select,
        textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 11px 12px;
          border: 1px solid #cbd5e1;
          border-radius: 8px;
          background: #ffffff;
          color: #172033;
          font-size: 14px;
          outline: none;
        }

        input:focus,
        select:focus,
        textarea:focus {
          border-color: #6366f1;
          box-shadow:
            0 0 0 3px
            rgba(99, 102, 241, 0.10);
        }

        input:disabled {
          background: #f1f5f9;
          color: #64748b;
          cursor: not-allowed;
        }

        th {
          padding: 13px 14px;
          text-align: left;
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }

        td {
          padding: 14px;
          border-top:
            1px solid #eef1f6;
          color: #334155;
          font-size: 13px;
          white-space: nowrap;
        }

        tbody tr:hover {
          background: #fafbff;
        }

        button {
          transition:
            opacity 0.15s ease,
            transform 0.15s ease;
        }

        button:hover:not(:disabled) {
          transform: translateY(-1px);
        }

        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}

// =========================================================
// STYLES
// =========================================================

const cardStyle = {
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: "16px",
  padding: "24px",
  marginBottom: "25px",
  boxShadow:
    "0 8px 25px rgba(15,23,42,0.05)",
};

const refreshButtonStyle = {
  padding: "10px 16px",
  border: "1px solid #e2e8f0",
  borderRadius: "9px",
  background: "#ffffff",
  color: "#334155",
  cursor: "pointer",
  fontWeight: "600",
};

const cancelButtonStyle = {
  padding: "10px 16px",
  border: "1px solid #cbd5e1",
  borderRadius: "9px",
  background: "#ffffff",
  color: "#475569",
  cursor: "pointer",
  fontWeight: "600",
};

const editButtonStyle = {
  padding: "8px 12px",
  border: "1px solid #c7d2fe",
  borderRadius: "7px",
  background: "#eef2ff",
  color: "#4338ca",
  cursor: "pointer",
  fontWeight: "700",
  fontSize: "12px",
};

const deleteButtonStyle = {
  padding: "8px 12px",
  border: "1px solid #fecaca",
  borderRadius: "7px",
  background: "#fef2f2",
  color: "#b91c1c",
  cursor: "pointer",
  fontWeight: "700",
  fontSize: "12px",
};

const errorStyle = {
  marginBottom: "20px",
  padding: "13px 15px",
  borderRadius: "9px",
  background: "#fef2f2",
  border: "1px solid #fecaca",
  color: "#b91c1c",
};

const successStyle = {
  marginBottom: "20px",
  padding: "13px 15px",
  borderRadius: "9px",
  background: "#f0fdf4",
  border: "1px solid #bbf7d0",
  color: "#15803d",
};

const emptyStyle = {
  padding: "40px",
  textAlign: "center",
  color: "#64748b",
};

export default Purchases;