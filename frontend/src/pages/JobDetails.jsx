import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import VideoCard from '@/components/VideoCard';
import VideoSkeleton from '@/components/VideoSkeleton';
import UpscaleModal from '@/components/UpscaleModal';
import { 
  ArrowLeft, 
  Download, 
  Sparkles, 
  CheckCircle, 
  XCircle, 
  Clock,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { jobAPI, videoAPI } from '@/services/api';
import { toast } from 'sonner';

const JobDetails = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadFolderName, setDownloadFolderName] = useState('');
  const [selectedVideos, setSelectedVideos] = useState(new Set());
  const [isDownloading, setIsDownloading] = useState(false);
  const [isUpscaleModalOpen, setIsUpscaleModalOpen] = useState(false);
  const [regeneratingVideos, setRegeneratingVideos] = useState(new Set());
  const [lastSelectedIndex, setLastSelectedIndex] = useState(null);

  const fetchJobData = useCallback(async () => {
    try {
      const [jobData, videosData] = await Promise.all([
        jobAPI.getJob(jobId),
        videoAPI.getJobVideos(jobId),
      ]);
      
      setJob(jobData);
      setVideos(videosData);

      // Auto-set folder name from job name if not set
      if (!downloadFolderName && jobData.job_name) {
        setDownloadFolderName(jobData.job_name.replace(/\s+/g, '_'));
      }
    } catch (error) {
      console.error('Failed to fetch job data:', error);
      toast.error('Failed to load job details');
    } finally {
      setLoading(false);
    }
  }, [jobId, downloadFolderName]);

  useEffect(() => {
    fetchJobData();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchJobData, 5000);
    return () => clearInterval(interval);
  }, [fetchJobData]);

  const handleToggleSelection = async (videoId, event = null) => {
    const completedVideos = videos.filter(v => v.status === 'completed');
    const currentIndex = completedVideos.findIndex(v => v.video_id === videoId);
    
    // Handle Shift+click for range selection
    if (event?.shiftKey && lastSelectedIndex !== null && currentIndex !== -1) {
      const start = Math.min(lastSelectedIndex, currentIndex);
      const end = Math.max(lastSelectedIndex, currentIndex);
      const newSelected = new Set(selectedVideos);
      
      // Select all videos in the range
      for (let i = start; i <= end; i++) {
        newSelected.add(completedVideos[i].video_id);
      }
      
      setSelectedVideos(newSelected);
      
      // Update backend for all selected videos in range
      try {
        for (let i = start; i <= end; i++) {
          const vid = completedVideos[i].video_id;
          if (!selectedVideos.has(vid)) {
            await videoAPI.toggleSelection(vid, true);
          }
        }
      } catch (error) {
        console.error('Failed to update selections:', error);
      }
    } else {
      // Normal toggle
      const newSelected = new Set(selectedVideos);
      
      if (newSelected.has(videoId)) {
        newSelected.delete(videoId);
      } else {
        newSelected.add(videoId);
      }
      
      setSelectedVideos(newSelected);

      // Update backend
      try {
        await videoAPI.toggleSelection(videoId, !selectedVideos.has(videoId));
      } catch (error) {
        console.error('Failed to update selection:', error);
      }
    }
    
    // Update last selected index for range selection
    if (currentIndex !== -1) {
      setLastSelectedIndex(currentIndex);
    }
  };

  const handleSelectAll = () => {
    const completedVideos = videos.filter(v => v.status === 'completed');
    const allSelected = completedVideos.length === selectedVideos.size && completedVideos.length > 0;

    if (allSelected) {
      setSelectedVideos(new Set());
      setLastSelectedIndex(null);
    } else {
      setSelectedVideos(new Set(completedVideos.map(v => v.video_id)));
      setLastSelectedIndex(null);
    }
  };

  const handleDownload = async (resolution = '720p') => {
    if (selectedVideos.size === 0) {
      toast.error('Please select at least one video');
      return;
    }

    if (!downloadFolderName.trim()) {
      toast.error('Please enter a folder name');
      return;
    }

    try {
      setIsDownloading(true);
      toast.info(`Preparing download of ${selectedVideos.size} video(s)...`);

      const response = await videoAPI.downloadVideos(
        Array.from(selectedVideos),
        downloadFolderName,
        resolution
      );

      // Create blob and trigger download
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${downloadFolderName}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success(`Downloaded ${selectedVideos.size} video(s)`);
    } catch (error) {
      console.error('Download failed:', error);
      toast.error('Failed to download videos');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleRegenerateVideo = async (videoId) => {
    try {
      // Add to regenerating set
      setRegeneratingVideos(prev => new Set([...prev, videoId]));
      
      toast.info('Starting video regeneration...');
      
      await videoAPI.regenerateVideo(videoId);
      
      toast.success('Video regeneration started! It will appear in the queue.');
      
      // Refresh data to show updated status
      fetchJobData();
    } catch (error) {
      console.error('Regeneration failed:', error);
      toast.error('Failed to start regeneration');
    } finally {
      // Remove from regenerating set after a delay
      setTimeout(() => {
        setRegeneratingVideos(prev => {
          const newSet = new Set(prev);
          newSet.delete(videoId);
          return newSet;
        });
      }, 2000);
    }
  };

  const handleUpscale = () => {
    if (selectedVideos.size === 0) {
      toast.error('Please select at least one video');
      return;
    }

    // Open the upscale modal
    setIsUpscaleModalOpen(true);
  };

  const handleUpscaleComplete = async () => {
    // Refresh job data after upscaling completes
    await fetchJobData();
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'outline', icon: Clock, label: 'Pending' },
      queued: { variant: 'outline', icon: Clock, label: 'Queued' },
      generating: { variant: 'default', icon: Loader2, label: 'Generating', animate: true },
      completed: { variant: 'secondary', icon: CheckCircle, label: 'Completed' },
      failed: { variant: 'destructive', icon: XCircle, label: 'Failed' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className={`w-3 h-3 ${config.animate ? 'animate-spin' : ''}`} />
        {config.label}
      </Badge>
    );
  };

  // Group videos by prompt number
  const groupedVideos = videos.reduce((acc, video) => {
    const key = video.prompt_number;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(video);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header Skeleton */}
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 shadow-sm animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-4" />
            <div className="h-4 bg-gray-200 rounded w-32" />
          </div>
          
          {/* Progress Skeleton */}
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 shadow-sm animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-full mb-4" />
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-20 bg-gray-200 rounded" />
              ))}
            </div>
          </div>
          
          {/* Video Grid Skeletons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
              <VideoSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center space-y-4">
          <XCircle className="w-12 h-12 mx-auto text-red-600" />
          <p className="text-gray-600">Job not found</p>
          <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{job.job_name}</h1>
                <p className="text-sm text-gray-600">
                  Created {new Date(job.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge(job.status)}
            </div>
          </div>

          {/* Progress Bar */}
          {job.status === 'processing' && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-700 font-medium flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  Processing image {job.current_image || 0}/{job.total_images}
                </span>
                <span className="text-gray-600 font-semibold">{Math.round(job.progress * 100)}%</span>
              </div>
              <Progress value={job.progress * 100} className="h-2" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>
                  {job.completed_videos} of {job.expected_videos} videos completed
                </span>
                {job.failed_videos > 0 && (
                  <span className="text-red-600 font-medium flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {job.failed_videos} failed (will retry)
                  </span>
                )}
              </div>
              
              {/* Show recent errors in real-time */}
              {videos.filter(v => v.status === 'failed' && !v.error_type?.includes('high_demand')).length > 0 && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="text-xs text-red-800">
                      <p className="font-medium">Recent Errors:</p>
                      <ul className="mt-1 space-y-1 list-disc list-inside">
                        {videos
                          .filter(v => v.status === 'failed' && !v.error_type?.includes('high_demand'))
                          .slice(0, 3)
                          .map(v => (
                            <li key={v.video_id}>
                              Prompt #{v.prompt_number}: {v.error_message || 'Unknown error'}
                            </li>
                          ))}
                      </ul>
                      {videos.filter(v => v.status === 'failed' && !v.error_type?.includes('high_demand')).length > 3 && (
                        <p className="mt-1 text-gray-600 italic">
                          +{videos.filter(v => v.status === 'failed' && !v.error_type?.includes('high_demand')).length - 3} more errors
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Stats */}
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{job.total_images}</p>
              <p className="text-xs text-gray-600">Images</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{job.completed_videos}</p>
              <p className="text-xs text-gray-600">Completed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{job.failed_videos}</p>
              <p className="text-xs text-gray-600">Failed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{selectedVideos.size}</p>
              <p className="text-xs text-gray-600">Selected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Video Grid */}
      <div className="max-w-7xl mx-auto px-6 py-6 space-y-8">
        {Object.keys(groupedVideos).length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              No videos generated yet. The automation will start once you click the Start button.
            </CardContent>
          </Card>
        ) : (
          Object.entries(groupedVideos)
            .sort(([a], [b]) => Number(a) - Number(b))
            .map(([promptNumber, promptVideos]) => {
              const firstVideo = promptVideos[0];
              return (
                <Card key={promptNumber} className="shadow-lg">
                  <CardHeader className="bg-gray-50 border-b">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="text-lg">
                          Prompt #{promptNumber}: {firstVideo.image_filename}
                        </CardTitle>
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                          {firstVideo.prompt_text}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const allCompleted = promptVideos
                            .filter(v => v.status === 'completed')
                            .map(v => v.video_id);
                          
                          const allSelected = allCompleted.every(id => selectedVideos.has(id));
                          
                          if (allSelected) {
                            const newSelected = new Set(selectedVideos);
                            allCompleted.forEach(id => newSelected.delete(id));
                            setSelectedVideos(newSelected);
                          } else {
                            const newSelected = new Set(selectedVideos);
                            allCompleted.forEach(id => newSelected.add(id));
                            setSelectedVideos(newSelected);
                          }
                        }}
                      >
                        {promptVideos.filter(v => v.status === 'completed').every(v => selectedVideos.has(v.video_id))
                          ? 'Deselect All'
                          : 'Select All'}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {promptVideos.map((video) => (
                        <VideoCard
                          key={video.video_id}
                          video={video}
                          isSelected={selectedVideos.has(video.video_id)}
                          onToggleSelection={(event) => handleToggleSelection(video.video_id, event)}
                          onRegenerate={() => handleRegenerateVideo(video.video_id)}
                          isRegenerating={regeneratingVideos.has(video.video_id)}
                        />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })
        )}
      </div>

      {/* Bottom Actions Bar - Glassmorphism */}
      {videos.some(v => v.status === 'completed') && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-lg border-t border-gray-200/50 shadow-2xl animate-in slide-in-from-bottom-4 duration-300">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <Checkbox
                  id="select-all"
                  checked={videos.filter(v => v.status === 'completed').length === selectedVideos.size && selectedVideos.size > 0}
                  onCheckedChange={handleSelectAll}
                  className="transition-transform hover:scale-110"
                />
                <label htmlFor="select-all" className="text-sm font-medium cursor-pointer hover:text-blue-600 transition-colors">
                  Select All ({selectedVideos.size} selected)
                </label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="text-xs text-gray-500 italic cursor-help hover:text-gray-700 transition-colors">
                        💡 Tip: Hold Shift to select range
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Hold Shift and click to select a range of videos</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              <div className="flex items-center gap-3">
                <Input
                  placeholder="Folder name for download"
                  value={downloadFolderName}
                  onChange={(e) => setDownloadFolderName(e.target.value)}
                  className="w-64 bg-white/90 backdrop-blur-sm transition-all focus:scale-105"
                />

                <Button
                  variant="outline"
                  onClick={handleUpscale}
                  disabled={selectedVideos.size === 0}
                  className="transition-all duration-200 hover:scale-105 hover:shadow-lg bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100"
                >
                  <Sparkles className="w-4 h-4 mr-2 animate-pulse" />
                  Upscale to 4K
                </Button>

                <Button
                  onClick={() => handleDownload('720p')}
                  disabled={selectedVideos.size === 0 || isDownloading}
                  className="transition-all duration-200 hover:scale-105 hover:shadow-lg bg-gradient-to-r from-blue-600 to-blue-700"
                >
                  <Download className="w-4 h-4 mr-2" />
                  {isDownloading ? 'Downloading...' : 'Download Selected'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobDetails;
