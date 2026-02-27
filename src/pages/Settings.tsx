import { useState } from 'react';
import { useApp } from '../app/AppContext';
import { Button, Card, Input } from '../components/UI';

export const Settings = ({ userName, onCloseApp }: { userName?: string; onCloseApp: () => void }) => {
  const { state, addCategory, updateCategory, deleteCategory, resetAll } = useApp();
  const [tab, setTab] = useState<'expense'|'income'>('expense');

  return <div className="space-y-3">
    <Card>
      <h3 className="mb-2 font-semibold">Категории</h3>
      <div className="mb-2 flex gap-2">{(['expense','income'] as const).map((t)=><button key={t} onClick={()=>setTab(t)} className={`rounded-lg px-2 py-1 ${tab===t?'bg-slate-200/70 font-medium':''}`}>{t==='expense'?'Расходы':'Доходы'}</button>)}</div>
      <div className="space-y-1">{state.categories.filter((c)=>c.type===tab).map((c)=><div key={c.id} className="flex items-center gap-2"><span>{c.icon}</span><Input value={c.name} onChange={(e)=>updateCategory({ ...c, name: e.target.value })} /><button onClick={()=>deleteCategory(c.id)} className="text-red-600">✕</button></div>)}</div>
      <button onClick={()=>{const name=prompt('Название категории'); if(!name) return; const icon=prompt('Иконка')||''; addCategory(name,tab,icon);}} className="mt-2 text-blue-600">+ Добавить категорию</button>
    </Card>
    <Card><h3 className="font-semibold">Валюта</h3><p className="text-sm" style={{ color: 'var(--tg-hint)' }}>Текущая: RUB</p></Card>
    <Card><h3 className="mb-2 font-semibold">Данные</h3><button className="rounded-xl border border-red-200 px-3 py-2 text-red-600" onClick={()=>{if(confirm('Сбросить все данные?')) resetAll();}}>Сбросить все данные</button></Card>
    <Card><h3 className="mb-2 font-semibold">Telegram</h3><p className="text-sm">Пользователь: {userName || 'Не определён'}</p><Button className="mt-2" onClick={onCloseApp}>Закрыть приложение</Button></Card>
  </div>;
};
