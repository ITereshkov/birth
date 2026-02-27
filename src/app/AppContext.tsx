import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { Account, AppState, Category, Transaction } from '../domain/models';
import { loadState, saveState } from '../lib/storage';
import { applyTransactionToAccount } from '../domain/services';
import { uid } from '../lib/utils';

interface Ctx {
  state: AppState;
  startOnboarding: () => void;
  addAccount: (name: string, balance: number) => void;
  updateAccount: (a: Account) => void;
  deleteAccount: (id: string) => void;
  addCategory: (name: string, type: Category['type'], icon?: string) => void;
  updateCategory: (c: Category) => void;
  deleteCategory: (id: string) => void;
  addTransaction: (tx: Omit<Transaction, 'id'|'createdAt'>) => void;
  updateTransaction: (tx: Transaction) => void;
  deleteTransaction: (id: string) => void;
  resetAll: () => void;
  undoMeta: { txId: string; expiresAt: number } | null;
  undoLast: () => void;
}

const AppContext = createContext<Ctx | null>(null);

const withBalance = (state: AppState, tx: Transaction, reverse = false) => ({
  ...state,
  accounts: state.accounts.map((a) => a.id === tx.accountId ? { ...a, balance: applyTransactionToAccount(a.balance, tx.type, tx.amount, reverse) } : a)
});

export const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const [state, setState] = useState<AppState>(() => loadState());
  const [undoMeta, setUndoMeta] = useState<Ctx['undoMeta']>(null);

  useEffect(() => saveState(state), [state]);

  const api = useMemo<Ctx>(() => ({
    state,
    startOnboarding: () => setState((s) => {
      const now = new Date().toISOString();
      const cats: Category[] = [
        ['Еда', 'expense', '🍔'], ['Дом', 'expense', '🏠'], ['Транспорт', 'expense', '🚌'], ['Подписки', 'expense', '📺'], ['Здоровье', 'expense', '💊'], ['Развлечения', 'expense', '🎉'], ['Покупки', 'expense', '🛍️'],
        ['Зарплата', 'income', '💼'], ['Подработка', 'income', '🧰'], ['Возврат', 'income', '↩️'], ['Подарки', 'income', '🎁']
      ].map(([name, type, icon]) => ({ id: uid(), name, type: type as Category['type'], icon, createdAt: now }));
      return {
        ...s,
        categories: cats,
        accounts: [{ id: uid(), name: 'Карта', balance: 0, createdAt: now }],
        settings: { ...s.settings, firstRunDone: true }
      };
    }),
    addAccount: (name, balance) => setState((s) => ({ ...s, accounts: [...s.accounts, { id: uid(), name, balance, createdAt: new Date().toISOString() }] })),
    updateAccount: (a) => setState((s) => ({ ...s, accounts: s.accounts.map((x) => x.id === a.id ? a : x) })),
    deleteAccount: (id) => setState((s) => ({ ...s, accounts: s.accounts.filter((a) => a.id !== id), transactions: s.transactions.filter((t) => t.accountId !== id) })),
    addCategory: (name, type, icon) => setState((s) => ({ ...s, categories: [...s.categories, { id: uid(), name, type, icon, createdAt: new Date().toISOString() }] })),
    updateCategory: (c) => setState((s) => ({ ...s, categories: s.categories.map((x) => x.id === c.id ? c : x) })),
    deleteCategory: (id) => setState((s) => ({ ...s, categories: s.categories.filter((c) => c.id !== id) })),
    addTransaction: (input) => setState((s) => {
      const tx: Transaction = { ...input, id: uid(), createdAt: new Date().toISOString() };
      setUndoMeta({ txId: tx.id, expiresAt: Date.now() + 10_000 });
      return withBalance({ ...s, transactions: [tx, ...s.transactions] }, tx);
    }),
    updateTransaction: (next) => setState((s) => {
      const prev = s.transactions.find((t) => t.id === next.id);
      if (!prev) return s;
      let ns = withBalance(s, prev, true);
      ns = withBalance({ ...ns, transactions: ns.transactions.map((t) => t.id === next.id ? next : t) }, next, false);
      return ns;
    }),
    deleteTransaction: (id) => setState((s) => {
      const tx = s.transactions.find((t) => t.id === id);
      if (!tx) return s;
      const ns = withBalance({ ...s, transactions: s.transactions.filter((t) => t.id !== id) }, tx, true);
      return ns;
    }),
    resetAll: () => setState({ accounts: [], categories: [], transactions: [], settings: { currency: 'RUB', firstRunDone: false } }),
    undoMeta,
    undoLast: () => {
      setState((s) => {
        if (!undoMeta || Date.now() > undoMeta.expiresAt) return s;
        const tx = s.transactions.find((t) => t.id === undoMeta.txId);
        if (!tx) return s;
        return withBalance({ ...s, transactions: s.transactions.filter((t) => t.id !== tx.id) }, tx, true);
      });
      setUndoMeta(null);
    }
  }), [state, undoMeta]);

  useEffect(() => {
    if (!undoMeta) return;
    const timer = setTimeout(() => setUndoMeta(null), Math.max(0, undoMeta.expiresAt - Date.now()));
    return () => clearTimeout(timer);
  }, [undoMeta]);

  return <AppContext.Provider value={api}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('AppContext missing');
  return ctx;
};
