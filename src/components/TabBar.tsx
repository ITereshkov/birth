const tabs = ['Панель', 'Операции', 'Отчёты', 'Настройки'] as const;

export const TabBar = ({ active, onChange }: { active: number; onChange: (index: number) => void }) => (
  <div className="fixed bottom-0 left-0 right-0 mx-auto max-w-md border-t border-black/10 px-2 py-2" style={{ background: 'var(--tg-surface)' }}>
    <div className="grid grid-cols-4 gap-1 text-xs">
      {tabs.map((t, i) => (
        <button key={t} onClick={() => onChange(i)} className={`rounded-lg py-2 ${active === i ? 'bg-slate-100/80 font-semibold' : ''}`} style={{ color: active === i ? 'var(--tg-text)' : 'var(--tg-hint)' }}>{t}</button>
      ))}
    </div>
  </div>
);
