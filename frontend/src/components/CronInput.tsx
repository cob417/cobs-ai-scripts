/**
 * Cron expression input with live preview
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { parseCron, CronParseResult } from '../services/api';
import { validateCronExpression } from '../utils/validation';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

interface CronInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

const COMMON_PRESETS = [
  { label: 'Every minute', value: '* * * * *' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Daily at 9 AM', value: '0 9 * * *' },
  { label: 'Daily at midnight', value: '0 0 * * *' },
  { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
  { label: 'Every weekday at 9 AM', value: '0 9 * * 1-5' },
  { label: 'Every Sunday at midnight', value: '0 0 * * 0' },
];

export const CronInput: React.FC<CronInputProps> = ({ value, onChange, error }) => {
  const [description, setDescription] = useState<string>('');
  const [nextRuns, setNextRuns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [parseError, setParseError] = useState<string>('');

  // Debounce cron parsing
  useEffect(() => {
    const validation = validateCronExpression(value);
    if (!validation.valid) {
      setParseError(validation.error || '');
      setDescription('');
      setNextRuns([]);
      return;
    }

    const timeoutId = setTimeout(() => {
      setLoading(true);
      setParseError('');
      parseCron(value)
        .then((result: CronParseResult) => {
          setDescription(result.description);
          setNextRuns(result.next_runs);
        })
        .catch((err) => {
          const errorMessage = err instanceof Error ? err.message : 'Invalid cron expression';
          setParseError(errorMessage);
          setDescription('');
          setNextRuns([]);
        })
        .finally(() => {
          setLoading(false);
        });
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [value]);

  const cronParts = useMemo(() => {
    const parts = value.trim().split(/\s+/);
    if (parts.length !== 5) {
      return ['*', '*', '*', '*', '*'];
    }
    return parts;
  }, [value]);

  const handlePresetClick = useCallback((presetValue: string) => {
    onChange(presetValue);
  }, [onChange]);

  const handleFieldChange = useCallback((index: number, newValue: string) => {
    const newParts = [...cronParts];
    newParts[index] = newValue;
    onChange(newParts.join(' '));
  }, [cronParts, onChange]);

  return (
    <div className="cron-input">
      <div className="cron-input-fields">
        {[
          { label: 'Minute', placeholder: '0', index: 0 },
          { label: 'Hour', placeholder: '9', index: 1 },
          { label: 'Day', placeholder: '*', index: 2 },
          { label: 'Month', placeholder: '*', index: 3 },
          { label: 'Weekday', placeholder: '*', index: 4 },
        ].map(({ label, placeholder, index }) => (
          <label key={label}>
            <span>{label}</span>
            <input
              type="text"
              placeholder={placeholder}
              value={cronParts[index] || ''}
              onChange={(e) => handleFieldChange(index, e.target.value)}
            />
          </label>
        ))}
      </div>

      <div className="cron-full-input">
        <label>
          <span>Full Cron Expression</span>
          <input
            type="text"
            placeholder="0 9 * * *"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className={error || parseError ? 'error' : ''}
          />
        </label>
      </div>

      {(error || parseError) && (
        <ErrorMessage message={error || parseError} />
      )}

      {loading && <LoadingSpinner size="small" message="Parsing cron expression..." />}

      {description && !parseError && (
        <div className="cron-preview">
          <div className="description">
            <strong>Schedule:</strong> {description}
          </div>
          {nextRuns.length > 0 && (
            <div className="next-runs">
              <strong>Next runs:</strong>
              <ul>
                {nextRuns.map((run, idx) => (
                  <li key={idx}>{run}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="cron-presets">
        <strong>Common Presets:</strong>
        <div className="preset-buttons">
          {COMMON_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => handlePresetClick(preset.value)}
              className="preset-btn"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
