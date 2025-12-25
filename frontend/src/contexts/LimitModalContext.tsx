'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { LimitExceededError } from '@/types/usage';
import { LimitReachedModal } from '@/components/business/LimitReachedModal';
import { setLimitExceededHandler } from '@/lib/api-client';

interface LimitModalContextType {
  showLimitModal: (errorData: LimitExceededError) => void;
  hideLimitModal: () => void;
}

const LimitModalContext = createContext<LimitModalContextType | undefined>(undefined);

export function LimitModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [errorData, setErrorData] = useState<LimitExceededError | null>(null);

  const showLimitModal = (data: LimitExceededError) => {
    setErrorData(data);
    setIsOpen(true);
  };

  const hideLimitModal = () => {
    setIsOpen(false);
  };

  // Register the global limit exceeded handler
  useEffect(() => {
    setLimitExceededHandler(showLimitModal);
  }, []);

  return (
    <LimitModalContext.Provider value={{ showLimitModal, hideLimitModal }}>
      {children}
      {errorData && (
        <LimitReachedModal
          isOpen={isOpen}
          onClose={hideLimitModal}
          errorData={errorData}
        />
      )}
    </LimitModalContext.Provider>
  );
}

export function useLimitModal() {
  const context = useContext(LimitModalContext);
  if (!context) {
    throw new Error('useLimitModal must be used within a LimitModalProvider');
  }
  return context;
}
