type TagVariant = 'keyword' | 'theme' | 'external-id'

interface TagListProps {
  items: string[] | null | undefined
  variant: TagVariant
  fallback?: string
}

const TAG_CONFIG: Record<TagVariant, { className: string; element: 'span' | 'code' }> = {
  keyword: { className: 'keyword-tag', element: 'span' },
  theme: { className: 'theme-tag', element: 'span' },
  'external-id': { className: 'external-id-tag', element: 'code' },
}

export default function TagList({ items, variant, fallback = '-' }: TagListProps) {
  if (!items?.length) {
    return <span className="empty">{fallback}</span>
  }

  const { className, element: Element } = TAG_CONFIG[variant]

  return (
    <div className="tag-list">
      {items.map((item, i) => (
        <Element key={`${variant}-${item}-${i}`} className={className}>{item}</Element>
      ))}
    </div>
  )
}
