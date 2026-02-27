import { useMemo, useState } from 'react';
import { useApp } from '../app/AppContext';
import { Transaction, TransactionType } from '../domain/models';
import { Button, Input, Select } from './UI';
import { toInputDate } from '../lib/utils';

export const TransactionModal = ({ current, onClose, defaultType = 'expense' }: { current?: Transaction; onClose: () => void; defaultType?: TransactionType }) => {
  const { state, addTransaction, updateTransaction, deleteTransaction } = useApp();
  const [type, setType] = useState<TransactionType>(current?.type ?? defaultType);
  const [amount, setAmount] = useState(current?.amount ?? 0);
  const [accountId, setAccountId] = useState(current?.accountId ?? state.accounts[0]?.id ?? '');
  const [categoryId, setCategoryId] = useState(current?.categoryId ?? state.categories.find((c) => c.type === type)?.id ?? '');
  const [date, setDate] = useState((current?.date ?? new Date().toISOString()).slice(0, 10));
  const [comment, setComment] = useState(current?.comment ?? '');

  const filteredCategories = useMemo(() => state.categories.filter((c) => c.type === type), [state.categories, type]);

  const save = () => {
    if (!amount || !accountId || !categoryId) return;
    const payload = { type, amount, accountId, categoryId, date: `${date}T12:00:00.000Z`, comment };
    if (current) updateTransaction({ ...current, ...payload });
    else addTransaction(payload);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/30 p-4">
      <div className="mx-auto mt-10 max-w-md rounded-2xl bg-white p-4">
        <h3 className="mb-3 font-semibold">{current ? 'Редактировать операцию' : 'Новая операция'}</h3>
        <div className="space-y-2">
          <Select value={type} onChange={(e) => { setType(e.target.value as TransactionType); setCategoryId(state.categories.find((c) => c.type === e.target.value)?.id ?? ''); }}>
            <option value="expense">Расход</option><option value="income">Доход</option>
          </Select>
          <Input type="number" min="0" value={amount} onChange={(e) => setAmount(Number(e.target.value))} placeholder="Сумма" />
          <Select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            {filteredCategories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
          </Select>
          <Select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
            {state.accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </Select>
          <Input type="date" value={date || toInputDate(new Date())} onChange={(e) => setDate(e.target.value)} />
          <Input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Комментарий" />
        </div>
        <div className="mt-4 flex gap-2">
          <Button onClick={save}>Сохранить</Button>
          <button onClick={onClose} className="rounded-xl border px-4 py-2">Отмена</button>
          {current && <button onClick={() => { deleteTransaction(current.id); onClose(); }} className="ml-auto rounded-xl border border-red-200 px-3 text-red-600">Удалить</button>}
        </div>
      </div>
    </div>
  );
};
