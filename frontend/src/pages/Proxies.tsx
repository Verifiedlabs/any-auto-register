import { useEffect, useState } from 'react'
import { apiFetch } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Trash2, RefreshCw, ToggleLeft, ToggleRight, Globe2, ShieldCheck, CircleOff, Activity, Download } from 'lucide-react'

export default function Proxies() {
  const [proxies, setProxies] = useState<any[]>([])
  const [newProxy, setNewProxy] = useState('')
  const [region, setRegion] = useState('')
  const [checking, setChecking] = useState(false)
  const [fetchType, setFetchType] = useState('SOCKS5')
  const [fetchLimit, setFetchLimit] = useState('100')
  const [fetchCheckAlive, setFetchCheckAlive] = useState(true)
  const [fetching, setFetching] = useState(false)
  const [fetchResult, setFetchResult] = useState<any>(null)

  const load = () => apiFetch('/proxies').then(setProxies)

  useEffect(() => { load() }, [])

  const add = async () => {
    if (!newProxy.trim()) return
    const lines = newProxy.trim().split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length > 1) {
      await apiFetch('/proxies/bulk', {
        method: 'POST',
        body: JSON.stringify({ proxies: lines, region }),
      })
    } else {
      await apiFetch('/proxies', {
        method: 'POST',
        body: JSON.stringify({ url: lines[0], region }),
      })
    }
    setNewProxy('')
    load()
  }

  const del = async (id: number) => {
    await apiFetch(`/proxies/${id}`, { method: 'DELETE' })
    load()
  }

  const toggle = async (id: number) => {
    await apiFetch(`/proxies/${id}/toggle`, { method: 'PATCH' })
    load()
  }

  const check = async () => {
    setChecking(true)
    await apiFetch('/proxies/check', { method: 'POST' })
    setTimeout(() => { load(); setChecking(false) }, 3000)
  }

  const fetchProxies = async () => {
    setFetching(true)
    setFetchResult(null)
    try {
      const res = await apiFetch('/proxy-fetch/fetch', {
        method: 'POST',
        body: JSON.stringify({ proxy_type: fetchType, limit: parseInt(fetchLimit) || 100, save_to_pool: true, check_alive: fetchCheckAlive }),
      })
      setFetchResult(res)
      load()
    } catch (e: any) {
      setFetchResult({ ok: false, error: e.message })
    }
    setFetching(false)
  }

  const deleteAll = async () => {
    if (!confirm('Delete all proxies?')) return
    for (const p of proxies) {
      await apiFetch(`/proxies/${p.id}`, { method: 'DELETE' })
    }
    load()
  }

  const downloadProxies = () => {
    const text = proxies.map(p => p.url).join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `proxies_${new Date().toISOString().slice(0,10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const activeCount = proxies.filter((item) => item.is_active).length
  const totalSuccess = proxies.reduce((sum, item) => sum + Number(item.success_count || 0), 0)
  const totalFail = proxies.reduce((sum, item) => sum + Number(item.fail_count || 0), 0)
   const metricCards = [
     { label: 'Total Proxies', value: proxies.length, icon: Globe2, tone: 'text-[var(--accent)]' },
     { label: 'Enabled', value: activeCount, icon: ShieldCheck, tone: 'text-emerald-400' },
     { label: 'Success Count', value: totalSuccess, icon: Activity, tone: 'text-[var(--accent)]' },
     { label: 'Fail Count', value: totalFail, icon: CircleOff, tone: 'text-red-400' },
   ]

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-[var(--text-primary)]">Proxies</div>
             <Badge variant="default">Total {proxies.length}</Badge>
             <Badge variant="secondary">Active {activeCount}</Badge>
          </div>
          <Button variant="outline" size="sm" onClick={check} disabled={checking}>
             <RefreshCw className={`h-4 w-4 mr-1.5 ${checking ? 'animate-spin' : ''}`} />
             Check All
          </Button>
          <Button variant="outline" size="sm" onClick={downloadProxies}>
             <Download className="h-4 w-4 mr-1.5" />
             Download
          </Button>
          <Button variant="outline" size="sm" onClick={deleteAll} className="text-red-400 hover:text-red-300">
             <Trash2 className="h-4 w-4 mr-1.5" />
             Delete All
          </Button>
        </div>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map(({ label, value, icon: Icon, tone }) => (
          <Card key={label} className="bg-transparent">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">{label}</div>
                <div className="mt-1.5 text-xl font-semibold tracking-[-0.03em] text-[var(--text-primary)]">{value}</div>
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border-soft)] bg-[var(--chip-bg)]">
                <Icon className={`h-5 w-5 ${tone}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,330px)_minmax(0,330px)]">
        <Card className="bg-[var(--bg-pane)]/60">
          <div className="space-y-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Add</div>
               <div className="mt-1 text-sm font-medium text-[var(--text-primary)]">Add proxy or bulk import</div>
            </div>
            <textarea
              value={newProxy}
              onChange={e => setNewProxy(e.target.value)}
              placeholder="http://user:pass@host:port"
              rows={6}
              className="control-surface control-surface-mono resize-none"
            />
            <input
              value={region}
              onChange={e => setRegion(e.target.value)}
               placeholder="Region tag (e.g., US, SG)"
              className="control-surface"
            />
            <Button onClick={add} className="w-full">
               <Plus className="h-4 w-4 mr-1.5" />
               Add to Proxy Pool
            </Button>
          </div>
        </Card>

        <Card className="bg-[var(--bg-pane)]/60">
          <div className="space-y-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Auto Fetch</div>
              <div className="mt-1 text-sm font-medium text-[var(--text-primary)]">Fetch free proxies (325K+ available)</div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select className="control-surface text-xs" value={fetchType} onChange={e => setFetchType(e.target.value)}>
                <option value="all">All Types</option>
                <option value="HTTP">HTTP</option>
                <option value="SOCKS4">SOCKS4</option>
                <option value="SOCKS5">SOCKS5</option>
              </select>
              <input className="control-surface text-xs" placeholder="Limit" value={fetchLimit} onChange={e => setFetchLimit(e.target.value)} />
            </div>
            <label className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <input type="checkbox" checked={fetchCheckAlive} onChange={e => setFetchCheckAlive(e.target.checked)} />
              Check alive before saving
            </label>
            <Button onClick={fetchProxies} disabled={fetching} className="w-full">
              <Download className={`h-4 w-4 mr-1.5 ${fetching ? 'animate-spin' : ''}`} />
              {fetching ? 'Fetching...' : 'Fetch & Save to Pool'}
            </Button>
            {fetchResult && (
              <div className={`text-xs p-2 rounded ${fetchResult.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                {fetchResult.ok ? `Fetched ${fetchResult.fetched} | Saved ${fetchResult.saved} new proxies` : fetchResult.error}
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card className="overflow-x-auto p-0">
        <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-medium text-[var(--text-primary)]">
          Proxy List
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
              <th className="px-4 py-2.5 text-left">Proxy Address</th>
              <th className="px-4 py-2.5 text-left">Region</th>
              <th className="px-4 py-2.5 text-left">Success/Failed</th>
              <th className="px-4 py-2.5 text-left">Status</th>
              <th className="px-4 py-2.5 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {proxies.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">Proxy pool is empty</td>
              </tr>
            )}
            {proxies.map(p => (
              <tr key={p.id} className="border-b border-[var(--border)]/40 hover:bg-[var(--bg-hover)]/70">
                <td className="px-4 py-2.5 font-mono text-xs break-all">{p.url}</td>
                <td className="px-4 py-2.5 text-xs">{p.region || '-'}</td>
                <td className="px-4 py-2.5 text-xs">
                  <span className="text-emerald-400">{p.success_count}</span>
                  <span className="text-[var(--text-muted)]"> / </span>
                  <span className="text-red-400">{p.fail_count}</span>
                </td>
                <td className="px-4 py-2.5">
                  <Badge variant={p.is_active ? 'success' : 'danger'}>
                    {p.is_active ? 'Active' : 'Disabled'}
                  </Badge>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <button onClick={() => toggle(p.id)} className="table-action-btn">
                      {p.is_active ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                    </button>
                    <button onClick={() => del(p.id)} className="table-action-btn table-action-btn-danger">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
