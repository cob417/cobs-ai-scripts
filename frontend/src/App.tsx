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
import './App.css';

function App() {
  const { jobs, loading: jobsLoading, create, update, remove, run } = useJobs();
  const { runs, loading: runsLoading } = useJobRuns(50);
  const { status } = useStatus();
  
  const [showForm, setShowForm] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);

  const handleCreateJob = useCallback(async (data: JobCreate) => {
    await create(data);
    setShowForm(false);
  }, [create]);

  const handleUpdateJob = useCallback(async (data: JobUpdate) => {
    if (!editingJob) return;
    await update(editingJob.id, data);
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
    try {
      await run(job.id);
    } catch (error) {
      // Error is handled by the hook
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
          <h1>AI Script Scheduler</h1>
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
