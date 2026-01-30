import React, { useRef, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Loader2,
  Sparkles 
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const VideoCard = ({ video, isSelected, onToggleSelection, onRegenerate, isRegenerating = false }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const getStatusBadge = () => {
    switch (video.status) {
      case 'queued':
        return (
          <Badge variant="outline" className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Queued
          </Badge>
        );
      case 'generating':
        return (
          <Badge variant="default" className="flex items-center gap-1">
            <Loader2 className="w-3 h-3 animate-spin" />
            Generating
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            Failed
          </Badge>
        );
      default:
        return null;
    }
  };

  const getErrorMessage = () => {
    if (!video.error_message) return null;

    const errorMessages = {
      high_demand: 'Flow is experiencing high demand. Retrying...',
      prominent_people: 'Prompt violates policy about prominent people',
      policy_violation: 'Prompt violates content policy',
      timeout: 'Generation timed out',
      unknown: video.error_message,
    };

    return errorMessages[video.error_type] || video.error_message;
  };

  const isRetryable = video.error_type === 'high_demand' || video.error_type === 'timeout';

  return (
    <Card 
      className={`group overflow-hidden transition-all duration-300 hover:shadow-xl ${
        video.status === 'failed' ? 'border-red-300 border-2' : ''
      } ${
        isSelected 
          ? 'ring-2 ring-blue-500 shadow-lg scale-[1.02]' 
          : 'hover:scale-[1.01]'
      } backdrop-blur-sm bg-white/90`}
    >
      <CardContent className="p-0">
        {/* Video Player or Placeholder */}
        <div className="relative aspect-[9/16] bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
          {video.status === 'completed' && (video.cloudflare_url || video.telegram_url) ? (
            <>
              <video
                ref={videoRef}
                src={video.cloudflare_url || video.telegram_url}
                className="w-full h-full object-contain"
                loop
                onEnded={() => setIsPlaying(false)}
              />
              
              {/* Play/Pause Overlay */}
              <div 
                className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 cursor-pointer"
                onClick={handlePlayPause}
              >
                <div className="bg-white/20 backdrop-blur-md rounded-full p-4 transform group-hover:scale-110 transition-transform duration-300">
                  {isPlaying ? (
                    <Pause className="w-12 h-12 text-white drop-shadow-lg" />
                  ) : (
                    <Play className="w-12 h-12 text-white drop-shadow-lg" />
                  )}
                </div>
              </div>

              {/* Selection Checkbox - Glassmorphism */}
              <div className="absolute top-3 left-3">
                <div 
                  className="bg-white/90 backdrop-blur-md rounded-md p-2 shadow-lg cursor-pointer hover:bg-white transition-all duration-200 hover:scale-105"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleSelection(e);
                  }}
                >
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={(checked) => onToggleSelection()}
                  />
                </div>
              </div>

              {/* Status Badge - Enhanced */}
              <div className="absolute top-3 right-3 animate-in fade-in slide-in-from-top-2 duration-300">
                {getStatusBadge()}
              </div>

              {/* Upscaled Badge - Glassmorphism with animation */}
              {video.upscaled && (
                <div className="absolute bottom-3 left-3 animate-in fade-in slide-in-from-bottom-2 duration-500">
                  <Badge className="bg-gradient-to-r from-purple-600 to-pink-600 text-white flex items-center gap-1 backdrop-blur-sm shadow-lg">
                    <Sparkles className="w-3 h-3 animate-pulse" />
                    4K Ultra HD
                  </Badge>
                </div>
              )}

              {/* Video Index Badge */}
              <div className="absolute bottom-3 right-3">
                <Badge variant="outline" className="bg-white">
                  Output {video.video_index}
                </Badge>
              </div>
            </>
          ) : video.status === 'generating' ? (
            <div className="w-full h-full flex flex-col items-center justify-center text-white space-y-4 animate-pulse">
              <div className="relative">
                <Loader2 className="w-16 h-16 animate-spin text-blue-400" />
                <div className="absolute inset-0 w-16 h-16 rounded-full bg-blue-400/20 animate-ping" />
              </div>
              <p className="text-sm font-medium animate-bounce">Generating video...</p>
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          ) : video.status === 'queued' ? (
            <div className="w-full h-full flex flex-col items-center justify-center text-white space-y-4">
              <div className="relative">
                <Clock className="w-12 h-12 text-gray-400" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse" />
              </div>
              <p className="text-sm">Queued for generation</p>
            </div>
          ) : video.status === 'failed' ? (
            <div className="w-full h-full flex flex-col items-center justify-center text-white space-y-4 p-4 bg-gradient-to-br from-red-900/30 to-red-800/30">
              <div className="relative">
                <AlertCircle className="w-16 h-16 text-red-400 animate-pulse" />
                <div className="absolute inset-0 w-16 h-16 rounded-full bg-red-400/20 animate-ping" />
              </div>
              <p className="text-sm text-center font-medium">{getErrorMessage()}</p>
              {isRetryable ? (
                <div className="flex items-center gap-2 text-xs text-gray-300 bg-black/30 px-4 py-2 rounded-full backdrop-blur-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="animate-pulse">Retrying automatically...</span>
                </div>
              ) : (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={onRegenerate}
                  disabled={isRegenerating}
                  className="transition-all duration-200 hover:scale-105"
                >
                  {isRegenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Regenerate
                    </>
                  )}
                </Button>
              )}
            </div>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-white">
              <p className="text-sm">No video available</p>
            </div>
          )}
        </div>

        {/* Video Info - Glassmorphism */}
        <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 border-t backdrop-blur-sm">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span className="font-medium">Output {video.video_index} of 2</span>
            <div className="flex items-center gap-2">
              {video.duration_seconds && (
                <span className="bg-white/80 px-2 py-1 rounded-full">{video.duration_seconds}s</span>
              )}
              {video.resolution && (
                <Badge variant="outline" className="text-xs bg-white/80">
                  {video.resolution}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VideoCard;
