// src/components/Modal.jsx
export default function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-gray-900 border border-gray-800 rounded-md p-4 w-full max-w-lg">
        {title && <div className="text-lg font-semibold mb-2">{title}</div>}
        <div>{children}</div>
        <div className="mt-4 text-right">
          <button onClick={onClose} className="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600">Close</button>
        </div>
      </div>
    </div>
  );
}
