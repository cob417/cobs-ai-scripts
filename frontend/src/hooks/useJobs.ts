/**
 * Custom hook for managing jobs
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Job, JobCreate, JobUpdate, getJobs, createJob, updateJob, deleteJob, runJob } from '../services/api';
import { useErrorHandler } from './useErrorHandler';

export const useJobs = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const handleError = useErrorHandler();
  const isInitialLoadRef = useRef(true);

  const loadJobs = useCallback(async () => {
    try {
      // Only set loading on initial load, not on manual refreshes
      // This prevents the UI from unmounting/remounting and resetting scroll position
      if (isInitialLoadRef.current) {
        setLoading(true);
      }
      setError(null);
      const data = await getJobs();
      setJobs(data);
    } catch (err) {
      const errorMessage = handleError(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
      isInitialLoadRef.current = false;
    }
  }, [handleError]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const create = useCallback(async (jobData: JobCreate) => {
    try {
      const newJob = await createJob(jobData);
      setJobs((prev) => [...prev, newJob]);
      return newJob;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [handleError]);

  const update = useCallback(async (id: number, jobData: JobUpdate) => {
    try {
      const updatedJob = await updateJob(id, jobData);
      setJobs((prev) => prev.map((job) => (job.id === id ? updatedJob : job)));
      return updatedJob;
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [handleError]);

  const remove = useCallback(async (id: number) => {
    try {
      await deleteJob(id);
      setJobs((prev) => prev.filter((job) => job.id !== id));
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [handleError]);

  const run = useCallback(async (id: number) => {
    try {
      await runJob(id);
    } catch (err) {
      handleError(err);
      throw err;
    }
  }, [handleError]);

  return {
    jobs,
    loading,
    error,
    loadJobs,
    create,
    update,
    remove,
    run,
  };
};
