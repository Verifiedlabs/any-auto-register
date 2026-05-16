export const TASK_STATUS_VARIANTS: Record<string, any> = {
  pending: 'secondary',
  claimed: 'secondary',
  running: 'default',
  succeeded: 'success',
  failed: 'danger',
  interrupted: 'warning',
  cancel_requested: 'warning',
  cancelled: 'warning',
}

export const TERMINAL_TASK_STATUSES = new Set([
  'succeeded',
  'failed',
  'interrupted',
  'cancelled',
])

export function isTerminalTaskStatus(status: string) {
  return TERMINAL_TASK_STATUSES.has(status)
}

export function getTaskStatusText(status: string) {
  switch (status) {
    case 'succeeded':
      return 'Completed'
    case 'failed':
      return 'Failed'
    case 'interrupted':
      return 'Interrupted'
    case 'cancelled':
      return 'Cancelled'
    case 'cancel_requested':
      return 'Cancelling'
    case 'running':
      return 'Running'
    case 'claimed':
      return 'Claimed'
    case 'pending':
      return 'Pending'
    default:
      return status
  }
}
