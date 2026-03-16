import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { settingsApi } from '../../api/settings'
import Spinner from '../../components/common/Spinner'
import Modal from '../../components/common/Modal'
import Badge from '../../components/common/Badge'

const CLIENT_TYPES = ['qbittorrent', 'transmission', 'deluge', 'sabnzbd', 'nzbget']

export default function DownloadClientsSettings() {
  const qc = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({
    name: '', type: 'qbittorrent', host: 'localhost', port: 8080,
    use_ssl: false, username: '', password: '', api_key: '',
    category: 'scanarr', is_default: false, enabled: true, priority: 0,
  })

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ['download-clients'],
    queryFn: settingsApi.listClients,
  })

  const add = useMutation({
    mutationFn: () => settingsApi.addClient(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['download-clients'] }); setModalOpen(false) },
  })

  const remove = useMutation({
    mutationFn: (id: number) => settingsApi.deleteClient(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['download-clients'] }),
  })

  const test = useMutation({
    mutationFn: (id: number) => settingsApi.testClient(id),
  })

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-200">Download Clients</h3>
        <button className="btn-primary text-sm" onClick={() => setModalOpen(true)}>
          <Plus size={14} /> Add Client
        </button>
      </div>

      {isLoading ? <Spinner /> : (
        <div className="space-y-2">
          {clients.map((c) => (
            <div key={c.id} className="card flex items-center gap-4 px-4 py-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200">{c.name}</p>
                <p className="text-xs text-gray-500">{c.type} — {c.host}:{c.port}</p>
              </div>
              <div className="flex items-center gap-2">
                {c.is_default && <Badge variant="info">Default</Badge>}
                <Badge variant={c.enabled ? 'success' : 'muted'}>{c.enabled ? 'Enabled' : 'Disabled'}</Badge>
                <button className="btn-secondary text-xs px-2 py-1" onClick={() => test.mutate(c.id)}>Test</button>
                <button
                  className="p-1.5 text-gray-500 hover:text-red-400 transition-colors"
                  onClick={() => remove.mutate(c.id)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
          {clients.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-8">No download clients configured</p>
          )}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add Download Client">
        <div className="space-y-3">
          <div>
            <label className="label">Name</label>
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <label className="label">Type</label>
            <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {CLIENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Host</label>
              <input className="input" value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })} />
            </div>
            <div>
              <label className="label">Port</label>
              <input className="input" type="number" value={form.port} onChange={(e) => setForm({ ...form, port: Number(e.target.value) })} />
            </div>
          </div>
          <div>
            <label className="label">Username</label>
            <input className="input" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="def" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} />
            <label htmlFor="def" className="text-sm text-gray-300">Set as default</label>
          </div>
          <div className="flex gap-2 mt-4">
            <button className="btn-primary" onClick={() => add.mutate()} disabled={add.isPending || !form.name}>
              {add.isPending ? <Spinner size="sm" /> : 'Add'}
            </button>
            <button className="btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
