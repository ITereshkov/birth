import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const uid = () => crypto.randomUUID();

export const currencySymbol = (currency: 'RUB' | 'USD' | 'EUR' | 'GBP') => ({
  RUB: '₽',
  USD: '$',
  EUR: '€',
  GBP: '£',
}[currency]);

export const formatMoneyByCurrency = (v: number, currency: 'RUB' | 'USD' | 'EUR' | 'GBP') =>
  `${Math.round(v).toLocaleString('ru-RU')} ${currencySymbol(currency)}`;

export const formatMoney = (v: number, currency: 'RUB' | 'USD' | 'EUR' | 'GBP' = 'RUB') =>
  formatMoneyByCurrency(v, currency);

export const formatRuDate = (iso: string) => format(new Date(iso), 'd MMM yyyy', { locale: ru });

export const toInputDate = (date: Date) => format(date, 'yyyy-MM-dd');
