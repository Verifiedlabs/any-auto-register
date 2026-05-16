import { useEffect, useState } from 'react'
import { apiFetch } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Zap, CheckCircle, ArrowUpCircle, CreditCard } from 'lucide-react'

export default function Upgrade() {
  const [platform, setPlatform] = useState('windsurf')
  const [accounts, setAccounts] = useState<any[]>([])
  const [vccs, setVccs] = useState<any[]>([])
  const [selectedAccounts, setSelectedAccounts] = useState<number[]>([])
  const [selectedVcc, setSelectedVcc] = useState<number | null>(null)
  const [headless, setHeadless] = useState(false)
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<any[]>([])

  const loadAccounts = () => apiFetch(`/upgrade/accounts/${platform}`).then((d: any) => setAccounts(d.accounts || []))
  const loadVccs = () => apiFetch('/vccs').then((d: any) => setVccs(d.vccs || []))

  useEffect(() => { loadAccounts(); loadVccs() }, [platform])

  const toggleAccount = (id: number) => {
    setSelectedAccounts(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const selectAllUpgradeable = () => {
    const ids = accounts.filter(a => a.upgradeable).map(a => a.id)
    setSelectedAccounts(ids)
  }

  const runUpgrade = async () => {
    if (selectedAccounts.length === 0) return
    setRunning(true)
    setResults([])
    try {
      const res = await apiFetch('/upgrade/bulk', {
        method: 'POST',
        body: JSON.stringify({
          platform,
          account_ids: selectedAccounts,
          vcc_id: selectedVcc,
          headless,
          timeout: 180,
        }),
      })
      setResults(res.results || [])
    } catch (e: any) {
      setResults([{ ok: false, error: e.message }])
    }
    setRunning(false)
    loadAccounts()
  }

  const upgradeableCount = accounts.filter(a => a.upgradeable).length
  const activeVccs = vccs.filter(v => v.status === 'active')

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-[var(--text-primary)]">Multi-Platform Upgrade</div>
            <Badge variant="default">{platform}</Badge>
            <Badge variant="secondary">{upgradeableCount} upgradeable</Badge>
          </div>
          <div className="flex gap-2">
            {['windsurf', 'kiro'].map(p => (
              <Button key={p} size="sm" variant={platform === p ? 'default' : 'outline'} onClick={() => setPlatform(p)}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Total Accounts', value: accounts.length, icon: ArrowUpCircle, tone: 'text-[var(--accent)]' },
          { label: 'Upgradeable', value: upgradeableCount, icon: Zap, tone: 'text-emerald-400' },
          { label: 'Selected', value: selectedAccounts.length, icon: CheckCircle, tone: 'text-blue-400' },
          { label: 'Active VCCs', value: activeVccs.length, icon: CreditCard, tone: 'text-yellow-400' },
        ].map(({ label, value, icon: Icon, tone }) => (
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

      <div className="grid gap-4 xl:grid-cols-[minmax(0,350px)_minmax(0,1fr)]">
        <Card className="bg-[var(--bg-pane)]/60">
          <div className="space-y-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Settings</div>
            </div>
            <div className="space-y-2">
              <div>
                <div className="text-xs text-[var(--text-muted)] mb-1">VCC Card</div>
                <select className="input w-full text-xs" value={selectedVcc || ''} onChange={e => setSelectedVcc(e.target.value ? parseInt(e.target.value) : null)}>
                  <option value="">Auto (next active)</option>
                  {activeVccs.map(v => (
                    <option key={v.id} value={v.id}>{v.number} | {v.billing_country} | {v.label || '-'}</option>
                  ))}
                </select>
              </div>
              <label className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                <input type="checkbox" checked={headless} onChange={e => setHeadless(e.target.checked)} />
                Headless mode
              </label>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={selectAllUpgradeable} className="flex-1">Select All</Button>
                <Button size="sm" variant="outline" onClick={() => setSelectedAccounts([])} className="flex-1">Clear</Button>
              </div>
              <Button size="sm" onClick={runUpgrade} disabled={running || selectedAccounts.length === 0} className="w-full">
                <Zap className={`h-4 w-4 mr-1.5 ${running ? 'animate-spin' : ''}`} />
                {running ? 'Upgrading...' : `Upgrade ${selectedAccounts.length} accounts`}
              </Button>
            </div>

            {results.length > 0 && (
              <div className="border-t border-[var(--border-soft)] pt-3 space-y-1">
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Results</div>
                {results.map((r, i) => (
                  <div key={i} className={`text-xs p-1.5 rounded ${r.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {r.ok ? `✓ Account ${r.account_id}` : `✗ ${r.account_id ? `Account ${r.account_id}: ` : ''}${r.error}`}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card className="overflow-x-auto bg-[var(--bg-pane)]/60">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-soft)] text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
                <th className="py-2 px-2 text-left w-8"></th>
                <th className="py-2 px-2 text-left">Email</th>
                <th className="py-2 px-2 text-left">Plan</th>
                <th className="py-2 px-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a: any) => (
                <tr key={a.id} className={`border-b border-[var(--border-soft)]/50 hover:bg-[var(--bg-hover)] ${selectedAccounts.includes(a.id) ? 'bg-[var(--accent)]/5' : ''}`} onClick={() => a.upgradeable && toggleAccount(a.id)} style={{cursor: a.upgradeable ? 'pointer' : 'default'}}>
                  <td className="py-2 px-2">
                    {a.upgradeable && <input type="checkbox" checked={selectedAccounts.includes(a.id)} onChange={() => toggleAccount(a.id)} />}
                  </td>
                  <td className="py-2 px-2 text-xs font-mono">{a.email}</td>
                  <td className="py-2 px-2 text-xs">{a.plan}</td>
                  <td className="py-2 px-2">
                    {a.upgradeable ? <Badge variant="secondary">Upgradeable</Badge> : <Badge variant="default">Pro</Badge>}
                  </td>
                </tr>
              ))}
              {accounts.length === 0 && (
                <tr><td colSpan={4} className="py-8 text-center text-sm text-[var(--text-muted)]">No accounts for {platform}</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
