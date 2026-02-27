const tabs = ['Панель', 'Операции', 'Отчёты', 'Настройки'] as const;

export const TabBar = ({ active, onChange }: { active: number; onChange: (index: number) => void }) => (
  <div className="fixed bottom-0 left-0 right-0 mx-auto max-w-md border-t border-slate-200 bg-white px-2 py-2">
    <div className="grid grid-cols-4 gap-1 text-xs">
      {tabs.map((t, i) => (
        <button key={t} onClick={() => onChange(i)} className={`rounded-lg py-2 ${active === i ? 'bg-slate-100 font-semibold' : 'text-slate-500'}`}>{t}</button>
      ))}
    </div>
  </div>
);
