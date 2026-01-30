import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Skeleton loader for video cards
 * Displays while videos are loading
 */
const VideoSkeleton = () => {
  return (
    <Card className="overflow-hidden animate-pulse">
      <CardContent className="p-0">
        {/* Video placeholder */}
        <div className="relative aspect-[9/16] bg-gradient-to-br from-gray-200 to-gray-300">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-16 border-4 border-gray-300 border-t-gray-400 rounded-full animate-spin" />
          </div>
          
          {/* Checkbox placeholder */}
          <div className="absolute top-3 left-3 w-5 h-5 bg-gray-300 rounded" />
          
          {/* Badge placeholder */}
          <div className="absolute top-3 right-3 w-20 h-6 bg-gray-300 rounded-full" />
        </div>
        
        {/* Info placeholder */}
        <div className="p-4 space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-1/2" />
          <div className="flex gap-2">
            <div className="h-3 bg-gray-200 rounded w-16" />
            <div className="h-3 bg-gray-200 rounded w-16" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VideoSkeleton;
