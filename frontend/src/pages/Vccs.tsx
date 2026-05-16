import { useEffect, useState } from 'react'
import { apiFetch } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Trash2, CreditCard, CheckCircle, XCircle, Clock, Search, Zap, Eye, EyeOff } from 'lucide-react'

export default function Vccs() {
  const [vccs, setVccs] = useState<any[]>([])
  const [form, setForm] = useState({ number: '', exp_month: '', exp_year: '', cvc: '', billing_country: 'US', label: '' })
  const [bulkText, setBulkText] = useState('')
  const [binInput, setBinInput] = useState('')
  const [binCount, setBinCount] = useState('10')
  const [binCountry, setBinCountry] = useState('US')
  const [binSave, setBinSave] = useState(true)
  const [binCheckLive, setBinCheckLive] = useState(true)
  const [binResult, setBinResult] = useState<any>(null)
  const [binLookup, setBinLookup] = useState<any>(null)
  const [generating, setGenerating] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [expandedDetail, setExpandedDetail] = useState<any>(null)

  const load = () => apiFetch('/vccs').then((d: any) => setVccs(d.vccs || []))

  useEffect(() => { load() }, [])

  const add = async () => {
    if (!form.number.trim()) return
    await apiFetch('/vccs', {
      method: 'POST',
      body: JSON.stringify({
        ...form,
        exp_month: parseInt(form.exp_month) || 1,
        exp_year: parseInt(form.exp_year) || 2029,
      }),
    })
    setForm({ number: '', exp_month: '', exp_year: '', cvc: '', billing_country: 'US', label: '' })
    load()
  }

  const bulkAdd = async () => {
    if (!bulkText.trim()) return
    const lines = bulkText.trim().split('\n').filter(Boolean)
    const vccs = lines.map(line => {
      const parts = line.split('|').map(s => s.trim())
      return {
        number: parts[0] || '',
        exp_month: parseInt(parts[1]) || 1,
        exp_year: parseInt(parts[2]) || 2029,
        cvc: parts[3] || '',
        billing_country: parts[4] || 'US',
        label: parts[5] || '',
      }
    })
    await apiFetch('/vccs/batch', { method: 'POST', body: JSON.stringify(vccs) })
    setBulkText('')
    load()
  }

  const del = async (id: number) => {
    await apiFetch(`/vccs/${id}`, { method: 'DELETE' })
    load()
  }

  const toggleDetail = async (id: number) => {
    if (expandedId === id) {
      setExpandedId(null)
      setExpandedDetail(null)
      return
    }
    const res = await apiFetch(`/vccs/${id}`)
    setExpandedDetail(res.vcc || res)
    setExpandedId(id)
  }

  const genCards = async () => {
    if (!binInput.trim()) return
    setGenerating(true)
    try {
      const res = await apiFetch('/bin/generate', {
        method: 'POST',
        body: JSON.stringify({
          bin: binInput.trim(),
          count: parseInt(binCount) || 10,
          save_to_pool: binSave,
          check_live: binCheckLive,
          billing_country: binCountry,
        }),
      })
      setBinResult(res)
      if (binSave) load()
    } catch (e: any) {
      setBinResult({ ok: false, error: e.message })
    }
    setGenerating(false)
  }

  const lookupBin = async () => {
    if (!binInput.trim()) return
    try {
      const res = await apiFetch('/bin/lookup', {
        method: 'POST',
        body: JSON.stringify({ bin: binInput.trim() }),
      })
      setBinLookup(res?.data || res)
    } catch (e: any) {
      setBinLookup({ error: e.message })
    }
  }

  const statusIcon = (status: string) => {
    if (status === 'active') return <CheckCircle className="h-4 w-4 text-emerald-400" />
    if (status === 'declined') return <XCircle className="h-4 w-4 text-red-400" />
    return <Clock className="h-4 w-4 text-yellow-400" />
  }

  const activeCount = vccs.filter(v => v.status === 'active').length

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-[var(--text-primary)]">VCC Pool</div>
            <Badge variant="default">Total {vccs.length}</Badge>
            <Badge variant="secondary">Active {activeCount}</Badge>
          </div>
        </div>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Total Cards', value: vccs.length, icon: CreditCard, tone: 'text-[var(--accent)]' },
          { label: 'Active', value: activeCount, icon: CheckCircle, tone: 'text-emerald-400' },
          { label: 'Declined', value: vccs.filter(v => v.status === 'declined').length, icon: XCircle, tone: 'text-red-400' },
          { label: 'Used', value: vccs.filter(v => v.used_by).length, icon: Clock, tone: 'text-yellow-400' },
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

      <div className="grid gap-4 xl:grid-cols-[minmax(0,400px)_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card className="bg-[var(--bg-pane)]/60">
            <div className="space-y-4">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">BIN Generator</div>
                <div className="mt-1 text-sm font-medium text-[var(--text-primary)]">Generate cards from BIN prefix</div>
              </div>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input className="input flex-1" placeholder="BIN (6-8 digits)" value={binInput} onChange={e => setBinInput(e.target.value)} />
                  <Button variant="outline" size="sm" onClick={lookupBin}><Search className="h-4 w-4" /></Button>
                </div>
                {binLookup && !binLookup.error && (
                  <div className="text-xs text-[var(--text-muted)] bg-[var(--chip-bg)] p-2 rounded">
                    {binLookup.brand} | {binLookup.type} | {binLookup.country_name || binLookup.country} | {binLookup.bank || '-'}
                  </div>
                )}
                <div className="grid grid-cols-3 gap-2">
                  <input className="input" placeholder="Count" value={binCount} onChange={e => setBinCount(e.target.value)} />
                  <input className="input" placeholder="Country" value={binCountry} onChange={e => setBinCountry(e.target.value)} />
                  <div className="flex flex-col gap-1">
                    <label className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <input type="checkbox" checked={binSave} onChange={e => setBinSave(e.target.checked)} />
                      Save to pool
                    </label>
                    <label className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <input type="checkbox" checked={binCheckLive} onChange={e => setBinCheckLive(e.target.checked)} />
                      Check live
                    </label>
                  </div>
                </div>
                <Button size="sm" onClick={genCards} disabled={generating} className="w-full">
                  <Zap className={`h-4 w-4 mr-1.5 ${generating ? 'animate-spin' : ''}`} />
                  {generating ? 'Generating...' : 'Generate Cards'}
                </Button>
                {binResult && (
                  <div className={`text-xs p-2 rounded ${binResult.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {binResult.ok ? `Generated ${binResult.count} cards | Live: ${binResult.live ?? '?'} | Dead: ${binResult.dead ?? '?'}${binResult.errors ? ` | Errors: ${binResult.errors}` : ''}${binResult.saved ? ` | Saved: ${binResult.saved_count}` : ''}` : binResult.error}
                  </div>
                )}
              </div>
            </div>
          </Card>

          <Card className="bg-[var(--bg-pane)]/60">
            <div className="space-y-4">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Add VCC</div>
                <div className="mt-1 text-sm font-medium text-[var(--text-primary)]">Single card or bulk import</div>
              </div>
              <div className="space-y-2">
                <input className="input w-full" placeholder="Card number" value={form.number} onChange={e => setForm({ ...form, number: e.target.value })} />
                <div className="grid grid-cols-3 gap-2">
                  <input className="input" placeholder="MM" value={form.exp_month} onChange={e => setForm({ ...form, exp_month: e.target.value })} />
                  <input className="input" placeholder="YYYY" value={form.exp_year} onChange={e => setForm({ ...form, exp_year: e.target.value })} />
                  <input className="input" placeholder="CVC" value={form.cvc} onChange={e => setForm({ ...form, cvc: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input className="input" placeholder="Country (US)" value={form.billing_country} onChange={e => setForm({ ...form, billing_country: e.target.value })} />
                  <input className="input" placeholder="Label (optional)" value={form.label} onChange={e => setForm({ ...form, label: e.target.value })} />
                </div>
                <Button size="sm" onClick={add} className="w-full"><Plus className="h-4 w-4 mr-1.5" />Add Card</Button>
              </div>
              <div className="border-t border-[var(--border-soft)] pt-3">
                <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)] mb-2">Bulk Import</div>
                <div className="text-xs text-[var(--text-muted)] mb-1">Format: number|month|year|cvc|country|label</div>
                <textarea className="input w-full h-20 text-xs" placeholder="4111111111111111|12|2029|123|US|card1" value={bulkText} onChange={e => setBulkText(e.target.value)} />
                <Button size="sm" variant="outline" onClick={bulkAdd} className="w-full mt-2">Bulk Import</Button>
              </div>
            </div>
          </Card>
        </div>

        <Card className="overflow-x-auto bg-[var(--bg-pane)]/60">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-soft)] text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
                <th className="py-2 px-2 text-left">Card</th>
                <th className="py-2 px-2 text-left">Exp</th>
                <th className="py-2 px-2 text-left">Country</th>
                <th className="py-2 px-2 text-left">Status</th>
                <th className="py-2 px-2 text-left">Used By</th>
                <th className="py-2 px-2 text-left">Label</th>
                <th className="py-2 px-2"></th>
              </tr>
            </thead>
            <tbody>
              {vccs.map((v: any) => (
                <>
                <tr key={v.id} className="border-b border-[var(--border-soft)]/50 hover:bg-[var(--bg-hover)]">
                  <td className="py-2 px-2 font-mono text-xs">{v.number}</td>
                  <td className="py-2 px-2 text-xs">{String(v.exp_month).padStart(2, '0')}/{v.exp_year}</td>
                  <td className="py-2 px-2 text-xs">{v.billing_country}</td>
                  <td className="py-2 px-2">{statusIcon(v.status)}</td>
                  <td className="py-2 px-2 text-xs text-[var(--text-muted)]">{v.used_by || '-'}</td>
                  <td className="py-2 px-2 text-xs text-[var(--text-muted)]">{v.label || '-'}</td>
                  <td className="py-2 px-2 flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => toggleDetail(v.id)}>
                      {expandedId === v.id ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => del(v.id)}><Trash2 className="h-3.5 w-3.5 text-red-400" /></Button>
                  </td>
                </tr>
                {expandedId === v.id && expandedDetail && (
                  <tr key={`${v.id}-detail`} className="bg-[var(--bg-hover)]">
                    <td colSpan={7} className="py-2 px-4">
                      <div className="flex gap-4 text-xs font-mono">
                        <span><b>Number:</b> {expandedDetail.number}</span>
                        <span><b>CVC:</b> {expandedDetail.cvc}</span>
                        <span><b>Exp:</b> {String(expandedDetail.exp_month).padStart(2,'0')}/{expandedDetail.exp_year}</span>
                        <span><b>Address:</b> {expandedDetail.billing_line1}, {expandedDetail.billing_city}, {expandedDetail.billing_state} {expandedDetail.billing_postal_code}</span>
                      </div>
                    </td>
                  </tr>
                )}
                </>
              ))}
              {vccs.length === 0 && (
                <tr><td colSpan={7} className="py-8 text-center text-sm text-[var(--text-muted)]">No VCC cards added yet</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
