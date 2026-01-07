/**
 * Custom hook for error handling
 */

import { useCallback } from 'react';
import { AxiosError } from 'axios';

export const useErrorHandler = () => {
  return useCallback((error: unknown): string => {
    if (error instanceof AxiosError) {
      const message = error.response?.data?.detail || error.message || 'An error occurred';
      console.error('API Error:', message, error);
      return message;
    }
    
    if (error instanceof Error) {
      console.error('Error:', error.message, error);
      return error.message;
    }
    
    console.error('Unknown error:', error);
    return 'An unexpected error occurred';
  }, []);
};
