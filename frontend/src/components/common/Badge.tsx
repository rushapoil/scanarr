import { clsx } from 'clsx'

type Variant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'muted'

interface Props {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

const variants: Record<Variant, string> = {
  default: 'bg-brand-900/60 text-brand-300',
  success: 'bg-green-900/60 text-green-400',
  warning: 'bg-yellow-900/60 text-yellow-400',
  danger: 'bg-red-900/60 text-red-400',
  info: 'bg-blue-900/60 text-blue-400',
  muted: 'bg-surface-border text-gray-400',
}

export default function Badge({ children, variant = 'default', className }: Props) {
  return (
    <span className={clsx('badge', variants[variant], className)}>
      {children}
    </span>
  )
}
