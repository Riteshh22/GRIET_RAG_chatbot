import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'griet_chat_history';

export function useChatHistory() {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setConversations(parsed.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)));
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
  }, []);

  const saveConversations = useCallback((convs) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
      setConversations(convs.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)));
    } catch (e) {
      console.error('Failed to save chat history:', e);
    }
  }, []);

  const createConversation = useCallback((title = 'New Chat') => {
    const now = new Date().toISOString();
    const newConv = {
      id: crypto.randomUUID(),
      title,
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
    saveConversations([newConv, ...conversations]);
    return newConv.id;
  }, [conversations, saveConversations]);

  const updateConversation = useCallback((id, updates) => {
    setConversations(prev => {
      const updated = prev.map(conv => 
        conv.id === id ? { ...conv, ...updates, updatedAt: new Date().toISOString() } : conv
      );
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    });
  }, []);

  const addMessageToConversation = useCallback((id, message) => {
    setConversations(prev => {
      const updated = prev.map(conv => {
        if (conv.id === id) {
          const newTitle = conv.messages.length === 0 && message.role === 'user' 
            ? message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
            : conv.title;
          return {
            ...conv,
            title: newTitle,
            messages: [...conv.messages, message],
            updatedAt: new Date().toISOString(),
          };
        }
        return conv;
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    });
  }, []);

  const deleteConversation = useCallback((id) => {
    setConversations(prev => {
      const filtered = prev.filter(conv => conv.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
      return filtered;
    });
  }, []);

  const clearAllConversations = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setConversations([]);
  }, []);

  const getConversation = useCallback((id) => {
    return conversations.find(conv => conv.id === id);
  }, [conversations]);

  return {
    conversations,
    createConversation,
    updateConversation,
    addMessageToConversation,
    deleteConversation,
    clearAllConversations,
    getConversation,
  };
}