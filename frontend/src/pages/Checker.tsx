import { useState } from 'react'
import { apiFetch } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, AlertCircle, Zap } from 'lucide-react'

export default function Checker() {
  const [input, setInput] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [checking, setChecking] = useState(false)

  const check = async () => {
    if (!input.trim()) return
    setChecking(true)
    const lines = input.trim().split('\n').filter(Boolean)
    const newResults: any[] = []
    for (const line of lines) {
      const parts = line.split('|').map(s => s.trim())
      if (parts.length < 4) {
        newResults.push({ card: line, status: 'invalid', message: 'Format: number|month|year|cvc' })
        continue
      }
      try {
        const res = await apiFetch('/bin/check', {
          method: 'POST',
          body: JSON.stringify({ number: parts[0], exp_month: parseInt(parts[1]), exp_year: parseInt(parts[2]), cvc: parts[3] }),
        })
        newResults.push({ card: `****${parts[0].slice(-4)}`, ...res })
      } catch (e: any) {
        newResults.push({ card: `****${parts[0].slice(-4)}`, status: 'error', message: e.message })
      }
    }
    setResults(newResults)
    setChecking(false)
  }

  const liveCount = results.filter(r => r.live).length
  const deadCount = results.filter(r => r.status === 'Die' || (!r.live && r.status !== 'error' && r.status !== 'invalid')).length
  const errorCount = results.filter(r => r.status === 'error' || r.status === 'invalid').length

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-[var(--text-primary)]">Card Checker</div>
            {results.length > 0 && (
              <>
                <Badge variant="default">{results.length} checked</Badge>
                <Badge variant="secondary" className="text-emerald-400">{liveCount} live</Badge>
                <Badge variant="secondary" className="text-red-400">{deadCount} dead</Badge>
              </>
            )}
          </div>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,400px)_minmax(0,1fr)]">
        <Card className="bg-[var(--bg-pane)]/60">
          <div className="space-y-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">Input Cards</div>
              <div className="mt-1 text-sm font-medium text-[var(--text-primary)]">One card per line</div>
            </div>
            <textarea
              className="input w-full h-48 text-xs font-mono"
              placeholder={"4111111111111111|12|2029|123\n5154620022947715|03|2031|694"}
              value={input}
              onChange={e => setInput(e.target.value)}
            />
            <div className="text-xs text-[var(--text-muted)]">Format: number|month|year|cvc</div>
            <Button size="sm" onClick={check} disabled={checking} className="w-full">
              <Zap className={`h-4 w-4 mr-1.5 ${checking ? 'animate-spin' : ''}`} />
              {checking ? 'Checking...' : `Check ${input.trim().split('\n').filter(Boolean).length} cards`}
            </Button>
          </div>
        </Card>

        <Card className="overflow-x-auto bg-[var(--bg-pane)]/60">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-soft)] text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
                <th className="py-2 px-3 text-left">Card</th>
                <th className="py-2 px-3 text-left">Status</th>
                <th className="py-2 px-3 text-left">Message</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="border-b border-[var(--border-soft)]/50">
                  <td className="py-2 px-3 font-mono text-xs">{r.card}</td>
                  <td className="py-2 px-3">
                    {r.live ? <span className="flex items-center gap-1 text-emerald-400"><CheckCircle className="h-4 w-4" /> Live</span> :
                     r.status === 'error' || r.status === 'invalid' ? <span className="flex items-center gap-1 text-yellow-400"><AlertCircle className="h-4 w-4" /> {r.status}</span> :
                     <span className="flex items-center gap-1 text-red-400"><XCircle className="h-4 w-4" /> Dead</span>}
                  </td>
                  <td className="py-2 px-3 text-xs text-[var(--text-muted)]">{r.message || '-'}</td>
                </tr>
              ))}
              {results.length === 0 && (
                <tr><td colSpan={3} className="py-8 text-center text-sm text-[var(--text-muted)]">Paste cards and click Check</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
