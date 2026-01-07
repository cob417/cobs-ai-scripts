/**
 * Validation utilities
 */

export const validateCronExpression = (cron: string): { valid: boolean; error?: string } => {
  if (!cron || !cron.trim()) {
    return { valid: false, error: 'Cron expression is required' };
  }

  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) {
    return { valid: false, error: 'Cron expression must have exactly 5 fields' };
  }

  // Basic validation - check if fields contain valid characters
  const cronPattern = /^[\d\*\/\-\,\s]+$/;
  for (const part of parts) {
    if (!cronPattern.test(part)) {
      return { valid: false, error: `Invalid characters in cron expression: ${part}` };
    }
  }

  return { valid: true };
};

export const validateJobName = (name: string): { valid: boolean; error?: string } => {
  if (!name || !name.trim()) {
    return { valid: false, error: 'Job name is required' };
  }

  if (name.trim().length < 3) {
    return { valid: false, error: 'Job name must be at least 3 characters' };
  }

  if (name.trim().length > 100) {
    return { valid: false, error: 'Job name must be less than 100 characters' };
  }

  return { valid: true };
};

export const validatePromptContent = (content: string): { valid: boolean; error?: string } => {
  if (!content || !content.trim()) {
    return { valid: false, error: 'Prompt content is required' };
  }

  if (content.trim().length < 10) {
    return { valid: false, error: 'Prompt content must be at least 10 characters' };
  }

  return { valid: true };
};
