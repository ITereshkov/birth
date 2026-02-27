import { useMemo, useState } from 'react';
import { AppProvider, useApp } from './AppContext';
import { useTelegram } from './useTelegram';
import { Dashboard } from '../pages/Dashboard';
import { History } from '../pages/History';
import { Reports } from '../pages/Reports';
import { Settings } from '../pages/Settings';
import { TabBar } from '../components/TabBar';
import { FAB } from '../components/FAB';
import { TransactionModal } from '../components/TransactionModal';
import { Button } from '../components/UI';

const Inner = () => {
  const { state, startOnboarding, undoMeta, undoLast } = useApp();
  const { webApp, user } = useTelegram();
  const [tab, setTab] = useState(0);
  const [modal, setModal] = useState<{ id?: string; type?: 'income'|'expense' } | null>(null);
  const editTx = useMemo(() => state.transactions.find((t) => t.id === modal?.id), [state.transactions, modal]);

  if (!state.settings.firstRunDone) {
    return <div className="mx-auto max-w-md p-4"><div className="rounded-2xl p-5 shadow" style={{ background: 'var(--tg-surface)' }}><h1 className="text-xl font-bold">👋 Привет! Это ФинАгент</h1><p className="mt-2 text-sm" style={{ color: 'var(--tg-hint)' }}>Быстрый учёт денег. Добавь счёт, затем занеси первую операцию.</p><Button className="mt-3" onClick={startOnboarding}>Начать</Button></div></div>;
  }

  return <div className="mx-auto min-h-screen max-w-md p-3 pb-28">
    <h1 className="mb-1 text-4xl font-bold">ФинАгент</h1>
    <p className="mb-3 text-sm" style={{ color: 'var(--tg-hint)' }}>Ваш личный мини-учёт в Telegram</p>
    {tab===0 && <Dashboard openAdd={(type)=>setModal({ type })} goHistory={() => setTab(1)} />}
    {tab===1 && <History onEdit={(id)=>setModal({ id })} onAdd={()=>setModal({})} />}
    {tab===2 && <Reports />}
    {tab===3 && <Settings userName={user?.first_name || user?.username} onCloseApp={() => webApp?.close()} />}
    {(tab===0||tab===1) && <FAB onClick={() => setModal({})} />}
    <TabBar active={tab} onChange={setTab} />
    {modal && <TransactionModal current={editTx} defaultType={modal.type} onClose={() => setModal(null)} />}
    {undoMeta && <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 rounded-xl bg-slate-900 px-3 py-2 text-sm text-white">✅ Записано <button className="ml-2 underline" onClick={undoLast}>Отменить</button></div>}
  </div>;
};

export const App = () => <AppProvider><Inner /></AppProvider>;
