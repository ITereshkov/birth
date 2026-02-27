import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const uid = () => crypto.randomUUID();

export const formatMoney = (v: number) =>
  `${Math.round(v).toLocaleString('ru-RU')} ₽`;

export const formatRuDate = (iso: string) => format(new Date(iso), 'd MMM yyyy', { locale: ru });

export const toInputDate = (date: Date) => date.toISOString().slice(0, 10);
