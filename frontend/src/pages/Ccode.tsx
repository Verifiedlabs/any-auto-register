import { useState } from 'react'
import { apiFetch } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Zap, CheckCircle, XCircle, Copy, Key } from 'lucide-react'

export default function Ccode() {
  const [count, setCount] = useState('10')
  const [affCode, setAffCode] = useState('3GLRG6XG8VQE')
  const [useProxy, setUseProxy] = useState(true)
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<any[]>([])

  const register = async () => {
    setRunning(true)
    try {
      const res = await apiFetch('/ccode/register', {
        method: 'POST',
        body: JSON.stringify({ count: parseInt(count) || 10, aff_code: affCode, use_proxy: useProxy }),
      })
      setResults(res.results || [])
    } catch (e: any) {
      setResults([{ ok: false, error: e.message }])
    }
    setRunning(false)
  }

  const copyAllKeys = () => {
    const keys = results.filter(r => r.ok && r.api_key).map(r => r.api_key).join('\n')
    navigator.clipboard.writeText(keys)
  }

  const copyAll = () => {
    const lines = results.filter(r => r.ok).map(r => `${r.email}|${r.password}|${r.api_key}`).join('\n')
    navigator.clipboard.writeText(lines)
  }

  const successCount = results.filter(r => r.ok).length

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-[var(--text-primary)]">Ccode Auto Register</div>
            {results.length > 0 && (
              <>
                <Badge variant="default">{results.length} total</Badge>
                <Badge variant="secondary" className="text-emerald-400">{successCount} success</Badge>
              </>
            )}
          </div>
          {successCount > 0 && (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={copyAllKeys}><Key className="h-4 w-4 mr-1.5" />Copy Keys</Button>
              <Button variant="outline" size="sm" onClick={copyAll}><Copy className="h-4 w-4 mr-1.5" />Copy All</Button>
            </div>
          )}
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,350px)_minmax(0,1fr)]">
        <Card className="bg-[var(--bg-pane)]/60">
          <div className="space-y-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Register Settings</div>
              <div className="mt-1 text-sm font-medium text-[var(--text-primary)]">Random email + auto API key</div>
            </div>
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <input className="input" placeholder="Count" value={count} onChange={e => setCount(e.target.value)} />
                <input className="input" placeholder="Aff code" value={affCode} onChange={e => setAffCode(e.target.value)} />
              </div>
              <label className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                <input type="checkbox" checked={useProxy} onChange={e => setUseProxy(e.target.checked)} />
                Use proxy rotation (avoid rate limit)
              </label>
              <Button size="sm" onClick={register} disabled={running} className="w-full">
                <Zap className={`h-4 w-4 mr-1.5 ${running ? 'animate-spin' : ''}`} />
                {running ? 'Registering...' : `Register ${count} accounts`}
              </Button>
            </div>
          </div>
        </Card>

        <Card className="overflow-x-auto bg-[var(--bg-pane)]/60">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-soft)] text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
                <th className="py-2 px-2 text-left">Email</th>
                <th className="py-2 px-2 text-left">Password</th>
                <th className="py-2 px-2 text-left">API Key</th>
                <th className="py-2 px-2 text-left">Balance</th>
                <th className="py-2 px-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="border-b border-[var(--border-soft)]/50 hover:bg-[var(--bg-hover)]">
                  <td className="py-2 px-2 text-xs font-mono">{r.email || '-'}</td>
                  <td className="py-2 px-2 text-xs font-mono">{r.password || '-'}</td>
                  <td className="py-2 px-2 text-xs font-mono">{r.api_key ? `${r.api_key.slice(0, 15)}...` : '-'}</td>
                  <td className="py-2 px-2 text-xs">{r.balance ?? '-'}</td>
                  <td className="py-2 px-2">
                    {r.ok ? <CheckCircle className="h-4 w-4 text-emerald-400" /> : <XCircle className="h-4 w-4 text-red-400" />}
                  </td>
                </tr>
              ))}
              {results.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-sm text-[var(--text-muted)]">Enter gmail base and click Register</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
