// ChatWidget.js
import React, { useState } from 'react';

const CHAT_API = 'http://localhost:8000/chat';

function ChatWidget() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState('');
  const [error, setError] = useState(null);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setResponse('');
    try {
      const res = await fetch(CHAT_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResponse(data.response);
    } catch (err) {
      setError('Failed to send message');
      setResponse('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 w-full bg-white border-t border-gray-300 shadow p-4 flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-4 z-30">
      <form onSubmit={handleSend} className="flex flex-1 items-center space-x-2">
        <input
          className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={input}
          maxLength={400}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question for the chess coach AI..."
          disabled={loading}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-blue-300"
          disabled={loading || !input.trim()}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
      <div className="w-full md:w-auto mt-2 md:mt-0 text-gray-700 text-sm">
        {error && <span className="text-red-600">{error}</span>}
        {response && !error && (
          <div className="bg-gray-100 rounded p-2 mt-2">{response}</div>
        )}
      </div>
    </div>
  );
}

export default ChatWidget;