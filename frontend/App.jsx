import React, { useState, useEffect } from 'react';
import ChatUI from './components/ChatUI';
import { createSession } from './api/chatApi';
import { Sparkles, AlertCircle } from 'lucide-react';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setLoading(true);
      const session = await createSession();
      setSessionId(session.session_id);
      setError(null);
    } catch (err) {
      console.error('Failed to initialize session:', err);
      setError('Failed to connect. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setError(null);
    initializeSession();
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <p className="text-gray-600">Initializing your counselor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="text-center max-w-md px-4">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <ChatUI sessionId={sessionId} onReset={handleReset} />
    </div>
  );
}

export default App;