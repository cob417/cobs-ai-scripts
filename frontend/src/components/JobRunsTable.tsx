/**
 * Table of recent job runs
 */

import React from 'react';
import { JobRun } from '../services/api';
import { format } from 'date-fns';

interface JobRunsTableProps {
  runs: JobRun[];
  onView: (runId: number) => void;
}

export const JobRunsTable: React.FC<JobRunsTableProps> = ({ runs, onView }) => {
  const getStatusBadge = (status: string) => {
    const className = `status-badge status-${status}`;
    return <span className={className}>{status.toUpperCase()}</span>;
  };

  const getDuration = (run: JobRun) => {
    if (!run.completed_at) {
      return 'Running...';
    }
    const start = new Date(run.started_at);
    const end = new Date(run.completed_at);
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (runs.length === 0) {
    return (
      <div className="empty-state">
        <p>No job runs yet. Jobs will appear here after they execute.</p>
      </div>
    );
  }

  return (
    <div className="job-runs-table">
      <h3>Recent Job Runs</h3>
      <table>
        <thead>
          <tr>
            <th>Job Name</th>
            <th>Status</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td data-label="Job Name">{run.job_name}</td>
              <td data-label="Status">{getStatusBadge(run.status)}</td>
              <td data-label="Started">
                {format(new Date(run.started_at), 'MMM d, yyyy HH:mm:ss')}
              </td>
              <td data-label="Duration">{getDuration(run)}</td>
              <td data-label="Actions">
                <button onClick={() => onView(run.id)} className="btn-view">
                  View Details
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
