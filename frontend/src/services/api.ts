/**
 * API client for backend
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    // Could add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      return Promise.reject(new Error(message));
    } else if (error.request) {
      // Request made but no response
      return Promise.reject(new Error('No response from server. Please check your connection.'));
    } else {
      // Error setting up request
      return Promise.reject(error);
    }
  }
);

export interface Job {
  id: number;
  name: string;
  prompt_filename: string;
  prompt_content: string;
  cron_expression: string;
  enabled: boolean;
  email_recipients?: string[];
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  name: string;
  prompt_content: string;
  cron_expression: string;
  enabled?: boolean;
  email_recipients?: string[];
}

export interface JobUpdate {
  name?: string;
  prompt_content?: string;
  cron_expression?: string;
  enabled?: boolean;
  email_recipients?: string[];
}

export interface JobRun {
  id: number;
  job_id: number;
  job_name: string;
  status: 'running' | 'success' | 'failed';
  output_content?: string;  // Markdown
  html_output_content?: string;  // HTML formatted
  log_content?: string;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface CronParseResult {
  cron_expression: string;
  description: string;
  next_runs: string[];
}

export interface Status {
  scheduler_running: boolean;
  active_jobs_count: number;
  total_jobs_count: number;
}

// Jobs API
export const getJobs = async (): Promise<Job[]> => {
  const response = await api.get<Job[]>('/jobs');
  return response.data;
};

export const getJob = async (id: number): Promise<Job> => {
  const response = await api.get<Job>(`/jobs/${id}`);
  return response.data;
};

export const createJob = async (job: JobCreate): Promise<Job> => {
  const response = await api.post<Job>('/jobs', job);
  return response.data;
};

export const updateJob = async (id: number, job: JobUpdate): Promise<Job> => {
  const response = await api.put<Job>(`/jobs/${id}`, job);
  return response.data;
};

export const deleteJob = async (id: number): Promise<void> => {
  await api.delete(`/jobs/${id}`);
};

export const runJob = async (id: number): Promise<JobRun> => {
  const response = await api.post<JobRun>(`/jobs/${id}/run`);
  return response.data;
};

// Cron API
export const parseCron = async (cronExpression: string): Promise<CronParseResult> => {
  const response = await api.post<CronParseResult>('/cron/parse', {
    cron_expression: cronExpression,
  });
  return response.data;
};

// Job Runs API
export const getJobRuns = async (limit: number = 50): Promise<JobRun[]> => {
  const response = await api.get<JobRun[]>(`/job-runs?limit=${limit}`);
  return response.data;
};

export const getJobRun = async (id: number): Promise<JobRun> => {
  const response = await api.get<JobRun>(`/job-runs/${id}`);
  return response.data;
};

// Status API
export const getStatus = async (): Promise<Status> => {
  const response = await api.get<Status>('/status');
  return response.data;
};
