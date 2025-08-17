export default function Card({ children, className = "" }) {
  return (
    <div
      className={`bg-white/10 backdrop-blur-md rounded-2xl shadow-lg border border-white/20 p-6 ${className}`}
    >
      {children}
    </div>
  );
}
