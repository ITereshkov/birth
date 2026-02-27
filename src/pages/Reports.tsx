import { useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { inRange, periodRange, reportData } from '../domain/services';
import { Period } from '../domain/models';
import { Button, Card, Select } from '../components/UI';
import { Bar, BarChart, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatMoney } from '../lib/utils';

export const Reports = () => {
  const { state } = useApp();
  const currency = state.settings.currency;
  const [period, setPeriod] = useState<Period>('month');
  const [chart, setChart] = useState<'mix' | 'expense' | 'income'>('mix');
  const range = useMemo(() => periodRange(period), [period]);
  const data = useMemo(() => reportData(state, range), [range, state]);
  const periodTransactions = useMemo(
    () => state.transactions
      .filter((t) => inRange(t.date, range))
      .sort((a, b) => +new Date(b.date) - +new Date(a.date))
      .slice(0, 30),
    [range, state.transactions],
  );

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'finagent-export.json';
    a.click();
  };

  return <div className="space-y-3 pb-4">
    <h2 className="text-5xl font-bold">Отчет</h2>
    <div className="grid grid-cols-3 gap-2">
      <button onClick={() => setChart('expense')} className={`rounded-2xl border px-2 py-3 ${chart === 'expense' ? 'text-rose-400' : ''}`} style={{ background: 'var(--tg-surface)', borderColor: 'rgba(255,255,255,.1)' }}>Расходы</button>
      <button onClick={() => setChart('mix')} className={`rounded-2xl border px-2 py-3 ${chart === 'mix' ? 'text-sky-400' : ''}`} style={{ background: 'var(--tg-surface)', borderColor: 'rgba(255,255,255,.1)' }}>Доходы и расходы</button>
      <button onClick={() => setChart('income')} className={`rounded-2xl border px-2 py-3 ${chart === 'income' ? 'text-emerald-400' : ''}`} style={{ background: 'var(--tg-surface)', borderColor: 'rgba(255,255,255,.1)' }}>Доходы</button>
    </div>

    <Card><div className="flex gap-2"><Select value={period} onChange={(e) => setPeriod(e.target.value as Period)}><option value="today">Сегодня</option><option value="week">Неделя</option><option value="month">Месяц</option></Select><Button onClick={exportJson}>Скачать JSON</Button></div></Card>

    <Card>
      <div className="mb-2 flex justify-between text-sm" style={{ color: 'var(--tg-hint)' }}><span>Доходы {formatMoney(data.bar[0].value, currency)}</span><span>Расходы {formatMoney(data.bar[1].value, currency)}</span><span>Итого {formatMoney(data.bar[0].value - data.bar[1].value, currency)}</span></div>
      <div className="h-56">
        <ResponsiveContainer>
          <LineChart data={data.line}>
            <XAxis dataKey="day" stroke="#9aa0ae" />
            <YAxis stroke="#9aa0ae" />
            <Tooltip />
            {(chart === 'expense' || chart === 'mix') && <Line type="monotone" dataKey="expense" stroke="#fb7185" strokeWidth={2} />}
            {(chart === 'income' || chart === 'mix') && <Line type="monotone" dataKey="income" stroke="#4ade80" strokeWidth={2} />}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>

    <Card>
      <h3 className="mb-2 text-lg font-semibold">Расходы по категориям</h3>
      {data.pie.length === 0 ? <p style={{ color: 'var(--tg-hint)' }}>За этот период данных нет</p> : <div className="h-52"><ResponsiveContainer><PieChart><Pie data={data.pie} dataKey="amount" nameKey="name" /></PieChart></ResponsiveContainer></div>}
    </Card>

    <Card>
      <h3 className="mb-2 text-lg font-semibold">Инсайты</h3>
      <ul className="space-y-1 text-sm">
        <li>ТОП расход: {data.insights.topExpense?.name || '—'} — {formatMoney(data.insights.topExpense?.amount || 0, currency)} ({Math.round(data.insights.topExpense?.share || 0)}%)</li>
        <li>Средний расход/день: {formatMoney(data.insights.avgExpense, currency)}</li>
        <li>Дней в минус: {data.insights.minusDays}</li>
        <li>Самая большая операция: {data.insights.maxTx ? formatMoney(data.insights.maxTx.amount, currency) : '—'}</li>
      </ul>
    </Card>

    <Card><div className="h-44"><ResponsiveContainer><BarChart data={data.bar}><XAxis dataKey="name" stroke="#9aa0ae" /><YAxis stroke="#9aa0ae" /><Tooltip /><Bar dataKey="value" fill="#1f9bff" /></BarChart></ResponsiveContainer></div></Card>

    <Card>
      <h3 className="mb-2 text-lg font-semibold">Таблица операций за период</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead style={{ color: 'var(--tg-hint)' }}><tr><th className="py-1">Дата</th><th>Тип</th><th>Категория</th><th>Счёт</th><th className="text-right">Сумма</th></tr></thead>
          <tbody>
            {periodTransactions.map((t) => (
              <tr key={t.id} className="border-t" style={{ borderColor: 'rgba(255,255,255,.08)' }}>
                <td className="py-1">{new Date(t.date).toLocaleDateString('ru-RU')}</td>
                <td>{t.type === 'income' ? 'Доход' : 'Расход'}</td>
                <td>{state.categories.find((c) => c.id === t.categoryId)?.name ?? '—'}</td>
                <td>{state.accounts.find((a) => a.id === t.accountId)?.name ?? '—'}</td>
                <td className="text-right">{formatMoney(t.amount, currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  </div>;
};
