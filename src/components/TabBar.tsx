const tabs = ['Панель', 'Операции', 'Отчёты', 'Настройки'] as const;

export const TabBar = ({ active, onChange }: { active: number; onChange: (index: number) => void }) => (
  <div className="fixed bottom-3 left-0 right-0 mx-auto max-w-md px-2 py-2">
    <div className="grid grid-cols-4 gap-1 text-xs">
      {tabs.map((t, i) => (
        <button key={t} onClick={() => onChange(i)} className={`rounded-3xl border py-3 ${active === i ? 'font-semibold' : ''}`} style={{ background: active === i ? 'rgba(255,255,255,.14)' : 'rgba(255,255,255,.06)', color: active === i ? '#29a8ff' : 'var(--tg-text)', borderColor: 'rgba(255,255,255,.12)' }}>{t}</button>
      ))}
    </div>
  </div>
);
