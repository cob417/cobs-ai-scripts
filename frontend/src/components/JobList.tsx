/**
 * List of scheduled jobs
 */

import React from 'react';
import { Job } from '../services/api';
import { format } from 'date-fns';

interface JobListProps {
  jobs: Job[];
  onEdit: (job: Job) => void;
  onDelete: (job: Job) => void;
  onToggle: (job: Job) => void;
  onRun: (job: Job) => void;
}

export const JobList: React.FC<JobListProps> = ({
  jobs,
  onEdit,
  onDelete,
  onToggle,
  onRun,
}) => {
  if (jobs.length === 0) {
    return (
      <div className="empty-state">
        <p>No jobs scheduled. Create your first job to get started.</p>
      </div>
    );
  }

  return (
    <div className="job-list">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Schedule</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className={!job.enabled ? 'disabled' : ''}>
              <td>{job.name}</td>
              <td>
                <code>{job.cron_expression}</code>
              </td>
              <td>
                <span className={`status-badge ${job.enabled ? 'enabled' : 'disabled'}`}>
                  {job.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </td>
              <td>{format(new Date(job.created_at), 'MMM d, yyyy')}</td>
              <td>
                <div className="action-buttons">
                  <button onClick={() => onRun(job)} className="btn-run" title="Run Now">
                    ▶
                  </button>
                  <button onClick={() => onToggle(job)} className="btn-toggle" title={job.enabled ? 'Disable' : 'Enable'}>
                    {job.enabled ? '⏸' : '▶'}
                  </button>
                  <button onClick={() => onEdit(job)} className="btn-edit" title="Edit">
                    ✏️
                  </button>
                  <button onClick={() => onDelete(job)} className="btn-delete" title="Delete">
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
