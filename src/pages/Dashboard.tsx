import { useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { periodRange, getPeriodSummary } from '../domain/services';
import { Period } from '../domain/models';
import { formatMoney } from '../lib/utils';
import { Button, Card, Input } from '../components/UI';

const Bubble = ({ label, value, emoji, onClick }: { label: string; value: number; emoji?: string; onClick?: () => void }) => (
  <button onClick={onClick} className="w-20 text-center">
    <div className="mx-auto mb-1 flex h-16 w-16 items-center justify-center rounded-full text-3xl" style={{ background: 'rgba(255,255,255,.12)' }}>{emoji ?? '+'}</div>
    <div className="truncate text-xs" style={{ color: 'var(--tg-hint)' }}>{label}</div>
    <div className="text-sm font-semibold">{formatMoney(value)}</div>
  </button>
);

export const Dashboard = ({ openAdd, goHistory }: { openAdd: (type?: 'income'|'expense') => void; goHistory: () => void }) => {
  const { state, addAccount, addCategory } = useApp();
  const [period, setPeriod] = useState<Period>('month');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');

  const range = periodRange(period, from && to ? { from: new Date(from), to: new Date(to) } : undefined);
  const summary = useMemo(() => getPeriodSummary(state, range), [state, range]);

  const incomeByCategory = useMemo(() => {
    const map = new Map<string, number>();
    summary.tx.filter((t) => t.type === 'income').forEach((t) => map.set(t.categoryId, (map.get(t.categoryId) ?? 0) + t.amount));
    return [...map.entries()].map(([id, amount]) => ({ cat: state.categories.find((c) => c.id === id), amount }));
  }, [state.categories, summary.tx]);

  const expenseByCategory = useMemo(() => {
    const map = new Map<string, number>();
    summary.tx.filter((t) => t.type === 'expense').forEach((t) => map.set(t.categoryId, (map.get(t.categoryId) ?? 0) + t.amount));
    return [...map.entries()].map(([id, amount]) => ({ cat: state.categories.find((c) => c.id === id), amount }));
  }, [state.categories, summary.tx]);

  return <div className="space-y-3">
    <Card>
      <div className="mb-2 flex items-center justify-between text-sm" style={{ color: 'var(--tg-hint)' }}>
        <span>Период</span>
        <span>{period === 'today' ? 'Сегодня' : period === 'week' ? 'Неделя' : period === 'month' ? 'Месяц' : 'Выборочно'}</span>
      </div>
      <div className="flex gap-2 text-sm">
        {(['today', 'week', 'month', 'custom'] as Period[]).map((p) => <button key={p} onClick={() => setPeriod(p)} className={`rounded-2xl px-3 py-1 ${period === p ? 'font-semibold' : ''}`} style={{ background: period === p ? 'rgba(255,255,255,.16)' : 'rgba(255,255,255,.06)' }}>{p === 'today' ? 'Сегодня' : p === 'week' ? 'Неделя' : p === 'month' ? 'Месяц' : 'Выбрать'}</button>)}
      </div>
      {period === 'custom' && <div className="mt-2 grid grid-cols-2 gap-2"><Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /><Input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></div>}
      <div className="mt-3 grid grid-cols-3 text-center">
        <div><div style={{ color: 'var(--tg-hint)' }}>Доходы</div><div className="text-xl font-bold text-emerald-400">{formatMoney(summary.income_total)}</div></div>
        <div><div style={{ color: 'var(--tg-hint)' }}>Расходы</div><div className="text-xl font-bold text-rose-400">{formatMoney(summary.expense_total)}</div></div>
        <div><div style={{ color: 'var(--tg-hint)' }}>Итого</div><div className="text-xl font-bold">{formatMoney(summary.net_cashflow)}</div></div>
      </div>
    </Card>

    <Card>
      <div className="mb-2 flex items-center justify-between"><h3 className="text-3xl font-bold">Доходы</h3><b>{formatMoney(summary.income_total)}</b></div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {incomeByCategory.map((x) => <Bubble key={x.cat?.id} label={x.cat?.name ?? 'Без категории'} value={x.amount} emoji={x.cat?.icon} />)}
        <Bubble label="Добавить" value={0} onClick={() => { const name = prompt('Категория дохода'); if (name) addCategory(name, 'income', '💼'); }} />
      </div>
    </Card>

    <Card>
      <div className="mb-2 flex items-center justify-between"><h3 className="text-3xl font-bold">Кошельки</h3><b>{formatMoney(state.accounts.reduce((s, a) => s + a.balance, 0))}</b></div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {state.accounts.map((a) => <Bubble key={a.id} label={a.name} value={a.balance} emoji="💳" />)}
        <Bubble label="Добавить" value={0} onClick={() => { const name = prompt('Название счёта'); if (!name) return; const b = Number(prompt('Стартовый баланс') || '0'); addAccount(name, b); }} />
      </div>
    </Card>

    <Card>
      <div className="mb-2 flex items-center justify-between"><h3 className="text-3xl font-bold">Расходы</h3><b>{formatMoney(summary.expense_total)}</b></div>
      <div className="flex flex-wrap gap-3">
        {expenseByCategory.map((x) => <Bubble key={x.cat?.id} label={x.cat?.name ?? 'Без категории'} value={x.amount} emoji={x.cat?.icon} />)}
        <Bubble label="Добавить" value={0} onClick={() => { const name = prompt('Категория расхода'); if (name) addCategory(name, 'expense', '🧾'); }} />
      </div>
      <div className="mt-3 flex gap-2">
        <Button onClick={() => openAdd('expense')} className="flex-1">➖ Расход</Button>
        <Button onClick={() => openAdd('income')} className="flex-1">➕ Доход</Button>
      </div>
      <button onClick={goHistory} className="mt-3 text-sm underline" style={{ color: 'var(--tg-hint)' }}>Перейти в историю</button>
    </Card>
  </div>;
};
