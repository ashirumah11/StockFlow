function StatCard({ title, value, description, icon, variant = "default" }) {
  return (
    <article className={`stat-card stat-${variant}`}>
      <div className="stat-card-top">
        <div className="stat-icon" aria-hidden="true">{icon}</div>
        {variant === "danger" && <span className="stat-badge">Attention</span>}
      </div>
      <p className="stat-title">{title}</p>
      <h3>{value}</h3>
      <p className="stat-description">{description}</p>
    </article>
  );
}

export default StatCard;