import { isToday, isYesterday, format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { Period } from '../domain/models';
import { getPeriodSummary, periodRange } from '../domain/services';
import { Button, Input, Select } from '../components/UI';
import { formatMoney } from '../lib/utils';

export const History = ({ onEdit, onAdd }: { onEdit: (id: string)=>void; onAdd: ()=>void }) => {
  const { state } = useApp();
  const [period, setPeriod] = useState<Period>('month');
  const [type, setType] = useState<'all'|'income'|'expense'>('all');
  const [account, setAccount] = useState('all');
  const [category, setCategory] = useState('all');
  const [query, setQuery] = useState('');
  const base = useMemo(() => getPeriodSummary(state, periodRange(period)).tx, [state, period]);
  const txs = useMemo(
    () => base
      .filter((t) => (type === 'all' || t.type === type)
        && (account === 'all' || t.accountId === account)
        && (category === 'all' || t.categoryId === category)
        && `${state.categories.find((c) => c.id === t.categoryId)?.name || ''} ${t.comment || ''}`.toLowerCase().includes(query.toLowerCase()))
      .sort((a, b) => +new Date(b.date) - +new Date(a.date)),
    [account, base, category, query, state.categories, type],
  );

  const groups = txs.reduce<Record<string, typeof txs>>((acc, t) => {
    const d = t.date.slice(0, 10);
    (acc[d] ||= []).push(t);
    return acc;
  }, {});
  const orderedDays = Object.keys(groups).sort((a, b) => +new Date(b) - +new Date(a));

  return <div className="space-y-3">
    <div className="grid grid-cols-2 gap-2">
      <Select value={period} onChange={(e)=>setPeriod(e.target.value as Period)}><option value="today">Сегодня</option><option value="week">Неделя</option><option value="month">Месяц</option></Select>
      <Select value={type} onChange={(e)=>setType(e.target.value as typeof type)}><option value="all">Все</option><option value="expense">Расход</option><option value="income">Доход</option></Select>
      <Select value={account} onChange={(e)=>setAccount(e.target.value)}><option value="all">Все счета</option>{state.accounts.map((a)=><option key={a.id} value={a.id}>{a.name}</option>)}</Select>
      <Select value={category} onChange={(e)=>setCategory(e.target.value)}><option value="all">Все категории</option>{state.categories.map((c)=><option key={c.id} value={c.id}>{c.name}</option>)}</Select>
    </div>
    <Input placeholder="Поиск по категории/комментарию" value={query} onChange={(e)=>setQuery(e.target.value)} />
    {txs.length===0 && <div className="rounded-2xl border border-black/5 p-4 text-center text-sm" style={{ background: 'var(--tg-surface)', color: 'var(--tg-hint)' }}>Пока нет операций. Добавь первую — и тут появится история ✅<div className="mt-2"><Button onClick={onAdd}>➕ Добавить</Button></div></div>}
    {orderedDays.map((day) => {
      const arr = groups[day];
      const dt = new Date(day);
      const title = isToday(dt) ? 'Сегодня' : isYesterday(dt) ? 'Вчера' : format(dt, 'd MMM yyyy', { locale: ru });
      return <div key={day} className="rounded-2xl border border-black/5 p-3" style={{ background: 'var(--tg-surface)' }}><div className="mb-2 text-sm font-semibold">{title}</div><div className="space-y-2">{arr.map((t)=>{const cat=state.categories.find((c)=>c.id===t.categoryId); const acc=state.accounts.find((a)=>a.id===t.accountId); return <button key={t.id} onClick={()=>onEdit(t.id)} className="flex w-full items-center justify-between text-left"><div className="text-sm"><div>{cat?.icon} {cat?.name}</div><div className="text-xs" style={{ color: 'var(--tg-hint)' }}>{t.comment||'—'} · {acc?.name}</div></div><div className={t.type==='income'?'text-emerald-600':'text-rose-600'}>{t.type==='income'?'+':'-'}{formatMoney(t.amount)}</div></button>;})}</div></div>;
    })}
  </div>;
};
