import { useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { periodRange, getPeriodSummary } from '../domain/services';
import { Period } from '../domain/models';
import { formatMoney, formatRuDate } from '../lib/utils';
import { Button, Card, Input } from '../components/UI';

export const Dashboard = ({ openAdd, goHistory }: { openAdd: (type?: 'income'|'expense') => void; goHistory: () => void }) => {
  const { state, addAccount } = useApp();
  const [period, setPeriod] = useState<Period>('month');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const range = periodRange(period, from && to ? { from: new Date(from), to: new Date(to) } : undefined);
  const summary = useMemo(() => getPeriodSummary(state, range), [state, range]);
  const totalBalance = state.accounts.reduce((a, b) => a + b.balance, 0);

  return <div className="space-y-3">
    <Card>
      <div className="text-sm text-slate-500">Баланс</div>
      <div className="text-3xl font-bold">{formatMoney(totalBalance)}</div>
      <div className="mt-2 flex gap-2 text-sm">
        {(['today','week','month','custom'] as Period[]).map((p) => <button key={p} onClick={() => setPeriod(p)} className={`rounded-lg px-2 py-1 ${period===p?'bg-slate-200':''}`}>{p==='today'?'Сегодня':p==='week'?'Неделя':p==='month'?'Месяц':'Выбрать'}</button>)}
      </div>
      {period==='custom' && <div className="mt-2 grid grid-cols-2 gap-2"><Input type="date" value={from} onChange={(e)=>setFrom(e.target.value)} /><Input type="date" value={to} onChange={(e)=>setTo(e.target.value)} /></div>}
      <div className="mt-3 grid grid-cols-3 text-sm">
        <div>Доходы<br/><b className="text-emerald-600">{formatMoney(summary.income_total)}</b></div>
        <div>Расходы<br/><b className="text-rose-600">{formatMoney(summary.expense_total)}</b></div>
        <div>Разница<br/><b>{formatMoney(summary.net_cashflow)}</b></div>
      </div>
    </Card>
    <Card>
      <div className="mb-2 flex items-center justify-between"><h3 className="font-semibold">Счета</h3><button onClick={() => { const name = prompt('Название счёта'); if (!name) return; const b = Number(prompt('Стартовый баланс')||'0'); addAccount(name,b); }} className="text-sm text-blue-600">+ Счёт</button></div>
      <div className="space-y-1">{state.accounts.map((a) => <div key={a.id} className="flex justify-between"><span>{a.name}</span><span>{formatMoney(a.balance)}</span></div>)}</div>
    </Card>
    <Card>
      <h3 className="mb-2 font-semibold">Быстрое добавление</h3>
      <div className="grid grid-cols-2 gap-2">
        <Button className="bg-rose-500" onClick={() => openAdd('expense')}>➖ Расход</Button>
        <Button className="bg-emerald-500" onClick={() => openAdd('income')}>➕ Доход</Button>
      </div>
    </Card>
    <Card>
      <div className="mb-2 flex items-center justify-between"><h3 className="font-semibold">Последние операции</h3><button onClick={goHistory} className="text-sm text-blue-600">Все</button></div>
      {state.transactions.slice(0, 5).map((t) => {
        const cat = state.categories.find((c) => c.id === t.categoryId);
        return <div key={t.id} className="flex items-center justify-between text-sm"><span>{cat?.icon} {cat?.name} · {formatRuDate(t.date)}</span><b className={t.type==='income'?'text-emerald-600':'text-rose-600'}>{t.type==='income'?'+':'-'}{formatMoney(t.amount)}</b></div>;
      })}
      {state.transactions.length===0 && <div className="text-sm text-slate-500">Нет операций. Добавьте первую.</div>}
    </Card>
  </div>;
};
