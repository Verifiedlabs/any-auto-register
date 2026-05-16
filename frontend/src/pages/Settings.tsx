import { useEffect, useState } from 'react'
import { getConfig, getConfigOptions, getPlatforms, invalidateConfigCache, invalidateConfigOptionsCache, invalidatePlatformsCache } from '@/lib/app-data'
import type { ChoiceOption, ConfigOptionsResponse, ProviderDriver, ProviderField as ProviderFieldDef, ProviderOption, ProviderSetting } from '@/lib/config-options'
import { getCaptchaStrategyLabel } from '@/lib/config-options'
import { apiFetch } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Save, Eye, EyeOff, Mail, Shield, Cpu, Sliders, Plus, X, Orbit, Package2, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import ProviderCards from '@/components/settings/ProviderCards'

const PROVIDER_TYPES = ['mailbox', 'captcha', 'sms'] as const

type ProviderType = typeof PROVIDER_TYPES[number]

const PROVIDER_META: Record<ProviderType, {
  tabLabel: string
  icon: any
  detailTitle: string
  addTitle: string
  createTitle: string
  addDialogHint: string
  usageHint: string
  usageHintClassName: string
  listTitle: string
  listDescription: (count: number) => string
  noAvailableText: string
  availableText: (count: number) => string
  emptyText: string
  metricLabel: string
}> = {
   mailbox: {
     tabLabel: 'Email Service',
     icon: Mail,
     detailTitle: 'Email Provider Details',
     addTitle: 'Add Email Provider',
     createTitle: 'Create Dynamic Email Provider',
     addDialogHint: 'Select from email provider catalog',
     usageHint: 'Email service configuration here is only used when "System Email" is selected as the registration identity. You can view details, edit, set default, and delete directly in the list.',
     usageHintClassName: 'rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-[var(--text-secondary)]',
     listTitle: 'Email Provider List',
     listDescription: (count: number) => `${count} configurations, support viewing details, editing, setting default, and deleting.`,
     noAvailableText: 'No email providers available to add',
     availableText: (count: number) => `${count} email providers available to add`,
     emptyText: 'No email provider configuration. Please add one first.',
     metricLabel: 'Email Service',
   },
   captcha: {
     tabLabel: 'Verification Service',
     icon: Shield,
     detailTitle: 'Verification Provider Details',
     addTitle: 'Add Verification Provider',
     createTitle: 'Create Dynamic Verification Provider',
     addDialogHint: 'Select from verification provider catalog',
     usageHint: 'Protocol mode automatically selects remote captcha service in enabled order; browser mode uses the current default verification provider. You can view details, edit, set default, and delete directly in the list.',
     usageHintClassName: 'rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-[var(--text-secondary)]',
     listTitle: 'Verification Provider List',
     listDescription: (count: number) => `${count} configurations, protocol mode will read available items here in order.`,
     noAvailableText: 'No verification providers available to add',
     availableText: (count: number) => `${count} verification providers available to add`,
     emptyText: 'No verification provider configuration. Please add one first.',
     metricLabel: 'Verification Service',
   },
   sms: {
     tabLabel: 'SMS Service',
     icon: MessageSquare,
     detailTitle: 'SMS Provider Details',
     addTitle: 'Add SMS Provider',
     createTitle: 'Create Dynamic SMS Provider',
     addDialogHint: 'Select from SMS provider catalog',
     usageHint: 'When the platform requires phone verification, temporary numbers will be created using enabled SMS providers here and SMS verification codes will be filled back. You can view details, edit, set default, and delete directly in the list.',
     usageHintClassName: 'rounded-lg border border-sky-500/20 bg-sky-500/10 px-4 py-3 text-sm text-[var(--text-secondary)]',
     listTitle: 'SMS Provider List',
     listDescription: (count: number) => `${count} configurations, phone and SMS verification will prioritize using the default item here.`,
     noAvailableText: 'No SMS providers available to add',
     availableText: (count: number) => `${count} SMS providers available to add`,
     emptyText: 'No SMS provider configuration. Please add one first.',
     metricLabel: 'SMS Service',
   },
 }

function SettingsMetric({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string | number
  icon: any
}) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-pane)]/58 px-3 py-2.5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] tracking-[0.16em] text-[var(--text-muted)]">{label}</div>
          <div className="mt-0.5 text-lg font-semibold tracking-[-0.03em] text-[var(--text-primary)]">{value}</div>
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-[12px] border border-[var(--border-soft)] bg-[var(--chip-bg)] text-[var(--accent)]">
          <Icon className="h-3.5 w-3.5" />
        </div>
      </div>
    </div>
  )
}

function PlatformCapsTab() {
  const [platforms, setPlatforms] = useState<any[]>([])
  const [drafts, setDrafts] = useState<Record<string, any>>({})
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const [saved, setSaved] = useState<Record<string, boolean>>({})

  useEffect(() => {
    getPlatforms().then((list: any[]) => {
      setPlatforms(list)
      const init: Record<string, any> = {}
      list.forEach(p => {
        init[p.name] = {
          supported_executors: [...p.supported_executors],
          supported_identity_modes: [...p.supported_identity_modes],
          supported_oauth_providers: [...p.supported_oauth_providers],
        }
      })
      setDrafts(init)
    })
  }, [])

  const toggle = (name: string, field: string, value: string) => {
    setDrafts(d => {
      const arr: string[] = [...(d[name]?.[field] || [])]
      const idx = arr.indexOf(value)
      if (idx >= 0) arr.splice(idx, 1); else arr.push(value)
      return { ...d, [name]: { ...d[name], [field]: arr } }
    })
  }

  const save = async (name: string) => {
    setSaving(s => ({ ...s, [name]: true }))
    try {
      await apiFetch(`/platforms/${name}/capabilities`, { method: 'PUT', body: JSON.stringify(drafts[name]) })
      invalidatePlatformsCache()
      setSaved(s => ({ ...s, [name]: true }))
      setTimeout(() => setSaved(s => ({ ...s, [name]: false })), 2000)
    } finally { setSaving(s => ({ ...s, [name]: false })) }
  }

  const reset = async (name: string) => {
    await apiFetch(`/platforms/${name}/capabilities`, { method: 'DELETE' })
    invalidatePlatformsCache()
    const list = await getPlatforms({ force: true })
    const p = list.find((x: any) => x.name === name)
    if (p) setDrafts(d => ({
      ...d,
      [name]: {
        supported_executors: [...p.supported_executors],
        supported_identity_modes: [...p.supported_identity_modes],
        supported_oauth_providers: [...p.supported_oauth_providers],
      },
    }))
  }

  return (
    <div className="space-y-4">
      {platforms.map(p => {
        const draft = drafts[p.name] || {}
        const executors: string[] = draft.supported_executors || []
        const modes: string[] = draft.supported_identity_modes || []
        const oauths: string[] = draft.supported_oauth_providers || []
        const executorOptions: ChoiceOption[] = p.supported_executor_options || []
        const identityOptions: ChoiceOption[] = p.supported_identity_mode_options || []
        const oauthOptions: ChoiceOption[] = p.supported_oauth_provider_options || []
        return (
          <div key={p.name} className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">{p.display_name}</h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">{p.name} v{p.version}</p>
              </div>
              <button onClick={() => reset(p.name)}
                className="table-action-btn">
                 Restore Default
              </button>
            </div>
            <div className="space-y-3">
              <div>
                 <p className="text-xs text-[var(--text-muted)] mb-2">Executor Type</p>
                <div className="flex flex-wrap gap-4">
                  {executorOptions.map(option => (
                    <label key={option.value} className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] cursor-pointer">
                      <input type="checkbox" checked={executors.includes(option.value)}
                        onChange={() => toggle(p.name, 'supported_executors', option.value)}
                        className="checkbox-accent" />
                      {option.label}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                 <p className="text-xs text-[var(--text-muted)] mb-2">Registration Identity</p>
                <div className="flex gap-4">
                  {identityOptions.map(option => (
                    <label key={option.value} className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] cursor-pointer">
                      <input type="checkbox" checked={modes.includes(option.value)}
                        onChange={() => toggle(p.name, 'supported_identity_modes', option.value)}
                        className="checkbox-accent" />
                      {option.label}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                 <p className="text-xs text-[var(--text-muted)] mb-2">Third-party Entry</p>
                <div className="flex flex-wrap gap-4">
                  {oauthOptions.map(option => (
                    <label key={option.value} className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] cursor-pointer">
                      <input type="checkbox" checked={oauths.includes(option.value)}
                        onChange={() => toggle(p.name, 'supported_oauth_providers', option.value)}
                        className="checkbox-accent" />
                      {option.label}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-4">
              <Button size="sm" onClick={() => save(p.name)} disabled={saving[p.name]}>
                <Save className="h-3.5 w-3.5 mr-1" />
                 {saved[p.name] ? 'Saved ✓' : saving[p.name] ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

const TABS: { id: string; label: string; icon: any; sections?: any[] }[] = [
  {
    id: 'register', label: 'Registration Strategy', icon: Cpu,
    sections: [{
      section: 'Default Registration Strategy',
      desc: 'Default behavior configured here will be reused directly in account list and registration page.',
      items: [
        { key: 'default_identity_provider', label: 'Default Registration Identity' },
        { key: 'default_oauth_provider', label: 'Default Third-party Entry', placeholder: '' },
        { key: 'default_executor', label: 'Default Execution Method' },
      ],
    }, {
      section: 'Browser Reuse',
      desc: 'When using background browser for third-party accounts, you typically need to reuse the locally logged-in browser.',
      items: [
        { key: 'oauth_email_hint', label: 'Expected login email', placeholder: 'your-account@example.com' },
        { key: 'chrome_user_data_dir', label: 'Chrome Profile path', placeholder: '~/Library/Application Support/Google/Chrome' },
        { key: 'chrome_cdp_url', label: 'Chrome CDP address', placeholder: 'http://localhost:9222' },
      ],
    }],
  },
  {
    id: 'mailbox', label: PROVIDER_META.mailbox.tabLabel, icon: PROVIDER_META.mailbox.icon,
    sections: [],
  },
  {
    id: 'captcha', label: PROVIDER_META.captcha.tabLabel, icon: PROVIDER_META.captcha.icon,
    sections: [],
  },
  {
    id: 'sms', label: PROVIDER_META.sms.tabLabel, icon: PROVIDER_META.sms.icon,
    sections: [],
  },
  {
    id: 'platform_caps', label: 'Advanced: Platform Capabilities', icon: Sliders,
    sections: [],
  },
  {
    id: 'chatgpt', label: 'ChatGPT', icon: Shield,
    sections: [{
      section: 'CPA Panel',
      desc: 'Auto upload to CPA management platform after registration',
      items: [
        { key: 'cpa_api_url', label: 'API URL', placeholder: 'https://your-cpa.example.com' },
        { key: 'cpa_api_key', label: 'API Key', secret: true },
      ],
    }, {
      section: 'Team Manager',
      desc: 'Upload to self-hosted Team Manager system',
      items: [
        { key: 'team_manager_url', label: 'API URL', placeholder: 'https://your-tm.example.com' },
        { key: 'team_manager_key', label: 'API Key', secret: true },
      ],
    }, {
      section: 'Any2Api',
      desc: 'Sync accounts to Any2Api service for export and integration',
      items: [
        { key: 'any2api_url', label: 'API URL', placeholder: 'https://your-any2api.example.com' },
        { key: 'any2api_password', label: 'Password', secret: true },
      ],
    }],
  },
]

function Field({ field, form, setForm, showSecret, setShowSecret, selectOptions }: any) {
  const { key, label, placeholder, secret } = field
  const options = (field.options && field.options.length > 0)
    ? field.options
    : ((selectOptions && selectOptions.length > 0) ? selectOptions : null)
  return (
    <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5 last:border-0">
      <label className="text-sm text-[var(--text-secondary)] font-medium">{label}</label>
      <div className="col-span-2 relative">
        {options ? (
          <select
            value={form[key] || options[0].value}
            onChange={e => setForm((f: any) => ({ ...f, [key]: e.target.value }))}
            className="control-surface appearance-none"
          >
            {options.map((o: any) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ) : (
          <>
            <input
              type={secret && !showSecret[key] ? 'password' : 'text'}
              value={form[key] || ''}
              onChange={e => setForm((f: any) => ({ ...f, [key]: e.target.value }))}
              placeholder={placeholder}
              className="control-surface pr-10"
            />
            {secret && (
              <button
                onClick={() => setShowSecret((s: any) => ({ ...s, [key]: !s[key] }))}
                className="absolute right-3 top-2.5 text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
              >
                {showSecret[key] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function ProviderField({ field, value, onChange, showSecret, setShowSecret, secretKey, disabled = false }: any) {
  const { label, placeholder, secret, type, options } = field
  return (
    <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5 last:border-0">
      <label className="text-sm text-[var(--text-secondary)] font-medium">{label}</label>
      <div className="col-span-2 relative">
        {type === 'select' && options?.length ? (
          <select
            value={value || options[0]?.value || ''}
            onChange={e => onChange(e.target.value)}
            disabled={disabled}
            className="control-surface appearance-none disabled:opacity-70"
          >
            {options.map((o: any) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ) : type === 'textarea' ? (
          <textarea
            value={value || ''}
            onChange={e => onChange(e.target.value)}
            disabled={disabled}
            placeholder={placeholder}
            rows={3}
            className="control-surface pr-10 disabled:opacity-70 resize-y"
          />
        ) : (
          <>
            <input
              type={secret && !showSecret[secretKey] ? 'password' : 'text'}
              value={value || ''}
              onChange={e => onChange(e.target.value)}
              disabled={disabled}
              placeholder={placeholder}
              autoComplete="new-password"
              data-1p-ignore
              data-lpignore="true"
              className="control-surface pr-10 disabled:opacity-70"
            />
            {secret && (
              <button
                onClick={() => setShowSecret((s: any) => ({ ...s, [secretKey]: !s[secretKey] }))}
                disabled={disabled}
                className="absolute right-3 top-2.5 text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
              >
                {showSecret[secretKey] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function HeroSmsTools({ item }: { item: ProviderSetting }) {
  const [loading, setLoading] = useState('')
  const [message, setMessage] = useState('')

  const payload = () => ({
    api_key: item.auth?.herosms_api_key || '',
    service: item.config?.sms_service || 'dr',
    country: item.config?.sms_country || '187',
  })

  const queryBalance = async () => {
    setLoading('balance')
    setMessage('')
    try {
      const data = await apiFetch('/sms/herosms/balance', {
        method: 'POST',
        body: JSON.stringify(payload()),
      })
      setMessage(`Balance: $${Number(data.balance ?? 0).toFixed(3)}`)
    } catch (e: any) {
      setMessage(e.message || 'Balance query failed')
    } finally {
      setLoading('')
    }
  }

  const queryPrice = async () => {
    setLoading('price')
    setMessage('')
    try {
      const data = await apiFetch('/sms/herosms/prices', {
        method: 'POST',
        body: JSON.stringify(payload()),
      })
      const prices = data.prices || {}
      const country = payload().country
      const service = payload().service
      const current = prices?.[country]?.[service]
      if (current) {
        setMessage(`Current price: $${current.cost}, Available count: ${current.count}`)
      } else {
        setMessage('Price info not found for current service/country')
      }
    } catch (e: any) {
      setMessage(e.message || 'Price query failed')
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="rounded-xl border border-sky-500/20 bg-sky-500/10 px-3 py-3 text-xs text-[var(--text-secondary)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-medium text-[var(--text-primary)]">HeroSMS Tool</div>
          <div className="mt-1 text-[var(--text-muted)]">Query balance/price using current API Key, service code and country ID.</div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={queryBalance} disabled={Boolean(loading)}>
             {loading === 'balance' ? 'Querying...' : 'Check Balance'}
          </Button>
          <Button size="sm" variant="outline" onClick={queryPrice} disabled={Boolean(loading)}>
             {loading === 'price' ? 'Querying...' : 'Check Price'}
          </Button>
        </div>
      </div>
      {message ? <div className="mt-2 text-[var(--text-primary)]">{message}</div> : null}
    </div>
  )
}

function ProviderDetailModal({
  title,
  item,
  readOnly,
  saving,
  saved,
  showSecret,
  setShowSecret,
  onClose,
  onEdit,
  onChangeName,
  onChangeAuthMode,
  onChangeField,
  onSave,
}: any) {
  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog-panel dialog-panel-md flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">{title}</h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{item.display_name || item.catalog_label} · {item.provider_key}</p>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"><X className="h-4 w-4" /></button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[var(--border)] bg-[var(--bg-hover)] px-2 py-0.5 text-[11px] text-[var(--text-secondary)]">
               {item.auth_modes.find((mode: any) => mode.value === item.auth_mode)?.label || item.auth_mode || 'No auth mode set'}
            </span>
            {item.is_default ? (
               <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] text-emerald-300">Default Provider</span>
            ) : null}
          </div>
          {item.description ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-hover)] px-3 py-2 text-xs text-[var(--text-secondary)]">
              {item.description}
            </div>
          ) : null}
          {item.provider_type === 'sms' && item.provider_key === 'herosms' ? (
            <HeroSmsTools item={item} />
          ) : null}
          <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
              <label className="text-sm text-[var(--text-secondary)] font-medium">Config Name</label>
            <div className="col-span-2">
              <input
                type="text"
                value={item.display_name || ''}
                onChange={e => onChangeName(e.target.value)}
                disabled={readOnly}
                placeholder={item.catalog_label}
                className="control-surface disabled:opacity-70"
              />
            </div>
          </div>
          {item.auth_modes?.length > 0 && (
             <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
               <label className="text-sm text-[var(--text-secondary)] font-medium">Auth Mode</label>
               <div className="col-span-2">
                 <select
                   value={item.auth_mode}
                   onChange={e => onChangeAuthMode(e.target.value)}
                   disabled={readOnly}
                   className="control-surface appearance-none disabled:opacity-70"
                 >
                  {item.auth_modes.map((mode: any) => <option key={mode.value} value={mode.value}>{mode.label}</option>)}
                </select>
              </div>
            </div>
          )}
          {item.fields.length === 0 ? (
             <div className="text-sm text-[var(--text-muted)] py-3">This provider requires no additional configuration.</div>
          ) : (
            <GroupedProviderFields
              fields={item.fields}
              getValue={(field: ProviderFieldDef) => field.category === 'auth' ? item.auth?.[field.key] : item.config?.[field.key]}
              onChangeField={(field: ProviderFieldDef, value: string) => onChangeField(field, value)}
              showSecret={showSecret}
              setShowSecret={setShowSecret}
              secretKeyPrefix={item.provider_key}
              disabled={readOnly}
            />
          )}
        </div>
        <div className="flex-shrink-0 flex gap-3 px-6 py-4 border-t border-[var(--border)]">
          {readOnly ? (
            <>
             <Button onClick={onEdit} className="flex-1">Switch to Edit</Button>
             <Button variant="outline" onClick={onClose} className="flex-1">Close</Button>
            </>
           ) : (
             <>
               <Button onClick={onSave} disabled={saving} className="flex-1">
                 <Save className="h-4 w-4 mr-2" />
                  {saved ? 'Saved ✓' : saving ? 'Saving...' : 'Save'}
               </Button>
               <Button variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function AddProviderModal({
  title,
  subtitle,
  providers,
  selectedKey,
  creating,
  onSelect,
  onClose,
  onCreate,
}: any) {
  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog-panel dialog-panel-sm" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">{title}</h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{subtitle}</p>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"><X className="h-4 w-4" /></button>
        </div>
        <div className="px-6 py-4">
          {providers.length === 0 ? (
            <div className="empty-state-panel">
               All available providers have been added to the list.
            </div>
          ) : (
            <div className="space-y-3">
               <label className="block text-sm text-[var(--text-secondary)]">Select Provider</label>
              <select
                value={selectedKey}
                onChange={e => onSelect(e.target.value)}
                className="control-surface appearance-none"
              >
                {providers.map((provider: ProviderOption) => (
                  <option key={provider.value} value={provider.value}>{provider.label}</option>
                ))}
              </select>
              {providers.find((provider: ProviderOption) => provider.value === selectedKey)?.description ? (
                <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-hover)] px-3 py-2 text-xs text-[var(--text-secondary)]">
                  {providers.find((provider: ProviderOption) => provider.value === selectedKey)?.description}
                </div>
              ) : null}
            </div>
          )}
        </div>
        <div className="flex gap-3 px-6 py-4 border-t border-[var(--border)]">
          <Button
            onClick={() => onCreate(selectedKey)}
            disabled={providers.length === 0 || !selectedKey || creating}
            className="flex-1"
          >
            <Plus className="h-4 w-4 mr-2" />
             {creating ? 'Adding...' : 'Add'}
          </Button>
           <Button variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
         </div>
       </div>
     </div>
   )
 }
 
 const FIELD_CATEGORY_LABELS: Record<string, string> = {
  connection: 'Connection & Endpoint',
  auth: 'Authentication',
  identity: 'Email Identity',
}

function GroupedProviderFields({
  fields,
  getValue,
  onChangeField,
  showSecret,
  setShowSecret,
  secretKeyPrefix,
  disabled = false,
}: {
  fields: ProviderFieldDef[]
  getValue: (field: ProviderFieldDef) => string
  onChangeField: (field: ProviderFieldDef, value: string) => void
  showSecret: Record<string, boolean>
  setShowSecret: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  secretKeyPrefix: string
  disabled?: boolean
}) {
  const grouped = fields.reduce<Record<string, ProviderFieldDef[]>>((acc, field) => {
    const cat = field.category || 'other'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(field)
    return acc
  }, {})

  const categoryOrder = ['auth', 'identity', 'connection', 'other']
  const sortedCategories = Object.keys(grouped).sort((a, b) => {
    const ia = categoryOrder.indexOf(a)
    const ib = categoryOrder.indexOf(b)
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
  })

  return (
    <>
      {sortedCategories.map(cat => (
        <div key={cat}>
          <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mt-4 mb-1 pt-2 border-t border-white/5">
            {FIELD_CATEGORY_LABELS[cat] || cat}
          </div>
          {grouped[cat].map(field => (
            <ProviderField
              key={field.key}
              field={field}
              value={getValue(field)}
              onChange={(value: string) => onChangeField(field, value)}
              showSecret={showSecret}
              setShowSecret={setShowSecret}
              secretKey={`${secretKeyPrefix}:${field.key}`}
              disabled={disabled}
            />
          ))}
        </div>
      ))}
    </>
  )
}

function CreateProviderDefinitionModal({
  title,
  providerType,
  drivers,
  form,
  creating,
  showSecret,
  setShowSecret,
  onChange,
  onClose,
  onCreate,
}: any) {
  const currentDriver = drivers.find((item: ProviderDriver) => item.driver_type === form.driver_type) || null
  const currentAuthModes = currentDriver?.auth_modes || []
  const currentFields = currentDriver?.fields || []

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog-panel dialog-panel-md flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">{title}</h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">Add a dynamic provider definition and create the first available configuration.</p>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"><X className="h-4 w-4" /></button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
          <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
             <label className="text-sm text-[var(--text-secondary)] font-medium">Provider Name</label>
            <div className="col-span-2">
              <input value={form.label} onChange={e => onChange('label', e.target.value)} placeholder="My Provider" className="control-surface" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
            <label className="text-sm text-[var(--text-secondary)] font-medium">Provider Key</label>
            <div className="col-span-2">
              <input value={form.provider_key} onChange={e => onChange('provider_key', e.target.value)} placeholder="my_provider" className="control-surface" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
             <label className="text-sm text-[var(--text-secondary)] font-medium">Description</label>
             <div className="col-span-2">
               <input value={form.description} onChange={e => onChange('description', e.target.value)} placeholder="Optional" className="control-surface" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
             <label className="text-sm text-[var(--text-secondary)] font-medium">Driver Family</label>
            <div className="col-span-2">
              <select value={form.driver_type} onChange={e => onChange('driver_type', e.target.value)} className="control-surface appearance-none">
                {drivers.map((driver: ProviderDriver) => (
                  <option key={driver.driver_type} value={driver.driver_type}>{driver.label}</option>
                ))}
              </select>
              {currentDriver?.description ? <p className="mt-2 text-xs text-[var(--text-muted)]">{currentDriver.description}</p> : null}
            </div>
          </div>
          {currentAuthModes.length > 0 && (
            <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-white/5">
               <label className="text-sm text-[var(--text-secondary)] font-medium">Auth Mode</label>
               <div className="col-span-2">
                 <select value={form.auth_mode} onChange={e => onChange('auth_mode', e.target.value)} className="control-surface appearance-none">
                  {currentAuthModes.map((mode: any) => (
                    <option key={mode.value} value={mode.value}>{mode.label}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
          {currentFields.length === 0 ? (
             <div className="text-sm text-[var(--text-muted)] py-3">This driver family requires no additional configuration fields.</div>
          ) : (
            <GroupedProviderFields
              fields={currentFields}
              getValue={(field: ProviderFieldDef) => field.category === 'auth' ? form.auth[field.key] : form.config[field.key]}
              onChangeField={(field: ProviderFieldDef, value: string) => {
                if (field.category === 'auth') {
                  onChange('auth', { ...form.auth, [field.key]: value })
                } else {
                  onChange('config', { ...form.config, [field.key]: value })
                }
              }}
              showSecret={showSecret}
              setShowSecret={setShowSecret}
              secretKeyPrefix={`create:${providerType}`}
            />
          )}
        </div>
        <div className="flex-shrink-0 flex gap-3 px-6 py-4 border-t border-[var(--border)]">
          <Button onClick={onCreate} disabled={creating} className="flex-1">
            <Plus className="h-4 w-4 mr-2" />
             {creating ? 'Creating...' : 'Create & Enable'}
          </Button>
           <Button variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
         </div>
       </div>
     </div>
   )
 }

export default function Settings({ embedded, defaultTab }: { embedded?: boolean; defaultTab?: string }) {
  const [activeTab, setActiveTab] = useState(defaultTab || 'register')
  const [form, setForm] = useState<Record<string, string>>({})
  const [configOptions, setConfigOptions] = useState<ConfigOptionsResponse>({
    mailbox_providers: [],
    captcha_providers: [],
    sms_providers: [],
    mailbox_drivers: [],
    captcha_drivers: [],
    sms_drivers: [],
    mailbox_settings: [],
    captcha_settings: [],
    sms_settings: [],
    captcha_policy: {},
    executor_options: [],
    identity_mode_options: [],
    oauth_provider_options: [],
  })
  const [providerSettings, setProviderSettings] = useState<Record<ProviderType, ProviderSetting[]>>({ mailbox: [], captcha: [], sms: [] })
  const [newProviderKey, setNewProviderKey] = useState<Record<ProviderType, string>>({ mailbox: '', captcha: '', sms: '' })
  const [providerDialog, setProviderDialog] = useState<{ providerType: ProviderType | null; providerKey: string; readOnly: boolean }>({ providerType: null, providerKey: '', readOnly: false })
  const [providerAddDialog, setProviderAddDialog] = useState<ProviderType | null>(null)
  const [providerCreateDialog, setProviderCreateDialog] = useState<ProviderType | null>(null)
  const [providerDefinitionCreating, setProviderDefinitionCreating] = useState<Record<string, boolean>>({})
  const [providerDefinitionForm, setProviderDefinitionForm] = useState<Record<ProviderType, any>>({
    mailbox: { provider_key: '', label: '', description: '', driver_type: '', auth_mode: '', config: {}, auth: {} },
    captcha: { provider_key: '', label: '', description: '', driver_type: '', auth_mode: '', config: {}, auth: {} },
    sms: { provider_key: '', label: '', description: '', driver_type: '', auth_mode: '', config: {}, auth: {} },
  })
  const [optionsError, setOptionsError] = useState('')
  const [providerNotice, setProviderNotice] = useState<Record<ProviderType, string>>({ mailbox: '', captcha: '', sms: '' })
  const [providerError, setProviderError] = useState<Record<ProviderType, string>>({ mailbox: '', captcha: '', sms: '' })
  const [showSecret, setShowSecret] = useState<Record<string, boolean>>({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [providerSaving, setProviderSaving] = useState<Record<string, boolean>>({})
  const [providerSaved, setProviderSaved] = useState<Record<string, boolean>>({})
  const [_providerDeleting, _setProviderDeleting] = useState<Record<string, boolean>>({})
  const [providerCreating, setProviderCreating] = useState<Record<string, boolean>>({})
  const [solverRunning] = useState<boolean | null>(null)

  const loadConfigData = async () => {
    const [cfg, options] = await Promise.all([
      getConfig().catch(() => ({})),
      getConfigOptions().catch(() => null),
    ])
    setForm(cfg)
    if (options) {
      setConfigOptions(options)
      const nextMailbox = options.mailbox_settings || []
      const nextCaptcha = options.captcha_settings || []
      const nextSms = options.sms_settings || []
      setProviderSettings({
        mailbox: nextMailbox,
        captcha: nextCaptcha,
        sms: nextSms,
      })
      setOptionsError('')
    } else {
      setConfigOptions({
        mailbox_providers: [],
        captcha_providers: [],
        sms_providers: [],
        mailbox_drivers: [],
        captcha_drivers: [],
        sms_drivers: [],
        mailbox_settings: [],
        captcha_settings: [],
        sms_settings: [],
        captcha_policy: {},
        executor_options: [],
        identity_mode_options: [],
        oauth_provider_options: [],
      })
      setProviderSettings({ mailbox: [], captcha: [], sms: [] })
      setOptionsError('Provider metadata not loaded. Please restart backend and refresh page.')
    }
  }

  useEffect(() => {
    loadConfigData()
  }, [])

  // Sync activeTab when defaultTab prop changes (sidebar navigation)
  useEffect(() => {
    if (defaultTab && defaultTab !== activeTab) {
      setActiveTab(defaultTab)
    }
  }, [defaultTab])

  const save = async () => {
    setSaving(true)
    try {
      await apiFetch('/config', { method: 'PUT', body: JSON.stringify({ data: form }) })
      invalidateConfigCache()
      setSaved(true); setTimeout(() => setSaved(false), 2000)
    } finally { setSaving(false) }
  }

  const tab = TABS.find(t => t.id === activeTab) ?? TABS[0]
  const sections = tab.sections ?? []
  const getSelectOptions = (key: string) => {
    if (key === 'default_executor') return configOptions.executor_options || []
    if (key === 'default_identity_provider') return configOptions.identity_mode_options || []
    if (key === 'default_oauth_provider') {
      return [
        { label: 'No pre-selection, choose on current page', value: '' },
        ...((configOptions.oauth_provider_options || []).filter(option => option.value !== '')),
      ]
    }
    return []
  }
  const mailboxCatalog = configOptions.mailbox_providers || []
  const captchaCatalog = configOptions.captcha_providers || []
  const smsCatalog = configOptions.sms_providers || []
  const mailboxDrivers = configOptions.mailbox_drivers || []
  const captchaDrivers = configOptions.captcha_drivers || []
  const smsDrivers = configOptions.sms_drivers || []
  const providerCatalogs: Record<ProviderType, ProviderOption[]> = {
    mailbox: mailboxCatalog,
    captcha: captchaCatalog,
    sms: smsCatalog,
  }
  const providerDrivers: Record<ProviderType, ProviderDriver[]> = {
    mailbox: mailboxDrivers,
    captcha: captchaDrivers,
    sms: smsDrivers,
  }
  const unusedProviders: Record<ProviderType, ProviderOption[]> = {
    mailbox: mailboxCatalog.filter(item => !providerSettings.mailbox.some(setting => setting.provider_key === item.value)),
    captcha: captchaCatalog.filter(item => !providerSettings.captcha.some(setting => setting.provider_key === item.value)),
    sms: smsCatalog.filter(item => !providerSettings.sms.some(setting => setting.provider_key === item.value)),
  }

  useEffect(() => {
    setNewProviderKey(current => {
      const next = { ...current }
      let changed = false
      PROVIDER_TYPES.forEach(providerType => {
        const candidates = unusedProviders[providerType]
        const nextValue = candidates.some(item => item.value === current[providerType]) ? current[providerType] : (candidates[0]?.value || '')
        if (next[providerType] !== nextValue) {
          next[providerType] = nextValue
          changed = true
        }
      })
      if (!changed) {
        return current
      }
      return next
    })
  }, [mailboxCatalog, captchaCatalog, smsCatalog, providerSettings.mailbox, providerSettings.captcha, providerSettings.sms])

  useEffect(() => {
    setProviderDefinitionForm(current => {
      const next = { ...current }
      let changed = false
      PROVIDER_TYPES.forEach(providerType => {
        const drivers = providerDrivers[providerType]
        const currentForm = current[providerType]
        const driver = drivers.find(item => item.driver_type === currentForm.driver_type) || drivers[0] || null
        const nextDriverType = driver?.driver_type || ''
        const nextAuthMode = driver?.auth_modes?.some(mode => mode.value === currentForm.auth_mode)
          ? currentForm.auth_mode
          : (driver?.default_auth_mode || driver?.auth_modes?.[0]?.value || '')
        if (currentForm.driver_type !== nextDriverType || currentForm.auth_mode !== nextAuthMode) {
          next[providerType] = {
            ...currentForm,
            driver_type: nextDriverType,
            auth_mode: nextAuthMode,
          }
          changed = true
        }
      })
      return changed ? next : current
    })
  }, [mailboxDrivers, captchaDrivers, smsDrivers])

  const getErrorMessage = (error: unknown, fallback: string) => {
    if (error instanceof Error && error.message) {
      return error.message
    }
    return fallback
  }

  const updateProviderDefinitionForm = (providerType: ProviderType, key: string, value: any) => {
    setProviderDefinitionForm(current => {
      const next = {
        ...current,
        [providerType]: {
          ...current[providerType],
          [key]: value,
        },
      }
      if (key === 'driver_type') {
        const drivers = providerDrivers[providerType]
        const driver = drivers.find(item => item.driver_type === value) || null
        next[providerType].auth_mode = driver?.default_auth_mode || driver?.auth_modes?.[0]?.value || ''
        next[providerType].config = {}
        next[providerType].auth = {}
      }
      return next
    })
  }

  const updateProviderSetting = (providerType: ProviderType, providerKey: string, updater: (item: ProviderSetting) => ProviderSetting) => {
    setProviderSettings(current => ({
      ...current,
      [providerType]: current[providerType].map(item => item.provider_key === providerKey ? updater(item) : item),
    }))
  }

  const updateProviderSettingField = (providerType: ProviderType, providerKey: string, field: any, value: string) => {
    updateProviderSetting(providerType, providerKey, item => {
      if (field.category === 'auth') {
        return { ...item, auth: { ...item.auth, [field.key]: value } }
      }
      return { ...item, config: { ...item.config, [field.key]: value } }
    })
  }

  const saveProviderSetting = async (providerType: ProviderType, item: ProviderSetting) => {
    const stateKey = `${providerType}:${item.provider_key}`
    setProviderSaving(current => ({ ...current, [stateKey]: true }))
    setProviderError(current => ({ ...current, [providerType]: '' }))
    try {
      await apiFetch('/provider-settings', {
        method: 'PUT',
        body: JSON.stringify({
          id: item.id || undefined,
          provider_type: providerType,
          provider_key: item.provider_key,
          display_name: item.display_name,
          auth_mode: item.auth_mode,
          enabled: item.enabled,
          is_default: item.is_default,
          config: item.config,
          auth: item.auth,
          metadata: item.metadata || {},
        }),
      })
      invalidateConfigOptionsCache()
      invalidateConfigCache()
      await loadConfigData()
      setProviderNotice(current => ({ ...current, [providerType]: `Saved ${item.catalog_label || item.provider_key} config` }))
      setProviderSaved(current => ({ ...current, [stateKey]: true }))
      setTimeout(() => setProviderSaved(current => ({ ...current, [stateKey]: false })), 2000)
    } catch (error) {
      setProviderError(current => ({ ...current, [providerType]: getErrorMessage(error, 'Failed to save provider config') }))
    } finally {
      setProviderSaving(current => ({ ...current, [stateKey]: false }))
    }
  }

  const createProviderSetting = async (providerType: ProviderType, providerKey: string) => {
    if (!providerKey) return
    const catalog = providerCatalogs[providerType].find(item => item.value === providerKey)
    if (!catalog) return
    const existing = providerSettings[providerType].some(item => item.provider_key === providerKey)
    if (existing) {
      setProviderDialog({ providerType, providerKey, readOnly: false })
      return
    }
    const stateKey = `${providerType}:${providerKey}`
    setProviderCreating(current => ({ ...current, [stateKey]: true }))
    setProviderError(current => ({ ...current, [providerType]: '' }))
    try {
      await apiFetch('/provider-settings', {
        method: 'POST',
        body: JSON.stringify({
          provider_type: providerType,
          provider_key: providerKey,
          display_name: catalog.label,
          auth_mode: catalog.default_auth_mode || catalog.auth_modes?.[0]?.value || '',
          enabled: true,
          is_default: providerSettings[providerType].length === 0,
          config: {},
          auth: {},
          metadata: {},
        }),
      })
      invalidateConfigOptionsCache()
      await loadConfigData()
      setProviderNotice(current => ({ ...current, [providerType]: `Added ${catalog.label}` }))
      setProviderAddDialog(null)
    } catch (error) {
      setProviderError(current => ({ ...current, [providerType]: getErrorMessage(error, 'Failed to add provider') }))
    } finally {
      setProviderCreating(current => ({ ...current, [stateKey]: false }))
    }
  }

  const createProviderDefinitionAndSetting = async (providerType: ProviderType) => {
    const payload = providerDefinitionForm[providerType]
    const driverList = providerDrivers[providerType]
    const driver = driverList.find(item => item.driver_type === payload.driver_type) || null
    const definitionKey = `${providerType}:${payload.provider_key || 'new'}`
    if (!payload.provider_key || !payload.label || !payload.driver_type) {
      setProviderError(current => ({ ...current, [providerType]: 'Please fill in Provider Name, Key and Driver Family first' }))
      return
    }
    setProviderDefinitionCreating(current => ({ ...current, [definitionKey]: true }))
    setProviderError(current => ({ ...current, [providerType]: '' }))
    try {
      await apiFetch('/provider-definitions', {
        method: 'POST',
        body: JSON.stringify({
          provider_type: providerType,
          provider_key: payload.provider_key,
          label: payload.label,
          description: payload.description || '',
          driver_type: payload.driver_type,
          enabled: true,
          default_auth_mode: payload.auth_mode || driver?.default_auth_mode || '',
          metadata: {},
        }),
      })
      await apiFetch('/provider-settings', {
        method: 'POST',
        body: JSON.stringify({
          provider_type: providerType,
          provider_key: payload.provider_key,
          display_name: payload.label,
          auth_mode: payload.auth_mode || driver?.default_auth_mode || '',
          enabled: true,
          is_default: providerSettings[providerType].length === 0,
          config: payload.config || {},
          auth: payload.auth || {},
          metadata: {},
        }),
      })
      invalidateConfigOptionsCache()
      await loadConfigData()
      setProviderNotice(current => ({ ...current, [providerType]: `Created dynamic provider ${payload.label}` }))
      setProviderCreateDialog(null)
      setProviderDefinitionForm(current => ({
        ...current,
        [providerType]: {
          provider_key: '',
          label: '',
          description: '',
          driver_type: driver?.driver_type || '',
          auth_mode: driver?.default_auth_mode || driver?.auth_modes?.[0]?.value || '',
          config: {},
          auth: {},
        },
      }))
    } catch (error) {
      setProviderError(current => ({ ...current, [providerType]: getErrorMessage(error, 'Failed to create dynamic provider') }))
    } finally {
      setProviderDefinitionCreating(current => ({ ...current, [definitionKey]: false }))
    }
  }

  const dialogItem = providerDialog.providerType
    ? providerSettings[providerDialog.providerType].find(item => item.provider_key === providerDialog.providerKey) || null
    : null

  const mailboxCount = providerSettings.mailbox.length
  const captchaCount = providerSettings.captcha.length
  const smsCount = providerSettings.sms.length
  const solverLabel = solverRunning === null ? '—' : solverRunning ? 'Running' : 'Not Running'
  const currentTabMeta = TABS.find(item => item.id === activeTab) ?? TABS[0]
  const currentProviderTab = PROVIDER_TYPES.includes(activeTab as ProviderType) ? activeTab as ProviderType : null

  const renderProviderPanel = (providerType: ProviderType) => {
    const meta = PROVIDER_META[providerType]
    const catalog = providerCatalogs[providerType] || []
    const settings = providerSettings[providerType]

    return (
      <>
        {optionsError && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {optionsError}
          </div>
        )}
        {providerError[providerType] && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {providerError[providerType]}
          </div>
        )}
        {providerNotice[providerType] && !providerError[providerType] && (
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            {providerNotice[providerType]}
          </div>
        )}
        <div className="rounded-lg border border-[var(--accent-edge)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--text-secondary)]">
          {meta.usageHint}
        </div>
        {providerType === 'captcha' && (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5">
            <div className="mb-2">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Current Strategy</h3>
            </div>
            <div className="text-sm text-[var(--text-secondary)]">{getCaptchaStrategyLabel('protocol', configOptions.captcha_policy, configOptions.captcha_providers)}</div>
            <div className="text-sm text-[var(--text-secondary)] mt-2">{getCaptchaStrategyLabel('headless', configOptions.captcha_policy, configOptions.captcha_providers)}</div>
          </div>
        )}
        <ProviderCards
          providerType={providerType}
          catalog={catalog}
          settings={settings}
          onReload={loadConfigData}
          onCreateCustom={() => {
            // Reset form before opening
            const drivers = providerDrivers[providerType] || []
            const firstDriver = drivers[0]
            setProviderDefinitionForm(current => ({
              ...current,
              [providerType]: {
                provider_key: '',
                label: '',
                description: '',
                driver_type: firstDriver?.driver_type || '',
                auth_mode: firstDriver?.default_auth_mode || firstDriver?.auth_modes?.[0]?.value || '',
                config: {},
                auth: {},
              },
            }))
            setProviderCreateDialog(providerType)
          }}
        />
      </>
    )
  }

  // Filter tabs: when embedded, exclude platform_caps (moved to Advanced)
  const visibleTabs = embedded
    ? TABS.filter(t => t.id !== 'platform_caps')
    : TABS

  return (
    <div className="space-y-4">
      {!embedded && (
        <Card className="overflow-hidden p-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-sm font-semibold text-[var(--text-primary)]">Configuration</div>
              <Badge variant="default">{currentTabMeta.label}</Badge>
              <Badge variant={solverRunning ? 'success' : solverRunning === false ? 'danger' : 'secondary'}>{solverLabel}</Badge>
            </div>
          </div>
        </Card>
      )}

      {!embedded && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <SettingsMetric label={PROVIDER_META.mailbox.metricLabel} value={mailboxCount} icon={PROVIDER_META.mailbox.icon} />
          <SettingsMetric label={PROVIDER_META.captcha.metricLabel} value={captchaCount} icon={PROVIDER_META.captcha.icon} />
          <SettingsMetric label={PROVIDER_META.sms.metricLabel} value={smsCount} icon={PROVIDER_META.sms.icon} />
          <SettingsMetric label="Solver" value={solverLabel} icon={Orbit} />
          <SettingsMetric label="Modules" value={TABS.length} icon={Package2} />
        </div>
      )}

      {/* Horizontal tab bar — only show when not navigated via sidebar */}
      {!(embedded && defaultTab) && (
      <div className="flex flex-wrap gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--chip-bg)] p-1">
        {visibleTabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={cn(
              'inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all',
              activeTab === id
                ? 'bg-[var(--accent)] text-white shadow-sm'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>
      )}

        <div className="space-y-4">
          {activeTab === 'platform_caps' ? (
            <PlatformCapsTab />
          ) : (
            <>
              {activeTab === 'register' && (
                <div className="rounded-lg border border-[var(--accent-edge)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--text-secondary)]">
                  Regular users only need to understand two things: choose "System Email" or "Third-party Account" for registration identity, and choose "Protocol Mode / Background Browser Auto / Visual Browser Auto" for execution method. The configuration here only sets default values.
                </div>
              )}
              {currentProviderTab && renderProviderPanel(currentProviderTab)}
              {!currentProviderTab && sections.map(({ section, desc, items }) => (
                <div key={section} className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5">
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">{section}</h3>
                    {desc && <p className="text-xs text-[var(--text-muted)] mt-0.5">{desc}</p>}
                  </div>
                  {items.map((field: any) => (
                    <Field key={field.key} field={field} form={form} setForm={setForm}
                      showSecret={showSecret} setShowSecret={setShowSecret}
                      selectOptions={getSelectOptions(field.key)} />
                  ))}
                </div>
              ))}
              {!currentProviderTab && (
                <Button onClick={save} disabled={saving} className="w-full">
                  <Save className="h-4 w-4 mr-2" />
                  {saved ? 'Saved ✓' : saving ? 'Saving...' : 'Save Config'}
                </Button>
              )}
            </>
          )}
        </div>
      {providerDialog.providerType && dialogItem && (
        <ProviderDetailModal
          title={PROVIDER_META[providerDialog.providerType].detailTitle}
          item={dialogItem}
          readOnly={providerDialog.readOnly}
          saving={providerSaving[`${providerDialog.providerType}:${dialogItem.provider_key}`]}
          saved={providerSaved[`${providerDialog.providerType}:${dialogItem.provider_key}`]}
          showSecret={showSecret}
          setShowSecret={setShowSecret}
          onClose={() => setProviderDialog({ providerType: null, providerKey: '', readOnly: false })}
          onEdit={() => setProviderDialog(current => ({ ...current, readOnly: false }))}
          onChangeName={(value: string) => updateProviderSetting(providerDialog.providerType as ProviderType, dialogItem.provider_key, item => ({ ...item, display_name: value }))}
          onChangeAuthMode={(value: string) => updateProviderSetting(providerDialog.providerType as ProviderType, dialogItem.provider_key, item => ({ ...item, auth_mode: value }))}
          onChangeField={(field: any, value: string) => updateProviderSettingField(providerDialog.providerType as ProviderType, dialogItem.provider_key, field, value)}
          onSave={() => saveProviderSetting(providerDialog.providerType as ProviderType, dialogItem)}
        />
      )}
      {providerAddDialog && (
        <AddProviderModal
          title={PROVIDER_META[providerAddDialog].addTitle}
          subtitle={PROVIDER_META[providerAddDialog].addDialogHint}
          providers={unusedProviders[providerAddDialog]}
          selectedKey={newProviderKey[providerAddDialog]}
          creating={Boolean(newProviderKey[providerAddDialog] && providerCreating[`${providerAddDialog}:${newProviderKey[providerAddDialog]}`])}
          onSelect={(value: string) => setNewProviderKey(current => ({ ...current, [providerAddDialog]: value }))}
          onClose={() => setProviderAddDialog(null)}
          onCreate={(providerKey: string) => createProviderSetting(providerAddDialog, providerKey)}
        />
      )}
      {providerCreateDialog && (
        <CreateProviderDefinitionModal
          title={PROVIDER_META[providerCreateDialog].createTitle}
          providerType={providerCreateDialog}
          drivers={providerDrivers[providerCreateDialog]}
          form={providerDefinitionForm[providerCreateDialog]}
          creating={Boolean(providerDefinitionCreating[`${providerCreateDialog}:${providerDefinitionForm[providerCreateDialog].provider_key || 'new'}`])}
          showSecret={showSecret}
          setShowSecret={setShowSecret}
          onChange={(key: string, value: any) => updateProviderDefinitionForm(providerCreateDialog, key, value)}
          onClose={() => setProviderCreateDialog(null)}
          onCreate={() => createProviderDefinitionAndSetting(providerCreateDialog)}
        />
      )}
    </div>
  )
}
