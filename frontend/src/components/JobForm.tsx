/**
 * Job creation/editing form
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Job, JobCreate, JobUpdate } from '../services/api';
import { CronInput } from './CronInput';
import { validateJobName, validatePromptContent, validateCronExpression } from '../utils/validation';
import { ErrorMessage } from './ErrorMessage';

interface JobFormProps {
  job?: Job;
  onSubmit: (data: JobCreate | JobUpdate) => Promise<void>;
  onCancel: () => void;
}

export const JobForm: React.FC<JobFormProps> = ({ job, onSubmit, onCancel }) => {
  const [name, setName] = useState(job?.name || '');
  const [promptContent, setPromptContent] = useState(job?.prompt_content || '');
  const [cronExpression, setCronExpression] = useState(job?.cron_expression || '0 9 * * *');
  const [enabled, setEnabled] = useState(job?.enabled ?? true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>('');

  const validateForm = useCallback((): boolean => {
    const nameValidation = validateJobName(name);
    if (!nameValidation.valid) {
      setError(nameValidation.error || '');
      return false;
    }

    const promptValidation = validatePromptContent(promptContent);
    if (!promptValidation.valid) {
      setError(promptValidation.error || '');
      return false;
    }

    const cronValidation = validateCronExpression(cronExpression);
    if (!cronValidation.valid) {
      setError(cronValidation.error || '');
      return false;
    }

    return true;
  }, [name, promptContent, cronExpression]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      if (job) {
        await onSubmit({
          name: name !== job.name ? name : undefined,
          prompt_content: promptContent !== job.prompt_content ? promptContent : undefined,
          cron_expression: cronExpression !== job.cron_expression ? cronExpression : undefined,
          enabled: enabled !== job.enabled ? enabled : undefined,
        });
      } else {
        await onSubmit({
          name: name.trim(),
          prompt_content: promptContent.trim(),
          cron_expression: cronExpression.trim(),
          enabled,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save job';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="job-form">
      <h2>{job ? 'Edit Job' : 'Create New Job'}</h2>

      {error && <ErrorMessage message={error} onDismiss={() => setError('')} />}

      <div className="form-group">
        <label>
          Job Name <span className="required">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="e.g., Daily AI News Research"
        />
      </div>

      <div className="form-group">
        <label>
          Prompt Content (Markdown) <span className="required">*</span>
        </label>
        <textarea
          value={promptContent}
          onChange={(e) => setPromptContent(e.target.value)}
          required
          rows={15}
          placeholder="Enter your prompt in Markdown format..."
          className="prompt-editor"
        />
      </div>

      <div className="form-group">
        <label>
          Schedule (Cron Expression) <span className="required">*</span>
        </label>
        <CronInput
          value={cronExpression}
          onChange={setCronExpression}
          error={error}
        />
      </div>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          <span>Enabled (job will run on schedule)</span>
        </label>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" disabled={submitting || !name || !promptContent || !cronExpression}>
          {submitting ? 'Saving...' : job ? 'Update Job' : 'Create Job'}
        </button>
      </div>
    </form>
  );
};
