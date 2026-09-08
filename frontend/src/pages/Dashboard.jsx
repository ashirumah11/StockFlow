import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";
import StatCard from "../components/dashboard/StatCard";
import InventoryHealth from "../components/dashboard/InventoryHealth";
import LowStockPanel from "../components/dashboard/LowStockPanel";
import RecentActivity from "../components/dashboard/RecentActivity";
import QuickActions from "../components/dashboard/QuickActions";

function Dashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get("dashboard/");
        setDashboard(response.data);
      } catch (error) {
        console.error(error);

        if (error.response?.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          navigate("/login", { replace: true });
          return;
        } else {
          setError("Unable to load dashboard.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [navigate]);

  if (loading) {
    return <div className="dashboard-loading"><div className="loading-spinner" /><p>Loading StockFlow...</p></div>;
  }

  if (error) {
    return <div className="dashboard-error"><div className="error-icon">!</div><h2>Dashboard unavailable</h2><p>{error}</p><button onClick={() => window.location.reload()} className="primary-action" type="button">Try again</button></div>;
  }

  const health = dashboard.health_tiles || {};
  const recentMovements = dashboard.recent_movements || [];

  return (
    <div className="stockflow-shell">
      <Sidebar />
      <div className="stockflow-main">
        <Topbar />
        <main className="dashboard-content">
          <section className="dashboard-header">
            <div><p className="eyebrow">INVENTORY COMMAND CENTER</p><h1>Good afternoon, Administrator</h1><p className="dashboard-subtitle">Here&apos;s what&apos;s happening with your inventory today.</p></div>
            <QuickActions />
          </section>
          <section className="stats-grid">
            <StatCard title="Total Products" value={health.total_products ?? 0} description="Products in your inventory" icon="[]" />
            <StatCard title="Total Stock" value={(health.total_stock ?? 0).toLocaleString()} description="Units currently available" icon="[]" variant="success" />
            <StatCard title="Low Stock" value={health.low_stock ?? 0} description="Products need replenishment" icon="!" variant="warning" />
            <StatCard title="Out of Stock" value={health.out_of_stock ?? 0} description="Products unavailable" icon="!" variant="danger" />
          </section>
          <section className="dashboard-grid-two">
            <InventoryHealth totalProducts={health.total_products ?? 0} lowStock={health.low_stock ?? 0} outOfStock={health.out_of_stock ?? 0} />
            <section className="dashboard-card insight-card">
              <div className="card-heading"><div><p className="eyebrow">SYSTEM STATUS</p><h2>Inventory Snapshot</h2></div><span className="status-online"><span />Live</span></div>
              <div className="snapshot-list">
                <div><span>Stock availability</span><strong>{health.total_stock ?? 0} units</strong></div>
                <div><span>Products requiring attention</span><strong>{(health.low_stock ?? 0) + (health.out_of_stock ?? 0)}</strong></div>
                <div><span>Recent movements</span><strong>{recentMovements.length}</strong></div>
              </div>
            </section>
          </section>
          <section className="dashboard-grid-two activity-section"><LowStockPanel products={dashboard.low_stock_products || []} /><RecentActivity activities={recentMovements} /></section>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
