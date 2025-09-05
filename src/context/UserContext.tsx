'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  name: string;
  email?: string;
}

interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  login: (userData: User) => void;
  logout: () => void;
  resetMemory: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Initialize with hardcoded user "Vivek" on first load
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Failed to parse stored user:', error);
        // Fallback to hardcoded user
        const defaultUser: User = {
          id: 'vivek_001',
          name: 'Vivek',
          email: 'vivek@example.com'
        };
        setUser(defaultUser);
        localStorage.setItem('user', JSON.stringify(defaultUser));
      }
    } else {
      // Set default hardcoded user
      const defaultUser: User = {
        id: 'vivek_001',
        name: 'Vivek',
        email: 'vivek@example.com'
      };
      setUser(defaultUser);
      localStorage.setItem('user', JSON.stringify(defaultUser));
    }
  }, []);

  const login = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  const resetMemory = async () => {
    if (!user) return;
    
    try {
      const { resetUserMemory } = await import('@/features/chatbot/api/sessionApi');
      await resetUserMemory(user.id);
      
      // Show success feedback (could be enhanced with toast notifications)
      console.log('User memory reset successfully');
      
      // Force a page reload to ensure all sessions are fresh
      // This is necessary because the current active session still has the old profile
      alert('Memory reset successfully! The page will reload to ensure all sessions are fresh.');
      window.location.reload();
    } catch (error) {
      console.error('Failed to reset user memory:', error);
      throw error;
    }
  };

  const value: UserContextType = {
    user,
    setUser,
    isAuthenticated: !!user,
    login,
    logout,
    resetMemory
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}