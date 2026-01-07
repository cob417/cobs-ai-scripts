/**
 * Job creation/editing form
 */

import React, { useState, useCallback } from 'react';
import { Job, JobCreate, JobUpdate } from '../services/api';
import { CronInput } from './CronInput';
import { validateJobName, validatePromptContent, validateCronExpression } from '../utils/validation';
import { ErrorMessage } from './ErrorMessage';

interface JobFormProps {
  job?: Job;
  onSubmit: (data: JobCreate | JobUpdate) => Promise<void>;
  onCancel: () => void;
}

const DEFAULT_EMAIL = 'christopher.j.obrien@gmail.com';

const JobFormComponent: React.FC<JobFormProps> = ({ job, onSubmit, onCancel }) => {
  // Initialize state directly from job prop (only runs on mount)
  const [name, setName] = useState(job?.name || '');
  const [promptContent, setPromptContent] = useState(job?.prompt_content || '');
  const [cronExpression, setCronExpression] = useState(job?.cron_expression || '0 9 * * *');
  const [enabled, setEnabled] = useState(job?.enabled ?? true);
  const [emailRecipients, setEmailRecipients] = useState<string[]>(() => {
    const recipients = job?.email_recipients || [];
    // Always ensure default email is included
    if (!recipients.includes(DEFAULT_EMAIL)) {
      return [DEFAULT_EMAIL, ...recipients];
    }
    return recipients;
  });
  const [newEmail, setNewEmail] = useState('');
  const [emailError, setEmailError] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  // Note: Form state is initialized from job prop on mount.
  // The component is memoized (see bottom) to prevent re-renders when parent re-renders.
  // This preserves form state and scroll position naturally.

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

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleAddEmail = () => {
    setEmailError('');
    const trimmedEmail = newEmail.trim();
    
    if (!trimmedEmail) {
      setEmailError('Please enter an email address');
      return;
    }
    
    if (!validateEmail(trimmedEmail)) {
      setEmailError('Please enter a valid email address');
      return;
    }
    
    if (emailRecipients.includes(trimmedEmail)) {
      setEmailError('This email is already in the list');
      return;
    }
    
    setEmailRecipients([...emailRecipients, trimmedEmail]);
    setNewEmail('');
    setEmailError('');
  };

  const handleRemoveEmail = (emailToRemove: string) => {
    // Prevent removing the default email
    if (emailToRemove === DEFAULT_EMAIL) {
      setEmailError('Cannot remove the default email recipient');
      return;
    }
    setEmailRecipients(emailRecipients.filter(email => email !== emailToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddEmail();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      // Ensure default email is always included
      const recipientsToSave = emailRecipients.includes(DEFAULT_EMAIL) 
        ? emailRecipients 
        : [DEFAULT_EMAIL, ...emailRecipients];
      
      // Check if email recipients changed
      const currentRecipients = job?.email_recipients || [];
      const currentWithDefault = currentRecipients.includes(DEFAULT_EMAIL) 
        ? currentRecipients 
        : [DEFAULT_EMAIL, ...currentRecipients];
      const recipientsChanged = JSON.stringify(recipientsToSave.sort()) !== JSON.stringify(currentWithDefault.sort());
      
      if (job) {
        await onSubmit({
          name: name !== job.name ? name : undefined,
          prompt_content: promptContent !== job.prompt_content ? promptContent : undefined,
          cron_expression: cronExpression !== job.cron_expression ? cronExpression : undefined,
          enabled: enabled !== job.enabled ? enabled : undefined,
          email_recipients: recipientsChanged ? recipientsToSave : undefined,
        });
      } else {
        await onSubmit({
          name: name.trim(),
          prompt_content: promptContent.trim(),
          cron_expression: cronExpression.trim(),
          enabled,
          email_recipients: recipientsToSave,
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

      <div className="form-group">
        <label>
          Email Recipients
        </label>
        <div className="email-recipients-container">
          <div className="email-input-group">
            <input
              type="email"
              value={newEmail}
              onChange={(e) => {
                setNewEmail(e.target.value);
                setEmailError('');
              }}
              onKeyPress={handleKeyPress}
              placeholder="Enter email address"
              className={emailError ? 'error' : ''}
            />
            <button
              type="button"
              onClick={handleAddEmail}
              className="btn-add-email"
            >
              Add
            </button>
          </div>
          {emailError && (
            <div className="email-error">{emailError}</div>
          )}
          {emailRecipients.length > 0 && (
            <div className="email-recipients-list">
              {emailRecipients.map((email, index) => (
                <div key={index} className={`email-recipient-item ${email === DEFAULT_EMAIL ? 'default-email' : ''}`}>
                  <span>{email}</span>
                  {email === DEFAULT_EMAIL && <span className="default-badge">Default</span>}
                  <button
                    type="button"
                    onClick={() => handleRemoveEmail(email)}
                    className="btn-remove-email"
                    title={email === DEFAULT_EMAIL ? "Cannot remove default email" : "Remove email"}
                    disabled={email === DEFAULT_EMAIL}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
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

// Memoize to prevent re-renders when parent re-renders with same job
export const JobForm = React.memo(JobFormComponent, (prevProps, nextProps) => {
  // Re-render only if job ID actually changes
  const prevJobId = prevProps.job?.id;
  const nextJobId = nextProps.job?.id;
  return prevJobId === nextJobId;
});
