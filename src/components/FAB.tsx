export const FAB = ({ onClick }: { onClick: () => void }) => (
  <button onClick={onClick} className="fixed bottom-20 right-4 h-14 w-14 rounded-full text-3xl text-white shadow-lg" style={{ background: 'var(--tg-btn)' }}>+</button>
);
