import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../../api/settings'
import Spinner from '../../components/common/Spinner'

export default function ProwlarrSettings() {
  const qc = useQueryClient()
  const { data: cfg, isLoading } = useQuery({
    queryKey: ['prowlarr-config'],
    queryFn: settingsApi.getProwlarr,
    retry: false,
  })

  const [url, setUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [enabled, setEnabled] = useState(true)
  const [testResult, setTestResult] = useState<'ok' | 'fail' | null>(null)

  const save = useMutation({
    mutationFn: () => settingsApi.saveProwlarr({ url, api_key: apiKey, enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['prowlarr-config'] }),
  })

  const test = useMutation({
    mutationFn: settingsApi.testProwlarr,
    onSuccess: () => setTestResult('ok'),
    onError: () => setTestResult('fail'),
  })

  const syncIndexers = useMutation({
    mutationFn: settingsApi.syncIndexers,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['indexers'] }),
  })

  if (isLoading) return <div className="flex justify-center py-16"><Spinner /></div>

  return (
    <div className="space-y-6 max-w-lg">
      <div className="card p-5">
        <h3 className="font-semibold text-gray-200 mb-4">Prowlarr Connection</h3>

        {cfg && (
          <div className="mb-4 p-3 rounded-lg bg-green-900/30 border border-green-800/50 text-sm text-green-400">
            Connected — last sync: {cfg.last_sync ? new Date(cfg.last_sync).toLocaleString() : 'never'}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="label">URL</label>
            <input
              className="input"
              placeholder="http://prowlarr:9696"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <div>
            <label className="label">API Key</label>
            <input
              className="input font-mono"
              type="password"
              placeholder="••••••••••••••••"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="enabled"
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="enabled" className="text-sm text-gray-300">Enabled</label>
          </div>
        </div>

        <div className="flex gap-2 mt-5">
          <button
            className="btn-primary"
            onClick={() => save.mutate()}
            disabled={save.isPending || !url || !apiKey}
          >
            {save.isPending ? <Spinner size="sm" /> : 'Save'}
          </button>
          <button
            className="btn-secondary"
            onClick={() => test.mutate()}
            disabled={test.isPending}
          >
            Test Connection
          </button>
          {cfg && (
            <button
              className="btn-secondary"
              onClick={() => syncIndexers.mutate()}
              disabled={syncIndexers.isPending}
            >
              Sync Indexers
            </button>
          )}
        </div>

        {testResult === 'ok' && <p className="mt-3 text-sm text-green-400">Connection successful</p>}
        {testResult === 'fail' && <p className="mt-3 text-sm text-red-400">Connection failed — check URL and API key</p>}
      </div>
    </div>
  )
}
