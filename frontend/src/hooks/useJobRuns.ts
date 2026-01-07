/**
 * Custom hook for managing job runs
 */

import { useState, useEffect, useCallback } from 'react';
import { JobRun, getJobRuns, getJobRun } from '../services/api';
import { useErrorHandler } from './useErrorHandler';

export const useJobRuns = (limit: number = 50) => {
  const [runs, setRuns] = useState<JobRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const handleError = useErrorHandler();

  const loadRuns = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getJobRuns(limit);
      setRuns(data);
    } catch (err) {
      const errorMessage = handleError(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [limit, handleError]);

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [loadRuns]);

  const getRun = useCallback(async (id: number): Promise<JobRun> => {
    try {
      return await getJobRun(id);
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [handleError]);

  return {
    runs,
    loading,
    error,
    loadRuns,
    getRun,
  };
};
