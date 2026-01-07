/**
 * Modal to view job run details (output and logs)
 */

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { JobRun, getJobRun } from '../services/api';
import { format } from 'date-fns';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

interface RunDetailModalProps {
  runId: number;
  onClose: () => void;
}

export const RunDetailModal: React.FC<RunDetailModalProps> = ({ runId, onClose }) => {
  const [run, setRun] = useState<JobRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    
    const loadRun = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getJobRun(runId);
        if (!cancelled) {
          setRun(data);
        }
      } catch (err) {
        if (!cancelled) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to load run details';
          setError(errorMessage);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadRun();

    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-body">
            <LoadingSpinner message="Loading run details..." />
          </div>
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>Error</h2>
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
          <div className="modal-body">
            <ErrorMessage message={error || 'Run not found'} />
          </div>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const className = `status-badge status-${status}`;
    return <span className={className}>{status.toUpperCase()}</span>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Job Run Details: {run.job_name}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="run-info">
            <div className="info-row">
              <strong>Status:</strong> {getStatusBadge(run.status)}
            </div>
            <div className="info-row">
              <strong>Started:</strong> {format(new Date(run.started_at), 'MMM d, yyyy HH:mm:ss')}
            </div>
            {run.completed_at && (
              <div className="info-row">
                <strong>Completed:</strong> {format(new Date(run.completed_at), 'MMM d, yyyy HH:mm:ss')}
              </div>
            )}
            {run.error_message && (
              <div className="info-row error">
                <strong>Error:</strong> {run.error_message}
              </div>
            )}
          </div>

          <div className="tabs">
            <div className="tab-content">
              <div className="tab-pane active">
                <h3>Output</h3>
                <div className="output-content">
                  {run.output_content ? (
                    <ReactMarkdown>{run.output_content}</ReactMarkdown>
                  ) : (
                    <p className="no-content">No output available</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="tabs">
            <div className="tab-content">
              <div className="tab-pane active">
                <h3>Logs</h3>
                <div className="log-content">
                  {run.log_content ? (
                    <pre>{run.log_content}</pre>
                  ) : (
                    <p className="no-content">No logs available</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
