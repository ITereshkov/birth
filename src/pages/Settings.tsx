import { ReactNode, useState } from 'react';
import { useApp } from '../app/AppContext';
import { Button, Card, Input } from '../components/UI';

const Row = ({ title, sub, right, onClick }: { title: string; sub?: string; right?: ReactNode; onClick?: () => void }) => (
  <button onClick={onClick} className="flex w-full items-center justify-between border-b py-3 text-left last:border-b-0" style={{ borderColor: 'rgba(255,255,255,.1)' }}>
    <div>
      <div className="text-3xl leading-8">{title}</div>
      {sub && <div className="mt-1 text-lg" style={{ color: 'var(--tg-hint)' }}>{sub}</div>}
    </div>
    <div className="text-xl" style={{ color: 'var(--tg-hint)' }}>{right ?? '›'}</div>
  </button>
);

export const Settings = ({ userName, onCloseApp }: { userName?: string; onCloseApp: () => void }) => {
  const { state, addCategory, updateCategory, deleteCategory, resetAll } = useApp();
  const [tab, setTab] = useState<'expense' | 'income'>('expense');

  return <div className="space-y-3 pb-4">
    <h2 className="text-5xl font-bold">Настройки</h2>

    <Card>
      <Row title="Основная валюта" sub="Российский рубль" right="₽" />
      <Row title="Экспорт в CSV (excel)" sub="Скачать архив операций" onClick={() => alert('MVP: пока доступен экспорт JSON в Отчётах')} />
      <Row title="Обновить балансы кошельков" sub="Пересчитать по операциям" onClick={() => alert('Баланс обновляется автоматически при создании и редактировании операций')} />
      <Row title="Удалить данные" sub="Удалить все данные и начать сначала" onClick={() => { if (confirm('Сбросить все данные?')) resetAll(); }} />
      <Row title="Telegram" sub={`Пользователь: ${userName || 'Не определён'}`} right={<Button onClick={onCloseApp}>Закрыть</Button>} />
    </Card>

    <Card>
      <h3 className="mb-2 text-2xl font-semibold">Категории</h3>
      <div className="mb-2 flex gap-2">{(['expense', 'income'] as const).map((t) => <button key={t} onClick={() => setTab(t)} className={`rounded-2xl px-3 py-1 ${tab === t ? 'font-medium' : ''}`} style={{ background: tab === t ? 'rgba(255,255,255,.15)' : 'rgba(255,255,255,.05)' }}>{t === 'expense' ? 'Расходы' : 'Доходы'}</button>)}</div>
      <div className="space-y-1">{state.categories.filter((c) => c.type === tab).map((c) => <div key={c.id} className="flex items-center gap-2"><span>{c.icon}</span><Input value={c.name} onChange={(e) => updateCategory({ ...c, name: e.target.value })} /><button onClick={() => deleteCategory(c.id)} className="text-red-400">✕</button></div>)}</div>
      <button onClick={() => { const name = prompt('Название категории'); if (!name) return; const icon = prompt('Иконка') || ''; addCategory(name, tab, icon); }} className="mt-2 text-sm underline" style={{ color: 'var(--tg-hint)' }}>+ Добавить категорию</button>
    </Card>
  </div>;
};
