import { ReactNode, useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { Button, Card, Input, Select } from '../components/UI';
import { formatMoney } from '../lib/utils';

const Row = ({ title, sub, right, onClick }: { title: string; sub?: string; right?: ReactNode; onClick?: () => void }) => (
  <div onClick={onClick} className="flex w-full items-center justify-between border-b py-3 text-left last:border-b-0" style={{ borderColor: 'rgba(255,255,255,.1)' }}>
    <div>
      <div className="text-3xl leading-8">{title}</div>
      {sub && <div className="mt-1 text-lg" style={{ color: 'var(--tg-hint)' }}>{sub}</div>}
    </div>
    <div className="text-xl" style={{ color: 'var(--tg-hint)' }}>{right ?? '›'}</div>
  </div>
);

export const Settings = ({ userName, onCloseApp }: { userName?: string; onCloseApp: () => void }) => {
  const { state, addCategory, updateCategory, deleteCategory, resetAll, setCurrency } = useApp();
  const [tab, setTab] = useState<'expense' | 'income'>('expense');

  const exportCsv = () => {
    const rows = [
      ['id', 'date', 'type', 'category', 'account', 'amount', 'comment'],
      ...state.transactions.map((t) => [
        t.id,
        t.date,
        t.type,
        state.categories.find((c) => c.id === t.categoryId)?.name ?? '',
        state.accounts.find((a) => a.id === t.accountId)?.name ?? '',
        String(t.amount),
        (t.comment ?? '').replaceAll('"', '""'),
      ]),
    ];
    const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'finagent-export.csv';
    a.click();
  };

  const accountsTable = useMemo(
    () => state.accounts.map((a) => ({ ...a, txCount: state.transactions.filter((t) => t.accountId === a.id).length })),
    [state.accounts, state.transactions],
  );

  return <div className="space-y-3 pb-4">
    <h2 className="text-5xl font-bold">Настройки</h2>

    <Card>
      <Row title="Премиум" sub="Скоро: расширенные графики и синхронизация" onClick={() => alert('Функция премиума будет доступна позже')} />
      <Row title="Профили" sub="Сейчас доступен один профиль (MVP)" onClick={() => alert('В MVP поддерживается один профиль')} />

      <div className="border-b py-3" style={{ borderColor: 'rgba(255,255,255,.1)' }}>
        <div className="mb-2 text-3xl leading-8">Основная валюта</div>
        <Select value={state.settings.currency} onChange={(e) => setCurrency(e.target.value as 'RUB' | 'USD' | 'EUR' | 'GBP')}>
          <option value="RUB">Российский рубль (₽)</option>
          <option value="USD">US Dollar ($)</option>
          <option value="EUR">Euro (€)</option>
          <option value="GBP">Pound Sterling (£)</option>
        </Select>
      </div>

      <Row title="Экспорт в CSV (excel)" sub="Скачать таблицу операций" onClick={exportCsv} />
      <Row title="Удалить данные" sub="Удалить все данные и начать сначала" onClick={() => { if (confirm('Сбросить все данные?')) resetAll(); }} />
      <Row title="Telegram" sub={`Пользователь: ${userName || 'Не определён'}`} right={<Button>Закрыть</Button>} onClick={onCloseApp} />
    </Card>

    <Card>
      <h3 className="mb-2 text-2xl font-semibold">Таблица кошельков</h3>
      <table className="w-full text-left text-sm">
        <thead style={{ color: 'var(--tg-hint)' }}><tr><th className="py-1">Счёт</th><th>Операций</th><th className="text-right">Баланс</th></tr></thead>
        <tbody>
          {accountsTable.map((a) => <tr key={a.id} className="border-t" style={{ borderColor: 'rgba(255,255,255,.1)' }}><td className="py-1">{a.name}</td><td>{a.txCount}</td><td className="text-right">{formatMoney(a.balance, state.settings.currency)}</td></tr>)}
        </tbody>
      </table>
    </Card>

    <Card>
      <h3 className="mb-2 text-2xl font-semibold">Категории</h3>
      <div className="mb-2 flex gap-2">{(['expense', 'income'] as const).map((t) => <button key={t} onClick={() => setTab(t)} className={`rounded-2xl px-3 py-1 ${tab === t ? 'font-medium' : ''}`} style={{ background: tab === t ? 'rgba(255,255,255,.15)' : 'rgba(255,255,255,.05)' }}>{t === 'expense' ? 'Расходы' : 'Доходы'}</button>)}</div>
      <div className="space-y-1">{state.categories.filter((c) => c.type === tab).map((c) => <div key={c.id} className="flex items-center gap-2"><span>{c.icon}</span><Input value={c.name} onChange={(e) => updateCategory({ ...c, name: e.target.value })} /><button onClick={() => deleteCategory(c.id)} className="text-red-400">✕</button></div>)}</div>
      <button onClick={() => { const name = prompt('Название категории'); if (!name) return; const icon = prompt('Иконка') || ''; addCategory(name, tab, icon); }} className="mt-2 text-sm underline" style={{ color: 'var(--tg-hint)' }}>+ Добавить категорию</button>
    </Card>
  </div>;
};
