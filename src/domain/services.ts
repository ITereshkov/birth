import { endOfDay, endOfMonth, endOfWeek, endOfToday, startOfDay, startOfMonth, startOfWeek, isWithinInterval, eachDayOfInterval, format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { AppState, DateRange, Period, Transaction, TransactionType } from './models';

export const periodRange = (period: Period, custom?: DateRange): DateRange => {
  const now = new Date();
  if (period === 'today') return { from: startOfDay(now), to: endOfToday() };
  if (period === 'week') return { from: startOfWeek(now, { weekStartsOn: 1 }), to: endOfWeek(now, { weekStartsOn: 1 }) };
  if (period === 'month') return { from: startOfMonth(now), to: endOfMonth(now) };
  return custom ?? { from: startOfDay(now), to: endOfDay(now) };
};

export const inRange = (iso: string, range: DateRange) => isWithinInterval(new Date(iso), range);

export const getPeriodSummary = (state: AppState, range: DateRange) => {
  const tx = state.transactions.filter((t) => inRange(t.date, range));
  const income_total = tx.filter((t) => t.type === 'income').reduce((a, b) => a + b.amount, 0);
  const expense_total = tx.filter((t) => t.type === 'expense').reduce((a, b) => a + b.amount, 0);
  return { tx, income_total, expense_total, net_cashflow: income_total - expense_total };
};

export const topExpenseCategories = (state: AppState, txs: Transaction[]) => {
  const expenses = txs.filter((t) => t.type === 'expense');
  const total = expenses.reduce((a, b) => a + b.amount, 0) || 1;
  const map = new Map<string, number>();
  expenses.forEach((t) => map.set(t.categoryId, (map.get(t.categoryId) || 0) + t.amount));
  return [...map.entries()].sort((a,b)=>b[1]-a[1]).map(([id, amount]) => {
    const cat = state.categories.find((c) => c.id === id);
    return { id, name: cat?.name ?? 'Без категории', amount, share: (amount / total) * 100 };
  });
};

export const reportData = (state: AppState, range: DateRange) => {
  const tx = state.transactions.filter((t) => inRange(t.date, range));
  const days = eachDayOfInterval(range);
  const line = days.map((d) => {
    const key = format(d, 'yyyy-MM-dd');
    const dayTx = tx.filter((t) => format(new Date(t.date), 'yyyy-MM-dd') === key);
    return {
      day: format(d, 'd MMM', { locale: ru }),
      expense: dayTx.filter((t) => t.type === 'expense').reduce((a,b)=>a+b.amount,0),
      income: dayTx.filter((t) => t.type === 'income').reduce((a,b)=>a+b.amount,0)
    };
  });
  const pie = topExpenseCategories(state, tx);
  const pieTop = pie.slice(0, 6);
  const other = pie.slice(6).reduce((a, b) => a + b.amount, 0);
  if (other) pieTop.push({ id: 'other', name: 'Прочее', amount: other, share: 0 });
  const { income_total, expense_total } = getPeriodSummary(state, range);
  const minusDays = line.filter((d) => d.expense > d.income).length;
  const maxTx = tx.sort((a,b)=>b.amount-a.amount)[0];
  return {
    line,
    pie: pieTop,
    bar: [{ name: 'Доходы', value: income_total }, { name: 'Расходы', value: expense_total }],
    insights: {
      topExpense: pie[0],
      avgExpense: expense_total / Math.max(1, days.length),
      minusDays,
      maxTx
    }
  };
};

export const applyTransactionToAccount = (balance: number, type: TransactionType, amount: number, reverse = false) => {
  const sign = type === 'income' ? 1 : -1;
  const mult = reverse ? -1 : 1;
  return balance + sign * amount * mult;
};
