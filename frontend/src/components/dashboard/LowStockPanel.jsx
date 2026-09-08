function LowStockPanel({ products = [] }) {
  return (
    <section className="dashboard-card">
      <div className="card-heading">
        <div><p className="eyebrow">ACTION REQUIRED</p><h2>Low Stock</h2></div>
        <button className="text-button" type="button">View all -&gt;</button>
      </div>
      {products.length === 0 ? (
        <div className="empty-panel"><div className="empty-icon">OK</div><strong>Inventory looks good</strong><p>No products currently require attention.</p></div>
      ) : (
        <div className="low-stock-list">
          {products.slice(0, 5).map((product) => (
            <div className="low-stock-item" key={product.id}>
              <div className="product-placeholder">{product.name?.charAt(0)?.toUpperCase() || "P"}</div>
              <div className="product-info"><strong>{product.name}</strong><span>SKU: {product.sku || "N/A"}</span></div>
              <div className="stock-level"><strong>{product.quantity ?? 0}</strong><span>units</span></div>
              <span className="low-badge">Low</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default LowStockPanel;