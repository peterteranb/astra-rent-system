import "./EquipmentImage.css";
export default function EquipmentImage({ inventoryId, name, className = "" }) {
  return <div className={`equipment-image ${className}`}><img src={`/img/equipment/${inventoryId}.jpg`} alt={name || inventoryId} loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} /><span>{name || inventoryId}</span></div>;
}
