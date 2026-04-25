function SectionHeader({ title, subtitle }) {
  return (
    <div className="section-header">
      <div className="section-header-title">{title}</div>
      {subtitle && <div className="section-header-subtitle">{subtitle}</div>}
    </div>
  )
}

export default SectionHeader
