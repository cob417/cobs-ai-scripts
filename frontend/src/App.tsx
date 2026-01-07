/**
 * Main App component
 */

import React, { useState, useCallback } from 'react';
import { Job, JobCreate, JobUpdate } from './services/api';
import { JobList } from './components/JobList';
import { JobForm } from './components/JobForm';
import { JobRunsTable } from './components/JobRunsTable';
import { RunDetailModal } from './components/RunDetailModal';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoadingSpinner } from './components/LoadingSpinner';
import { useJobs } from './hooks/useJobs';
import { useJobRuns } from './hooks/useJobRuns';
import { useStatus } from './hooks/useStatus';
import { getJobRuns } from './services/api';
import './App.css';

function App() {
  const { jobs, loading: jobsLoading, create, update, remove, run } = useJobs();
  const { runs, loading: runsLoading } = useJobRuns(50);
  const { status } = useStatus();
  
  const [showForm, setShowForm] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [runningJobs, setRunningJobs] = useState<Set<number>>(new Set());

  const handleCreateJob = useCallback(async (data: JobCreate | JobUpdate) => {
    await create(data as JobCreate);
    setShowForm(false);
  }, [create]);

  const handleUpdateJob = useCallback(async (data: JobCreate | JobUpdate) => {
    if (!editingJob) return;
    await update(editingJob.id, data as JobUpdate);
    setEditingJob(null);
    setShowForm(false);
  }, [editingJob, update]);

  const handleDeleteJob = useCallback(async (job: Job) => {
    if (window.confirm(`Are you sure you want to delete "${job.name}"?`)) {
      await remove(job.id);
    }
  }, [remove]);

  const handleToggleJob = useCallback(async (job: Job) => {
    await update(job.id, { enabled: !job.enabled });
  }, [update]);

  const handleRunJob = useCallback(async (job: Job) => {
    // Immediately set as running for UI feedback
    setRunningJobs(prev => new Set(prev).add(job.id));
    
    try {
      await run(job.id);
      // Poll for completion - check job runs to see when it finishes
      const checkCompletion = setInterval(async () => {
        try {
          const latestRuns = await getJobRuns(20);
          const jobRun = latestRuns.find((r) => r.job_id === job.id && r.status !== 'running');
          if (jobRun) {
            setRunningJobs(prev => {
              const next = new Set(prev);
              next.delete(job.id);
              return next;
            });
            clearInterval(checkCompletion);
          }
        } catch (e) {
          // Ignore errors, will clear on next poll
        }
      }, 2000); // Check every 2 seconds
      
      // Clear running state after 5 minutes max
      setTimeout(() => {
        setRunningJobs(prev => {
          const next = new Set(prev);
          next.delete(job.id);
          return next;
        });
        clearInterval(checkCompletion);
      }, 300000);
    } catch (error) {
      // Error is handled by the hook, but clear running state
      setRunningJobs(prev => {
        const next = new Set(prev);
        next.delete(job.id);
        return next;
      });
    }
  }, [run]);

  const handleEditJob = useCallback((job: Job) => {
    setEditingJob(job);
    setShowForm(true);
  }, []);

  const handleNewJob = useCallback(() => {
    setEditingJob(null);
    setShowForm(true);
  }, []);

  const handleCloseForm = useCallback(() => {
    setShowForm(false);
    setEditingJob(null);
  }, []);

  const loading = jobsLoading || runsLoading;

  if (loading) {
    return (
      <div className="app">
        <LoadingSpinner size="large" message="Loading application..." />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <header className="app-header">
          <div className="header-brand">
            <img src="/static/logo.png" alt="Cob's AI Scripts" className="header-logo" />
            <h1>Cob's AI Scripts</h1>
          </div>
          {status && (
            <div className="status-info">
              <span className={`scheduler-status ${status.scheduler_running ? 'running' : 'stopped'}`}>
                Scheduler: {status.scheduler_running ? 'Running' : 'Stopped'}
              </span>
              <span>Active Jobs: {status.active_jobs_count} / {status.total_jobs_count}</span>
            </div>
          )}
        </header>

        <main className="app-main">
          {showForm ? (
            <JobForm
              job={editingJob || undefined}
              onSubmit={editingJob ? handleUpdateJob : handleCreateJob}
              onCancel={handleCloseForm}
            />
          ) : (
            <>
              <div className="section-header">
                <h2>Scheduled Jobs</h2>
                <button onClick={handleNewJob} className="btn-primary">
                  + Create New Job
                </button>
              </div>

              <JobList
                jobs={jobs}
                runningJobs={runningJobs}
                onEdit={handleEditJob}
                onDelete={handleDeleteJob}
                onToggle={handleToggleJob}
                onRun={handleRunJob}
              />

              <JobRunsTable
                runs={runs}
                onView={setSelectedRun}
              />
            </>
          )}
        </main>

        {selectedRun !== null && (
          <RunDetailModal
            runId={selectedRun}
            onClose={() => setSelectedRun(null)}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
