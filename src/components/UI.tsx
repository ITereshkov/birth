import { PropsWithChildren } from 'react';

export const Card = ({ children, className = '' }: PropsWithChildren<{ className?: string }>) => (
  <div className={`rounded-2xl bg-white/85 p-4 shadow-sm ${className}`}>{children}</div>
);

export const Button = ({ children, className = '', ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button className={`rounded-xl px-4 py-2 font-medium text-white disabled:opacity-50 ${className}`} style={{ background: 'var(--tg-btn)' }} {...props}>{children}</button>
);

export const Input = (props: React.InputHTMLAttributes<HTMLInputElement>) => (
  <input className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2" {...props} />
);

export const Select = ({ children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) => (
  <select className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2" {...props}>{children}</select>
);
