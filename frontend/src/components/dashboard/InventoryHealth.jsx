function InventoryHealth({ totalProducts = 0, lowStock = 0, outOfStock = 0 }) {
  const healthy = Math.max(totalProducts - lowStock - outOfStock, 0);
  const healthPercentage = totalProducts > 0 ? Math.round((healthy / totalProducts) * 100) : 0;

  return (
    <section className="dashboard-card health-card">
      <div className="card-heading">
        <div><p className="eyebrow">INVENTORY OVERVIEW</p><h2>Inventory Health</h2></div>
        <span className="card-menu" aria-hidden="true">...</span>
      </div>
      <div className="health-content">
        <div className="health-ring" style={{ "--health": `${healthPercentage * 3.6}deg` }}>
          <div className="health-ring-inner"><strong>{healthPercentage}%</strong><span>Healthy</span></div>
        </div>
        <div className="health-breakdown">
          <div><span className="health-dot healthy" /><span>Healthy stock</span><strong>{healthy}</strong></div>
          <div><span className="health-dot low" /><span>Low stock</span><strong>{lowStock}</strong></div>
          <div><span className="health-dot empty" /><span>Out of stock</span><strong>{outOfStock}</strong></div>
        </div>
      </div>
    </section>
  );
}

export default InventoryHealth;