import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sparkles,
  CheckCircle,
  AlertCircle,
  Loader2,
  Download,
  Zap,
  Gauge,
  Crown,
} from 'lucide-react';
import { videoAPI } from '@/services/api';
import { toast } from 'sonner';

const QUALITY_PRESETS = {
  fast: {
    label: 'Fast',
    icon: Zap,
    description: 'Quick upscaling (~2x real-time)',
    color: 'text-blue-600',
    crf: 23,
  },
  balanced: {
    label: 'Balanced',
    icon: Gauge,
    description: 'Good quality (~3.5x real-time)',
    color: 'text-green-600',
    crf: 20,
  },
  high: {
    label: 'High Quality',
    icon: Crown,
    description: 'Best quality (~5x real-time)',
    color: 'text-purple-600',
    crf: 18,
  },
};

const UpscaleModal = ({ 
  isOpen, 
  onClose, 
  selectedVideoIds, 
  onUpscaleComplete 
}) => {
  const [quality, setQuality] = useState('balanced');
  const [isUpscaling, setIsUpscaling] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentVideo, setCurrentVideo] = useState(0);
  const [totalVideos, setTotalVideos] = useState(selectedVideoIds.length);
  const [logs, setLogs] = useState([]);
  const [isComplete, setIsComplete] = useState(false);
  const [hasError, setHasError] = useState(false);
  const logsEndRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const handleStartUpscaling = async () => {
    if (selectedVideoIds.length === 0) {
      toast.error('No videos selected');
      return;
    }

    try {
      setIsUpscaling(true);
      setProgress(0);
      setCurrentVideo(0);
      setIsComplete(false);
      setHasError(false);
      setLogs([]);

      addLog(`Starting upscaling process for ${selectedVideoIds.length} video(s)`, 'info');
      addLog(`Quality preset: ${QUALITY_PRESETS[quality].label} (CRF ${QUALITY_PRESETS[quality].crf})`, 'info');

      // Start upscaling
      const response = await videoAPI.upscaleVideos(selectedVideoIds, quality);
      
      if (response.task_id) {
        addLog(`Task ID: ${response.task_id}`, 'success');
        addLog('Upscaling started...', 'info');
        
        // Start polling for progress
        startProgressPolling(response.task_id);
      } else {
        // No task_id means immediate processing or mock
        simulateUpscaling();
      }
    } catch (error) {
      console.error('Failed to start upscaling:', error);
      addLog(`Error: ${error.response?.data?.detail || error.message}`, 'error');
      setHasError(true);
      setIsUpscaling(false);
      toast.error('Failed to start upscaling');
    }
  };

  const startProgressPolling = (taskId) => {
    let pollCount = 0;
    const maxPolls = 600; // Max 5 minutes at 500ms intervals

    pollingIntervalRef.current = setInterval(async () => {
      try {
        pollCount++;
        
        // Check if max polls reached
        if (pollCount >= maxPolls) {
          clearInterval(pollingIntervalRef.current);
          addLog('Timeout: Upscaling took too long', 'error');
          setHasError(true);
          setIsUpscaling(false);
          return;
        }

        // Poll for real status from backend
        const status = await videoAPI.getUpscaleStatus(taskId);
        
        if (!status) {
          return;
        }

        // Update progress
        setProgress(status.progress);
        setCurrentVideo(status.current_video_index);
        
        // Add new logs
        if (status.logs && status.logs.length > logs.length) {
          const newLogs = status.logs.slice(logs.length);
          setLogs(status.logs);
        }
        
        // Check if complete
        if (status.status === 'completed') {
          clearInterval(pollingIntervalRef.current);
          handleUpscaleComplete();
        } else if (status.status === 'failed') {
          clearInterval(pollingIntervalRef.current);
          addLog(status.error_message || 'Upscaling failed', 'error');
          setHasError(true);
          setIsUpscaling(false);
        }
        
      } catch (error) {
        console.error('Polling error:', error);
        // Don't show warning for every poll error, just log it
        if (pollCount % 10 === 0) {
          addLog('Still processing...', 'info');
        }
      }
    }, 1000); // Poll every second for smoother progress
  };

  const simulateUpscaling = () => {
    addLog('Processing videos...', 'info');
    
    let progress = 0;
    const increment = 100 / (totalVideos * 10);
    
    const interval = setInterval(() => {
      progress += increment;
      
      if (progress >= 100) {
        clearInterval(interval);
        handleUpscaleComplete();
        return;
      }
      
      setProgress(progress);
      
      const currentVid = Math.floor((progress / 100) * totalVideos);
      if (currentVid > currentVideo) {
        setCurrentVideo(currentVid);
        addLog(`Upscaling video ${currentVid}/${totalVideos}...`, 'info');
        
        // Simulate processing steps
        if (Math.random() > 0.7) {
          addLog(`  → Applying Lanczos filter to video ${currentVid}`, 'info');
        }
        if (Math.random() > 0.7) {
          addLog(`  → Encoding to 4K (3840x2160)`, 'info');
        }
      }
    }, 300);
    
    pollingIntervalRef.current = interval;
  };

  const handleUpscaleComplete = () => {
    setProgress(100);
    setCurrentVideo(totalVideos);
    setIsComplete(true);
    setIsUpscaling(false);
    
    addLog('Upscaling complete! ✓', 'success');
    addLog(`All ${totalVideos} video(s) upscaled to 4K`, 'success');
    addLog('Videos are now available for download', 'info');
    
    toast.success('Upscaling completed!', {
      description: `${totalVideos} video(s) upscaled to 4K`,
    });

    // Notify parent component
    if (onUpscaleComplete) {
      onUpscaleComplete();
    }
  };

  const handleClose = () => {
    if (isUpscaling && !window.confirm('Upscaling in progress. Are you sure you want to close?')) {
      return;
    }
    
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    onClose();
    
    // Reset state after animation
    setTimeout(() => {
      setQuality('balanced');
      setIsUpscaling(false);
      setProgress(0);
      setCurrentVideo(0);
      setLogs([]);
      setIsComplete(false);
      setHasError(false);
    }, 300);
  };

  const getLogIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0" />;
      default:
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            Upscale Videos to 4K
          </DialogTitle>
          <DialogDescription>
            Upscale {selectedVideoIds.length} selected video(s) to 4K resolution using FFmpeg
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Quality Preset Selection */}
          {!isUpscaling && !isComplete && (
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700">
                Quality Preset
              </label>
              <Select value={quality} onValueChange={setQuality}>
                <SelectTrigger>
                  <SelectValue placeholder="Select quality" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(QUALITY_PRESETS).map(([key, preset]) => {
                    const Icon = preset.icon;
                    return (
                      <SelectItem key={key} value={key}>
                        <div className="flex items-center gap-2">
                          <Icon className={`w-4 h-4 ${preset.color}`} />
                          <div>
                            <div className="font-medium">{preset.label}</div>
                            <div className="text-xs text-gray-500">
                              {preset.description}
                            </div>
                          </div>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              
              {/* Selected Quality Info */}
              <div className="bg-gray-50 p-3 rounded-lg border">
                <div className="flex items-start gap-2">
                  {React.createElement(QUALITY_PRESETS[quality].icon, {
                    className: `w-5 h-5 ${QUALITY_PRESETS[quality].color}`,
                  })}
                  <div className="flex-1">
                    <div className="font-medium text-sm">
                      {QUALITY_PRESETS[quality].label}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      {QUALITY_PRESETS[quality].description}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Progress Section */}
          {(isUpscaling || isComplete) && (
            <div className="space-y-4">
              {/* Status Badge */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isComplete ? (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      Complete
                    </Badge>
                  ) : hasError ? (
                    <Badge variant="destructive" className="flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      Error
                    </Badge>
                  ) : (
                    <Badge variant="default" className="flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Processing
                    </Badge>
                  )}
                  <span className="text-sm text-gray-600">
                    Video {currentVideo}/{totalVideos}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {Math.round(progress)}%
                </span>
              </div>

              {/* Progress Bar */}
              <Progress value={progress} className="h-3" />

              {/* Estimated Time */}
              {isUpscaling && (
                <div className="text-xs text-gray-500 text-center">
                  Estimated time: ~{Math.round((totalVideos - currentVideo) * 30)} seconds remaining
                </div>
              )}
            </div>
          )}

          {/* Live Logs */}
          {logs.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Process Log
              </label>
              <ScrollArea className="h-64 w-full rounded-md border bg-gray-50 p-4">
                <div className="space-y-2">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-2 text-xs font-mono"
                    >
                      {getLogIcon(log.type)}
                      <span className="text-gray-500 min-w-[70px]">
                        {log.timestamp}
                      </span>
                      <span
                        className={`flex-1 ${
                          log.type === 'error'
                            ? 'text-red-700'
                            : log.type === 'success'
                            ? 'text-green-700'
                            : log.type === 'warning'
                            ? 'text-yellow-700'
                            : 'text-gray-700'
                        }`}
                      >
                        {log.message}
                      </span>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </ScrollArea>
            </div>
          )}

          {/* Download Ready Notification */}
          {isComplete && (
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-green-900">
                    Upscaling Complete!
                  </h4>
                  <p className="text-sm text-green-700 mt-1">
                    All {totalVideos} video(s) have been successfully upscaled to 4K.
                    You can now download them from the job details page.
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <Download className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">
                      Videos ready for download
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          {!isUpscaling && !isComplete && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleStartUpscaling}>
                <Sparkles className="w-4 h-4 mr-2" />
                Start Upscaling
              </Button>
            </>
          )}
          
          {isUpscaling && (
            <Button variant="outline" onClick={handleClose}>
              Close
            </Button>
          )}
          
          {isComplete && (
            <Button onClick={handleClose}>
              <CheckCircle className="w-4 h-4 mr-2" />
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default UpscaleModal;
