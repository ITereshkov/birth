import { PropsWithChildren } from 'react';

export const Card = ({ children, className = '' }: PropsWithChildren<{ className?: string }>) => (
  <div className={`rounded-3xl border p-4 shadow-sm ${className}`} style={{ background: 'var(--tg-surface)', color: 'var(--tg-text)', borderColor: 'rgba(255,255,255,.08)' }}>{children}</div>
);

export const Button = ({ children, className = '', ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button className={`rounded-2xl px-4 py-2 font-medium disabled:opacity-50 ${className}`} style={{ background: 'var(--tg-btn)', color: 'var(--tg-btn-text)' }} {...props}>{children}</button>
);

export const Input = (props: React.InputHTMLAttributes<HTMLInputElement>) => (
  <input className="w-full rounded-2xl border px-3 py-2" style={{ background: 'rgba(255,255,255,.04)', color: 'var(--tg-text)', borderColor: 'rgba(255,255,255,.09)' }} {...props} />
);

export const Select = ({ children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) => (
  <select className="w-full rounded-2xl border px-3 py-2" style={{ background: 'rgba(255,255,255,.04)', color: 'var(--tg-text)', borderColor: 'rgba(255,255,255,.09)' }} {...props}>{children}</select>
);
