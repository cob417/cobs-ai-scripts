/**
 * Error message display component
 */

import React from 'react';

interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onDismiss }) => {
  return (
    <div className="error-message">
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="error-dismiss" aria-label="Dismiss error">
          ×
        </button>
      )}
    </div>
  );
};
