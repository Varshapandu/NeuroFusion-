// src/components/Loader.jsx
export default function Loader({ size = 6 }) {
  return <div className={`w-${size} h-${size} border-2 border-t-transparent rounded-full animate-spin`} />;
}
