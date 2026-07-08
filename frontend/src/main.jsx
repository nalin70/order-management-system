import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Boxes,
  CreditCard,
  LogOut,
  PackagePlus,
  RefreshCcw,
  Shield,
  ShoppingCart,
  Users,
} from "lucide-react";

import { apiRequest, normalizeList, storage } from "./api";
import "./styles.css";

const initialUser = () => {
  const stored = localStorage.getItem("user");
  return stored ? JSON.parse(stored) : null;
};

function App() {
  const [user, setUser] = useState(initialUser);
  const [view, setView] = useState(user?.role === "ADMIN" ? "inventory" : "products");

  function onLogin(data) {
    storage.setSession(data);
    setUser({ email: data.email, role: data.role });
    setView(data.role === "ADMIN" ? "inventory" : "products");
  }

  function logout() {
    storage.clear();
    setUser(null);
    setView("products");
  }

  if (!user) return <AuthScreen onLogin={onLogin} />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Boxes size={24} />
          <span>Order Management</span>
        </div>
        <nav>
          {user.role === "ADMIN" ? (
            <>
              <NavButton icon={<PackagePlus />} label="Inventory" id="inventory" view={view} setView={setView} />
              <NavButton icon={<ShoppingCart />} label="Orders" id="orders" view={view} setView={setView} />
              <NavButton icon={<CreditCard />} label="Payments" id="payments" view={view} setView={setView} />
              <NavButton icon={<Users />} label="Users" id="users" view={view} setView={setView} />
            </>
          ) : (
            <>
              <NavButton icon={<PackagePlus />} label="Products" id="products" view={view} setView={setView} />
              <NavButton icon={<ShoppingCart />} label="Orders" id="orders" view={view} setView={setView} />
              <NavButton icon={<CreditCard />} label="Payments" id="payments" view={view} setView={setView} />
            </>
          )}
        </nav>
        <button className="nav-button logout" onClick={logout} title="Log out">
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{viewLabel(view)}</h1>
            <p>{user.email}</p>
          </div>
          <span className="role-pill">
            <Shield size={16} />
            {user.role}
          </span>
        </header>

        {view === "products" && <Products />}
        {view === "inventory" && <Products admin />}
        {view === "orders" && <Orders />}
        {view === "payments" && <Payments />}
        {view === "users" && <UsersPanel />}
      </main>
    </div>
  );
}

function viewLabel(view) {
  return {
    products: "Products",
    inventory: "Inventory",
    orders: "Orders",
    payments: "Payments",
    users: "Users",
  }[view];
}

function NavButton({ icon, label, id, view, setView }) {
  return (
    <button
      className={`nav-button ${view === id ? "active" : ""}`}
      onClick={() => setView(id)}
      title={label}
    >
      {React.cloneElement(icon, { size: 18 })}
      <span>{label}</span>
    </button>
  );
}

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState("login");

  return (
    <main className="auth-layout">
      <section className="auth-panel">
        <div className="brand auth-brand">
          <Boxes size={24} />
          <span>Order Management</span>
        </div>
        <div className="segmented">
          <button className={mode === "login" ? "selected" : ""} onClick={() => setMode("login")}>Login</button>
          <button className={mode === "register" ? "selected" : ""} onClick={() => setMode("register")}>Register</button>
        </div>
        {mode === "login" ? <LoginForm onLogin={onLogin} /> : <RegisterForm setMode={setMode} />}
      </section>
    </main>
  );
}

function LoginForm({ onLogin }) {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const response = await apiRequest("/api/auth/login/", { method: "POST", body: form, auth: false });
      onLogin(response.data);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <TextInput label="Email" value={form.email} onChange={(email) => setForm({ ...form, email })} />
      <TextInput label="Password" type="password" value={form.password} onChange={(password) => setForm({ ...form, password })} />
      {error && <p className="error">{error}</p>}
      <button className="primary" type="submit">Login</button>
    </form>
  );
}

function RegisterForm({ setMode }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await apiRequest("/api/auth/register/", { method: "POST", body: form, auth: false });
      setMode("login");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <div className="grid two">
        <TextInput label="First name" value={form.first_name} onChange={(first_name) => setForm({ ...form, first_name })} />
        <TextInput label="Last name" value={form.last_name} onChange={(last_name) => setForm({ ...form, last_name })} />
      </div>
      <TextInput label="Email" value={form.email} onChange={(email) => setForm({ ...form, email })} />
      <TextInput label="Password" type="password" value={form.password} onChange={(password) => setForm({ ...form, password })} />
      <TextInput label="Confirm password" type="password" value={form.confirm_password} onChange={(confirm_password) => setForm({ ...form, confirm_password })} />
      {error && <p className="error">{error}</p>}
      <button className="primary" type="submit">Register</button>
    </form>
  );
}

function TextInput({ label, value, onChange, type = "text" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Products({ admin = false }) {
  const [products, setProducts] = useState([]);
  const [quantities, setQuantities] = useState({});
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({ name: "", description: "", sku: "", price: "", stock: "" });

  async function loadProducts() {
    const response = await apiRequest("/api/v1/products/", { auth: false });
    setProducts(normalizeList(response));
  }

  useEffect(() => {
    loadProducts().catch((err) => setMessage(err.message));
  }, []);

  async function placeOrder() {
    const items = Object.entries(quantities)
      .map(([product_id, quantity]) => ({ product_id: Number(product_id), quantity: Number(quantity) }))
      .filter((item) => item.quantity > 0);
    if (!items.length) return;
    const response = await apiRequest("/api/v1/orders/", { method: "POST", body: { items } });
    if (response.status === "INVENTORY_RESERVED") {
      setMessage(`Order #${response.id} created and inventory reserved.`);
    } else if (response.status === "OUT_OF_STOCK") {
      setMessage(`Order #${response.id} could not be fulfilled because stock is unavailable.`);
    } else {
      setMessage(`Order #${response.id} created.`);
    }
    setQuantities({});
    await loadProducts();
  }

  async function createProduct(event) {
    event.preventDefault();
    await apiRequest("/api/v1/products/", {
      method: "POST",
      body: { ...form, price: Number(form.price), stock: Number(form.stock) },
    });
    setForm({ name: "", description: "", sku: "", price: "", stock: "" });
    await loadProducts();
  }

  async function deleteProduct(id) {
    await apiRequest(`/api/v1/products/${id}/`, { method: "DELETE" });
    await loadProducts();
  }

  return (
    <section className="content-grid">
      {admin && (
        <form className="panel stack" onSubmit={createProduct}>
          <h2>New Product</h2>
          <TextInput label="Name" value={form.name} onChange={(name) => setForm({ ...form, name })} />
          <TextInput label="Description" value={form.description} onChange={(description) => setForm({ ...form, description })} />
          <div className="grid three">
            <TextInput label="SKU" value={form.sku} onChange={(sku) => setForm({ ...form, sku })} />
            <TextInput label="Price" value={form.price} onChange={(price) => setForm({ ...form, price })} />
            <TextInput label="Stock" value={form.stock} onChange={(stock) => setForm({ ...form, stock })} />
          </div>
          <button className="primary" type="submit">Create</button>
        </form>
      )}

      <section className="panel wide">
        <PanelHeader title={admin ? "Inventory" : "Products"} onRefresh={loadProducts} />
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Price</th>
                <th>Stock</th>
                <th>{admin ? "Action" : "Qty"}</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td>{product.sku}</td>
                  <td>{product.name}</td>
                  <td>{product.price}</td>
                  <td>{product.stock}</td>
                  <td>
                    {admin ? (
                      <button className="danger" onClick={() => deleteProduct(product.id)}>Delete</button>
                    ) : (
                      <input
                        className="qty"
                        type="number"
                        min="0"
                        max={product.stock}
                        value={quantities[product.id] || ""}
                        onChange={(event) => setQuantities({ ...quantities, [product.id]: event.target.value })}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!admin && <button className="primary align-right" onClick={placeOrder}>Place Order</button>}
        {message && <p className="status-line">{message}</p>}
      </section>
    </section>
  );
}

function Orders() {
  const [orders, setOrders] = useState([]);
  const [message, setMessage] = useState("");
  const [payingOrderId, setPayingOrderId] = useState(null);

  async function loadOrders() {
    const response = await apiRequest("/api/v1/orders/");
    setOrders(normalizeList(response));
  }

  async function payOrder(order) {
    setMessage("");
    setPayingOrderId(order.id);
    try {
      const response = await apiRequest("/api/v1/payments/initiate/", {
        method: "POST",
        body: { order_id: order.id },
      });
      setMessage(response.message || `Payment processed for order #${order.id}.`);
      await loadOrders();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setPayingOrderId(null);
    }
  }

  useEffect(() => {
    loadOrders();
  }, []);

  function canPay(order) {
    return !order.is_paid && ["INVENTORY_RESERVED", "PAYMENT_FAILED"].includes(order.status);
  }

  return (
    <section className="panel">
      <PanelHeader title="Orders" onRefresh={loadOrders} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Total</th>
              <th>Paid</th>
              <th>Payment</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id}>
                <td>#{order.id}</td>
                <td><Status value={order.status} /></td>
                <td>{order.total_amount}</td>
                <td>{order.is_paid ? "Yes" : "No"}</td>
                <td>{order.payment_status || "-"}</td>
                <td>{new Date(order.created_at).toLocaleString()}</td>
                <td>
                  {canPay(order) ? (
                    <button
                      className="secondary action-button"
                      disabled={payingOrderId === order.id}
                      onClick={() => payOrder(order)}
                    >
                      <CreditCard size={16} />
                      {payingOrderId === order.id ? "Processing" : "Pay"}
                    </button>
                  ) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {message && <p className={message.toLowerCase().includes("failed") ? "error" : "status-line"}>{message}</p>}
    </section>
  );
}

function Payments() {
  const [payments, setPayments] = useState([]);

  async function loadPayments() {
    const response = await apiRequest("/api/v1/payments/");
    setPayments(normalizeList(response));
  }

  async function retry(id) {
    await apiRequest(`/api/v1/payments/${id}/retry/`, { method: "POST" });
    await loadPayments();
  }

  useEffect(() => {
    loadPayments();
  }, []);

  return (
    <section className="panel">
      <PanelHeader title="Payments" onRefresh={loadPayments} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Order</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Retries</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr key={payment.id}>
                <td>#{payment.id}</td>
                <td>#{payment.order}</td>
                <td>{payment.amount}</td>
                <td><Status value={payment.status} /></td>
                <td>{payment.retry_count}</td>
                <td>
                  {payment.status === "FAILED" ? (
                    <button className="secondary" onClick={() => retry(payment.id)}>Retry</button>
                  ) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function UsersPanel() {
  const [users, setUsers] = useState([]);

  async function loadUsers() {
    const response = await apiRequest("/api/auth/users/");
    setUsers(normalizeList(response));
  }

  async function updateUser(user, updates) {
    await apiRequest(`/api/auth/users/${user.id}/`, {
      method: "PATCH",
      body: { ...updates },
    });
    await loadUsers();
  }

  useEffect(() => {
    loadUsers();
  }, []);

  return (
    <section className="panel">
      <PanelHeader title="Users" onRefresh={loadUsers} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Active</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map((item) => (
              <tr key={item.id}>
                <td>{item.email}</td>
                <td>
                  <select value={item.role} onChange={(event) => updateUser(item, { role: event.target.value })}>
                    <option value="CUSTOMER">CUSTOMER</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </td>
                <td>{item.is_active ? "Yes" : "No"}</td>
                <td>
                  <button
                    className="secondary"
                    onClick={() => updateUser(item, { is_active: !item.is_active })}
                  >
                    {item.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PanelHeader({ title, onRefresh }) {
  return (
    <div className="panel-header">
      <h2>{title}</h2>
      <button className="icon-button" onClick={onRefresh} title="Refresh">
        <RefreshCcw size={17} />
      </button>
    </div>
  );
}

function Status({ value }) {
  const tone = useMemo(() => {
    if (["COMPLETED", "SUCCESS"].includes(value)) return "good";
    if (["FAILED", "PAYMENT_FAILED", "OUT_OF_STOCK", "CANCELLED"].includes(value)) return "bad";
    return "pending";
  }, [value]);
  return <span className={`status ${tone}`}>{value}</span>;
}

createRoot(document.getElementById("root")).render(<App />);
