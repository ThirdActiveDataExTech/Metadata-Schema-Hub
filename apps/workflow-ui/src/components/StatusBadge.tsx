interface StatusBadgeProps {
  status: string
  className?: string
}

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const statusClass = status.toLowerCase()
  return (
    <span className={`status-badge ${statusClass} ${className}`}>
      {status}
    </span>
  )
}
