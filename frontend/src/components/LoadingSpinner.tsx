/**
 * Loading spinner component
 */

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  message = 'Loading...' 
}) => {
  const sizeClass = `spinner-${size}`;
  
  return (
    <div className="loading-spinner">
      <div className={`spinner ${sizeClass}`}></div>
      {message && <p>{message}</p>}
    </div>
  );
};
