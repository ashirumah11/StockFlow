function getMovementClass(type) {
  const movement = type?.toLowerCase();
  if (movement?.includes("in")) return "movement-in";
  if (movement?.includes("out")) return "movement-out";
  return "movement-adjustment";
}

function RecentActivity({ activities = [] }) {
  return (
    <section className="dashboard-card">
      <div className="card-heading">
        <div><p className="eyebrow">LATEST OPERATIONS</p><h2>Recent Activity</h2></div>
        <button className="text-button" type="button">View history -&gt;</button>
      </div>
      {activities.length === 0 ? (
        <div className="empty-panel"><div className="empty-icon">-</div><strong>No recent activity</strong><p>Stock movements will appear here.</p></div>
      ) : (
        <div className="activity-list">
          {activities.slice(0, 6).map((movement) => (
            <div className="activity-item" key={movement.id}>
              <div className={`movement-icon ${getMovementClass(movement.movement_type)}`}>
                {movement.movement_type?.toLowerCase()?.includes("out") ? "-" : "+"}
              </div>
              <div className="activity-details"><strong>{movement.product_name || "Product"}</strong><span>{movement.movement_type} - {movement.quantity} units</span></div>
              <span className="activity-time">Recent</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default RecentActivity;