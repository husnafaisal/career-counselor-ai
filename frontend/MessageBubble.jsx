import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Sparkles, RotateCcw, ChevronDown } from 'lucide-react';
import { sendMessage } from '../api/chatApi';
import MessageBubble from './MessageBubble';

const ChatUI = ({ sessionId, onReset }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  useEffect(() => {
    // Initial greeting
    setTimeout(() => {
      addBotMessage(
        "Hi there! I'm here to help you explore career paths and find the right learning journey for you. What brings you here today? 😊"
      );
    }, 500);
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isNearBottom);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToBottom = (smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ 
      behavior: smooth ? 'smooth' : 'auto' 
    });
  };

  const addBotMessage = (text, metadata = {}) => {
    setMessages(prev => [...prev, { 
      type: 'bot', 
      text,
      timestamp: new Date().toISOString(),
      metadata
    }]);
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);

    // Add user message immediately
    setMessages(prev => [...prev, { 
      type: 'user', 
      text: userMessage,
      timestamp: new Date().toISOString()
    }]);

    setIsTyping(true);

    try {
      // Send to backend
      const response = await sendMessage(sessionId, userMessage);
      
      // Add bot response
      setTimeout(() => {
        addBotMessage(response.response, response.metadata);
        setIsTyping(false);
      }, 800);

    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
      setIsTyping(false);
      
      // Add error message
      setTimeout(() => {
        addBotMessage(
          "I'm sorry, I'm having trouble connecting right now. Could you try sending that again?"
        );
      }, 500);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to start a new conversation? This will clear your current chat.')) {
      setMessages([]);
      onReset();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b shadow-sm px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-xl">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">Career Counselor AI</h1>
              <p className="text-sm text-gray-500">Your path to the right career, simplified</p>
            </div>
          </div>
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            title="Start new conversation"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="hidden sm:inline">Reset</span>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          
          {isTyping && (
            <div className="flex gap-3 justify-start">
              <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-full h-10 w-10 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white shadow-sm border border-gray-100 px-4 py-3 rounded-2xl">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={() => scrollToBottom()}
          className="fixed bottom-24 right-8 bg-white shadow-lg border border-gray-200 p-3 rounded-full hover:bg-gray-50 transition-colors z-10"
          aria-label="Scroll to bottom"
        >
          <ChevronDown className="w-5 h-5 text-gray-600" />
        </button>
      )}

      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-100">
          <p className="text-sm text-red-600 text-center max-w-4xl mx-auto">
            {error}
          </p>
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t shadow-lg px-4 py-4 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              disabled={isTyping}
            />
            <button
              onClick={handleSend}
              disabled={isTyping || !input.trim()}
              className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-3">
            Try saying: "I want to learn data science" or "I'm confused about my career"
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatUI;