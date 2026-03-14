// src/pages/Login.jsx
import { useState } from "react";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [err, setErr] = useState("");

  const submit = (e) => {
    e.preventDefault();
    setErr("");
    // simple mock auth: accept any non-empty credentials
    if (!email || !pass) return setErr("Please enter credentials");
    const token = btoa(`${email}:${Date.now()}`); // mock token
    localStorage.setItem("neuro_token", token);
    onLogin({ user: email, token });
  };

  return (
    <div className="max-w-md mx-auto bg-gray-900 border border-gray-800 p-6 rounded-md">
      <h2 className="text-xl font-semibold mb-4">Sign in</h2>
      {err && <div className="text-red-400 mb-2">{err}</div>}
      <form onSubmit={submit} className="space-y-3">
        <input value={email} onChange={(e)=>setEmail(e.target.value)} placeholder="email" className="w-full p-2 bg-gray-800 rounded" />
        <input value={pass} onChange={(e)=>setPass(e.target.value)} placeholder="password" type="password" className="w-full p-2 bg-gray-800 rounded" />
        <button className="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white w-full">Sign in</button>
      </form>
    </div>
  );
}
