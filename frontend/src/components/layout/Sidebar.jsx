import { NavLink } from "react-router-dom";

const navigation = [
  { section: "MAIN", items: [{ label: "Dashboard", icon: "[]", path: "/dashboard" }] },
  {
    section: "INVENTORY",
    items: [
      { label: "Products", icon: "[]", path: "/inventory" },
      { label: "Categories", icon: "<> ", path: "/categories" },
      { label: "Stock Movements", icon: "<>", path: "/movements" },
    ],
  },
  { section: "SUPPLY", items: [{ label: "Suppliers", icon: "<> ", path: "/suppliers" }] },
  {
    section: "MANAGEMENT",
    items: [
      { label: "Reports", icon: "[]", path: "/reports" },
      { label: "Notifications", icon: "!", path: "/notifications" },
    ],
  },
];

function Sidebar() {
  return (
    <aside className="stock-sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">S</div>
        <div>
          <h2>StockFlow</h2>
          <span>Inventory Management</span>
        </div>
      </div>

      <nav className="sidebar-navigation" aria-label="Main navigation">
        {navigation.map((group) => (
          <div className="nav-group" key={group.section}>
            <p className="nav-section-title">{group.section}</p>
            {group.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              >
                <span className="sidebar-icon" aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <NavLink to="/settings" className="sidebar-link">
          <span className="sidebar-icon" aria-hidden="true">*</span>
          <span>Settings</span>
        </NavLink>
        <div className="sidebar-user">
          <div className="user-avatar">A</div>
          <div className="sidebar-user-info">
            <strong>Administrator</strong>
            <span>StockFlow Admin</span>
          </div>
          <span className="user-menu" aria-hidden="true">...</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;