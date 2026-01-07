/**
 * Custom hook for scheduler status
 */

import { useState, useEffect, useCallback } from 'react';
import { Status, getStatus } from '../services/api';
import { useErrorHandler } from './useErrorHandler';

export const useStatus = () => {
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const handleError = useErrorHandler();

  const loadStatus = useCallback(async () => {
    try {
      setError(null);
      const data = await getStatus();
      setStatus(data);
    } catch (err) {
      const errorMessage = handleError(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [loadStatus]);

  return {
    status,
    loading,
    error,
    loadStatus,
  };
};
