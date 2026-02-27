import { useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { periodRange, reportData } from '../domain/services';
import { Period } from '../domain/models';
import { Button, Card, Select } from '../components/UI';
import { Bar, BarChart, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatMoney } from '../lib/utils';

export const Reports = () => {
  const { state } = useApp();
  const [period, setPeriod] = useState<Period>('month');
  const [generated, setGenerated] = useState(true);
  const data = useMemo(() => reportData(state, periodRange(period)), [state, period]);

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'finagent-export.json';
    a.click();
  };

  return <div className="space-y-3 pb-4">
    <Card><div className="flex gap-2"><Select value={period} onChange={(e)=>setPeriod(e.target.value as Period)}><option value="today">Сегодня</option><option value="week">Неделя</option><option value="month">Месяц</option></Select><Button onClick={()=>setGenerated(true)}>Сформировать отчёт</Button></div></Card>
    {generated && <>
      <Card><h3 className="mb-2 font-semibold">Расходы по категориям</h3>{data.pie.length===0 ? <p className="text-sm" style={{ color: 'var(--tg-hint)' }}>Нет расходов в выбранном периоде.</p> : <div className="h-52"><ResponsiveContainer><PieChart><Pie data={data.pie} dataKey="amount" nameKey="name" /></PieChart></ResponsiveContainer></div>}</Card>
      <Card><h3 className="mb-2 font-semibold">Динамика по дням</h3><div className="h-52"><ResponsiveContainer><LineChart data={data.line}><XAxis dataKey="day" /><YAxis /><Tooltip /><Line type="monotone" dataKey="expense" stroke="#ef4444" /><Line type="monotone" dataKey="income" stroke="#10b981" /></LineChart></ResponsiveContainer></div></Card>
      <Card><h3 className="mb-2 font-semibold">Доходы vs Расходы</h3><div className="h-52"><ResponsiveContainer><BarChart data={data.bar}><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value" fill="#3b82f6" /></BarChart></ResponsiveContainer></div></Card>
      <Card><h3 className="mb-2 font-semibold">Инсайты</h3><ul className="space-y-1 text-sm"><li>ТОП расход: {data.insights.topExpense?.name || '—'} — {formatMoney(data.insights.topExpense?.amount || 0)} ({Math.round(data.insights.topExpense?.share || 0)}%)</li><li>Средний расход/день: {formatMoney(data.insights.avgExpense)}</li><li>Дней в минус: {data.insights.minusDays}</li><li>Самая большая операция: {data.insights.maxTx ? formatMoney(data.insights.maxTx.amount) : '—'}</li></ul></Card>
      <Button onClick={exportJson}>Скачать JSON</Button>
    </>}
  </div>;
};
