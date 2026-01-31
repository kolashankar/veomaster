import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import FileUploader from '@/components/FileUploader';
import { FolderArchive, FileText, Play, Trash2, Eye, Clock, CheckCircle, XCircle } from 'lucide-react';
import { jobAPI } from '@/services/api';
import { toast } from 'sonner';

const Dashboard = () => {
  const navigate = useNavigate();
  const [jobName, setJobName] = useState('');
  const [imagesFile, setImagesFile] = useState(null);
  const [promptsFile, setPromptsFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);

  // Fetch jobs on mount
  useEffect(() => {
    fetchJobs();
    // Poll for job updates every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const jobsList = await jobAPI.listJobs(null, 20);
      setJobs(jobsList);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoadingJobs(false);
    }
  };

  const handleCreateAndUpload = async () => {
    if (!jobName.trim()) {
      toast.error('Please enter a job name');
      return;
    }
    if (!imagesFile) {
      toast.error('Please upload images folder (ZIP file)');
      return;
    }
    if (!promptsFile) {
      toast.error('Please upload prompts file');
      return;
    }

    try {
      setIsCreating(true);

      // Step 1: Create job
      toast.info('Creating job...');
      const job = await jobAPI.createJob(jobName);

      // Step 2: Upload files
      setIsUploading(true);
      toast.info('Uploading files...');
      
      await jobAPI.uploadFiles(
        job.job_id,
        imagesFile,
        promptsFile,
        (progress) => setUploadProgress(progress)
      );

      toast.success('Files uploaded successfully!');

      // Step 3: Start the automation process
      toast.info('Starting video generation automation...');
      await jobAPI.startJob(job.job_id);
      toast.success('Video generation started! You can monitor progress in the job details.');

      // Reset form
      setJobName('');
      setImagesFile(null);
      setPromptsFile(null);
      setUploadProgress(0);

      // Refresh jobs list
      await fetchJobs();

      // Navigate to job details
      navigate(`/job/${job.job_id}`);
    } catch (error) {
      console.error('Failed to create job:', error);
      toast.error(error.response?.data?.detail || 'Failed to create job');
    } finally {
      setIsCreating(false);
      setIsUploading(false);
    }
  };

  const handleStartJob = async (jobId) => {
    try {
      await jobAPI.startJob(jobId);
      toast.success('Automation started!');
      await fetchJobs();
    } catch (error) {
      console.error('Failed to start job:', error);
      toast.error(error.response?.data?.detail || 'Failed to start automation');
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job?')) {
      return;
    }

    try {
      await jobAPI.deleteJob(jobId);
      toast.success('Job deleted successfully');
      await fetchJobs();
    } catch (error) {
      console.error('Failed to delete job:', error);
      toast.error('Failed to delete job');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'outline', icon: Clock, label: 'Pending', color: 'text-gray-600' },
      processing: { variant: 'default', icon: Play, label: 'Processing', color: 'text-blue-600' },
      completed: { variant: 'secondary', icon: CheckCircle, label: 'Completed', color: 'text-green-600' },
      failed: { variant: 'destructive', icon: XCircle, label: 'Failed', color: 'text-red-600' },
      cancelled: { variant: 'outline', icon: XCircle, label: 'Cancelled', color: 'text-gray-600' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900">Google Flow Automation</h1>
          <p className="text-gray-600">Automate video generation with AI</p>
        </div>

        {/* Job Creation Card */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Create New Job</CardTitle>
            <CardDescription>
              Upload your images and prompts to start generating videos
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Job Name Input */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Job Name</label>
              <Input
                placeholder="e.g., Product Demo Videos"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                disabled={isCreating}
              />
            </div>

            {/* File Uploaders */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FileUploader
                label="Images Folder (ZIP)"
                icon={FolderArchive}
                accept={{ 'application/zip': ['.zip'] }}
                selectedFile={imagesFile}
                onFileSelect={setImagesFile}
                onRemove={() => setImagesFile(null)}
              />
              <FileUploader
                label="Prompts File (TXT)"
                icon={FileText}
                accept={{ 'text/plain': ['.txt'] }}
                selectedFile={promptsFile}
                onFileSelect={setPromptsFile}
                onRemove={() => setPromptsFile(null)}
              />
            </div>

            {/* Upload Progress */}
            {isUploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Uploading files...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}

            {/* Create Button */}
            <Button
              onClick={handleCreateAndUpload}
              disabled={isCreating || !jobName || !imagesFile || !promptsFile}
              className="w-full"
              size="lg"
            >
              {isCreating ? 'Creating...' : 'Create Job & Upload Files'}
            </Button>
          </CardContent>
        </Card>

        {/* Active Jobs List */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Your Jobs</CardTitle>
            <CardDescription>
              View and manage your video generation jobs
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingJobs ? (
              <div className="text-center py-8 text-gray-500">Loading jobs...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No jobs yet. Create your first job above!
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map((job) => (
                  <Card key={job.job_id} className="border-2 hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        {/* Job Info */}
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-3">
                            <h3 className="text-lg font-semibold text-gray-900">
                              {job.job_name}
                            </h3>
                            {getStatusBadge(job.status)}
                          </div>

                          {/* Progress Info */}
                          {job.total_images > 0 && (
                            <div className="space-y-1">
                              <div className="flex items-center gap-4 text-sm text-gray-600">
                                <span>Images: {job.total_images}</span>
                                <span>Videos: {job.completed_videos}/{job.expected_videos}</span>
                                {job.failed_videos > 0 && (
                                  <span className="text-red-600">Failed: {job.failed_videos}</span>
                                )}
                              </div>

                              {job.status === 'processing' && (
                                <div className="space-y-1">
                                  <Progress value={job.progress * 100} className="h-2" />
                                  <p className="text-xs text-gray-500">
                                    Processing image {job.current_image}/{job.total_images}
                                  </p>
                                </div>
                              )}
                            </div>
                          )}

                          <p className="text-xs text-gray-500">
                            Created: {new Date(job.created_at).toLocaleString()}
                          </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2">
                          {job.status === 'pending' && job.total_images > 0 && (
                            <Button
                              onClick={() => handleStartJob(job.job_id)}
                              size="sm"
                              variant="default"
                            >
                              <Play className="w-4 h-4 mr-1" />
                              Start
                            </Button>
                          )}
                          
                          <Button
                            onClick={() => navigate(`/job/${job.job_id}`)}
                            size="sm"
                            variant="outline"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>

                          {job.status !== 'processing' && (
                            <Button
                              onClick={() => handleDeleteJob(job.job_id)}
                              size="sm"
                              variant="destructive"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
