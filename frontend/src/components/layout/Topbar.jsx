function Topbar() {
  return (
    <header className="stock-topbar">
      <div className="topbar-search">
        <span aria-hidden="true">?</span>
        <input type="search" placeholder="Search products, SKU, suppliers..." aria-label="Search" />
        <kbd>Ctrl K</kbd>
      </div>
      <div className="topbar-actions">
        <button className="icon-button" type="button" title="Notifications" aria-label="Notifications">
          !<span className="notification-dot">3</span>
        </button>
        <div className="topbar-divider" />
        <button className="profile-button" type="button">
          <div className="user-avatar">A</div>
          <div className="profile-details">
            <strong>Administrator</strong>
            <span>Admin</span>
          </div>
          <span aria-hidden="true">v</span>
        </button>
      </div>
    </header>
  );
}

export default Topbar;