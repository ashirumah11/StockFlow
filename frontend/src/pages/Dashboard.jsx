import { useEffect, useState } from "react";
import api from "../api/axios";

function Dashboard() {
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
          setError("Your session has expired. Please log in again.");
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        } else {
          setError("Unable to load dashboard.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <h2>Loading dashboard...</h2>;
  }

  if (error) {
    return <p style={{ color: "red" }}>{error}</p>;
  }

  return (
    <div>
      <h1>StockFlow Dashboard</h1>

      <div>
        <h3>Total Products</h3>
        <p>{dashboard.total_products}</p>
      </div>

      <div>
        <h3>Total Stock</h3>
        <p>{dashboard.total_stock}</p>
      </div>

      <div>
        <h3>Low Stock</h3>
        <p>{dashboard.low_stock_count}</p>
      </div>

      <div>
        <h3>Out of Stock</h3>
        <p>{dashboard.out_of_stock_count}</p>
      </div>

      <h2>Recent Activity</h2>

      {dashboard.recent_activity.length === 0 ? (
        <p>No recent stock movements.</p>
      ) : (
        <ul>
          {dashboard.recent_activity.map((movement) => (
            <li key={movement.id}>
              {movement.product} — {movement.movement_type} —{" "}
              {movement.quantity}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Dashboard;
