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
  // Default to HTML view if HTML content is available, otherwise markdown
  const [viewMode, setViewMode] = useState<'html' | 'markdown'>(() => {
    // Will be set properly after run loads
    return 'html';
  });

  useEffect(() => {
    let cancelled = false;
    
    const loadRun = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getJobRun(runId);
        if (!cancelled) {
          setRun(data);
          // Set default view mode based on available content
          if (data.html_output_content) {
            setViewMode('html');
          } else if (data.output_content) {
            setViewMode('markdown');
          }
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
                <div className="output-header">
                  <h3>Output</h3>
                  {run.html_output_content && run.output_content && (
                    <div className="view-mode-toggle">
                      <button
                        onClick={() => setViewMode('html')}
                        className={`view-mode-btn ${viewMode === 'html' ? 'active' : ''}`}
                      >
                        HTML
                      </button>
                      <button
                        onClick={() => setViewMode('markdown')}
                        className={`view-mode-btn ${viewMode === 'markdown' ? 'active' : ''}`}
                      >
                        Markdown
                      </button>
                    </div>
                  )}
                </div>
                <div className={`output-content ${viewMode === 'html' ? 'html-view' : 'markdown-view'}`}>
                  {viewMode === 'html' ? (
                    // HTML view - show rendered HTML
                    run.html_output_content ? (
                      <div dangerouslySetInnerHTML={{ __html: run.html_output_content }} />
                    ) : run.output_content ? (
                      <div>
                        <p style={{ color: '#666', fontStyle: 'italic', marginBottom: '1rem' }}>HTML version not available. Showing rendered markdown:</p>
                        <ReactMarkdown>{run.output_content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="no-content">No output available</p>
                    )
                  ) : (
                    // Markdown view - show raw markdown text for copying
                    run.output_content ? (
                      <pre className="markdown-raw">{run.output_content}</pre>
                    ) : run.html_output_content ? (
                      <div>
                        <p style={{ color: '#cc0000', fontStyle: 'italic', marginBottom: '1rem', fontWeight: 'bold' }}>⚠️ Raw markdown not available. Only HTML version exists.</p>
                        <p style={{ color: '#666', fontStyle: 'italic', marginBottom: '1rem' }}>Showing HTML content below:</p>
                        <div dangerouslySetInnerHTML={{ __html: run.html_output_content }} />
                      </div>
                    ) : (
                      <p className="no-content">No output available</p>
                    )
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
