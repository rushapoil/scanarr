import { useQuery } from '@tanstack/react-query'
import { systemApi } from '../../api/system'
import Spinner from '../../components/common/Spinner'

export default function GeneralSettings() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: systemApi.status,
  })

  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: systemApi.tasks,
  })

  if (isLoading) return <div className="flex justify-center py-16"><Spinner /></div>

  return (
    <div className="space-y-6 max-w-2xl">
      {/* System info */}
      <div className="card p-5">
        <h3 className="font-semibold text-gray-200 mb-4">System Information</h3>
        <dl className="space-y-2 text-sm">
          {[
            ['Version', status?.version],
            ['Config Dir', status?.config_dir],
            ['Data Dir', status?.data_dir],
            ['Database', status?.db_path],
            ['Runtime', status?.runtime_version],
            ['OS', `${status?.os_name} ${status?.os_version}`],
            ['Started', status?.startup_time ? new Date(status.startup_time).toLocaleString() : '—'],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between gap-4">
              <dt className="text-gray-500">{label}</dt>
              <dd className="text-gray-300 font-mono text-xs">{value || '—'}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Scheduled tasks */}
      <div className="card p-5">
        <h3 className="font-semibold text-gray-200 mb-4">Scheduled Tasks</h3>
        <div className="space-y-2">
          {tasks.map((task) => (
            <div key={task.id} className="flex items-center justify-between text-sm py-2 border-b border-surface-border last:border-0">
              <span className="text-gray-300">{task.name}</span>
              <div className="flex items-center gap-3 text-xs text-gray-500">
                {task.next_run_time && (
                  <span>Next: {new Date(task.next_run_time).toLocaleTimeString()}</span>
                )}
                <button
                  className="btn-secondary text-xs px-2 py-1"
                  onClick={async () => {
                    await systemApi.runTask(task.id)
                  }}
                >
                  Run now
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
