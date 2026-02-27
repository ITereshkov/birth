import { AppState, Category } from '../domain/models';

const KEY = 'finagent:v1';

const defaults: Category[] = [
  ['Еда', 'expense', '🍔'], ['Дом', 'expense', '🏠'], ['Транспорт', 'expense', '🚌'], ['Подписки', 'expense', '📺'], ['Здоровье', 'expense', '💊'], ['Развлечения', 'expense', '🎉'], ['Покупки', 'expense', '🛍️'],
  ['Зарплата', 'income', '💼'], ['Подработка', 'income', '🧰'], ['Возврат', 'income', '↩️'], ['Подарки', 'income', '🎁']
].map(([name, type, icon]) => ({ id: crypto.randomUUID(), name: String(name), type: type as 'income'|'expense', icon: String(icon), createdAt: new Date().toISOString() }));

export const emptyState = (): AppState => ({
  accounts: [],
  categories: [],
  transactions: [],
  settings: { currency: 'RUB', firstRunDone: false }
});

export const loadState = (): AppState => {
  const raw = localStorage.getItem(KEY);
  if (!raw) return emptyState();
  try {
    const parsed = JSON.parse(raw) as AppState;
    const currency = parsed.settings?.currency;
    const safeCurrency = currency === 'USD' || currency === 'EUR' || currency === 'GBP' || currency === 'RUB' ? currency : 'RUB';
    return {
      ...emptyState(),
      ...parsed,
      settings: {
        ...emptyState().settings,
        ...parsed.settings,
        currency: safeCurrency,
      },
    };
  } catch {
    return emptyState();
  }
};

export const saveState = (state: AppState) => localStorage.setItem(KEY, JSON.stringify(state));

export const setupFirstRun = (state: AppState): AppState => ({
  ...state,
  categories: defaults,
  accounts: [{ id: crypto.randomUUID(), name: 'Карта', balance: 0, createdAt: new Date().toISOString() }],
  settings: { ...state.settings, firstRunDone: true }
});

export const resetData = () => saveState(emptyState());
