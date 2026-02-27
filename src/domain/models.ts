export type TransactionType = 'income' | 'expense';

export interface Account {
  id: string;
  name: string;
  balance: number;
  createdAt: string;
}

export interface Category {
  id: string;
  name: string;
  type: TransactionType;
  icon?: string;
  createdAt: string;
}

export interface Transaction {
  id: string;
  type: TransactionType;
  amount: number;
  categoryId: string;
  accountId: string;
  date: string;
  comment?: string;
  createdAt: string;
}

export interface AppState {
  accounts: Account[];
  categories: Category[];
  transactions: Transaction[];
  settings: { currency: 'RUB'; firstRunDone: boolean };
}

export type Period = 'today' | 'week' | 'month' | 'custom';

export interface DateRange {
  from: Date;
  to: Date;
}
