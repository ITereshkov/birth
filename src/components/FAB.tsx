export const FAB = ({ onClick }: { onClick: () => void }) => (
  <button onClick={onClick} className="fixed bottom-28 right-4 h-14 w-14 rounded-full text-3xl text-white shadow-lg" style={{ background: 'rgba(255,255,255,.2)', boxShadow: '0 0 22px rgba(255,255,255,.18)' }}>+</button>
);
