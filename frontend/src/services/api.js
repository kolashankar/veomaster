import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Job APIs
export const jobAPI = {
  // Create a new job
  createJob: async (jobName) => {
    const response = await api.post('/jobs/create', { job_name: jobName });
    return response.data;
  },

  // Upload files for a job
  uploadFiles: async (jobId, imagesFile, promptsFile, onProgress) => {
    const formData = new FormData();
    formData.append('images_folder', imagesFile);
    formData.append('prompts_file', promptsFile);

    const response = await api.post(`/jobs/${jobId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  // Start job automation
  startJob: async (jobId) => {
    const response = await api.post(`/jobs/${jobId}/start`);
    return response.data;
  },

  // Get job details
  getJob: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  // List all jobs
  listJobs: async (status, limit = 50) => {
    const params = {};
    if (status) params.status = status;
    if (limit) params.limit = limit;
    
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  // Delete job
  deleteJob: async (jobId) => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },
};

// Video APIs
export const videoAPI = {
  // Get all videos for a job
  getJobVideos: async (jobId) => {
    const response = await api.get(`/videos/job/${jobId}`);
    return response.data;
  },

  // Get single video
  getVideo: async (videoId) => {
    const response = await api.get(`/videos/${videoId}`);
    return response.data;
  },

  // Toggle video selection
  toggleSelection: async (videoId, selected) => {
    const response = await api.put(`/videos/${videoId}/select`, { selected });
    return response.data;
  },

  // Upscale videos
  upscaleVideos: async (videoIds, quality = 'balanced') => {
    const response = await api.post('/videos/upscale', {
      video_ids: videoIds,
      quality,
    });
    return response.data;
  },

  // Get upscale task status
  getUpscaleStatus: async (taskId) => {
    const response = await api.get(`/videos/upscale/status/${taskId}`);
    return response.data;
  },

  // Download videos
  downloadVideos: async (videoIds, folderName, resolution = '720p') => {
    const response = await api.post(
      '/videos/download',
      {
        video_ids: videoIds,
        folder_name: folderName,
        resolution,
      },
      {
        responseType: 'blob',
      }
    );
    return response;
  },

  // Regenerate a failed video
  regenerateVideo: async (videoId, newPrompt = null) => {
    const payload = {};
    if (newPrompt) {
      payload.new_prompt = newPrompt;
    }
    const response = await api.post(`/videos/${videoId}/regenerate`, payload);
    return response.data;
  },
};

export default api;
