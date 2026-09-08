import { useNavigate } from "react-router-dom";

function QuickActions() {
  const navigate = useNavigate();
  return (
    <div className="quick-actions">
      <button type="button" onClick={() => navigate("/inventory")} className="primary-action"><span>+</span>Add Product</button>
      <button type="button" onClick={() => navigate("/movements")} className="secondary-action"><span>v</span>Record Movement</button>
    </div>
  );
}

export default QuickActions;