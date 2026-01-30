import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, FolderArchive, X } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const FileUploader = ({ onFileSelect, accept, label, icon: Icon, selectedFile, onRemove }) => {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles && acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: false,
  });

  return (
    <Card
      {...getRootProps()}
      className={`p-6 border-2 border-dashed cursor-pointer transition-all ${
        isDragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      } ${selectedFile ? 'bg-green-50 border-green-500' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center justify-center space-y-3">
        {Icon ? <Icon className="w-12 h-12 text-gray-400" /> : <Upload className="w-12 h-12 text-gray-400" />}
        
        {selectedFile ? (
          <div className="flex items-center space-x-2">
            <File className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-700">
              {selectedFile.name}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="h-6 w-6 p-0 hover:bg-red-100"
            >
              <X className="w-4 h-4 text-red-600" />
            </Button>
          </div>
        ) : (
          <>
            <p className="text-sm font-medium text-gray-700">{label}</p>
            <p className="text-xs text-gray-500">
              {isDragActive ? 'Drop the file here...' : 'Drag and drop or click to browse'}
            </p>
          </>
        )}
      </div>
    </Card>
  );
};

export default FileUploader;
