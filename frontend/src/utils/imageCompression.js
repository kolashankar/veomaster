/**
 * Image compression utility for optimizing uploads
 * Reduces file size while maintaining quality for better performance
 */
import imageCompression from 'browser-image-compression';

/**
 * Compression options for different scenarios
 */
export const COMPRESSION_OPTIONS = {
  default: {
    maxSizeMB: 1,
    maxWidthOrHeight: 1920,
    useWebWorker: true,
    fileType: 'image/jpeg',
    initialQuality: 0.8
  },
  high: {
    maxSizeMB: 2,
    maxWidthOrHeight: 2560,
    useWebWorker: true,
    fileType: 'image/jpeg',
    initialQuality: 0.9
  },
  low: {
    maxSizeMB: 0.5,
    maxWidthOrHeight: 1280,
    useWebWorker: true,
    fileType: 'image/jpeg',
    initialQuality: 0.7
  }
};

/**
 * Compress a single image file
 * @param {File} file - The image file to compress
 * @param {Object} options - Compression options
 * @param {Function} onProgress - Progress callback (0-100)
 * @returns {Promise<File>} - Compressed image file
 */
export async function compressImage(file, options = COMPRESSION_OPTIONS.default, onProgress = null) {
  try {
    console.log('Original file size:', (file.size / 1024 / 1024).toFixed(2), 'MB');
    
    const compressedFile = await imageCompression(file, {
      ...options,
      onProgress: (progress) => {
        if (onProgress) {
          onProgress(progress);
        }
        console.log('Compression progress:', progress + '%');
      }
    });
    
    console.log('Compressed file size:', (compressedFile.size / 1024 / 1024).toFixed(2), 'MB');
    console.log('Compression ratio:', ((1 - compressedFile.size / file.size) * 100).toFixed(1) + '%');
    
    return compressedFile;
  } catch (error) {
    console.error('Image compression failed:', error);
    // Return original file if compression fails
    return file;
  }
}

/**
 * Compress multiple images in a ZIP file
 * @param {File} zipFile - ZIP file containing images
 * @param {Object} options - Compression options
 * @param {Function} onProgress - Progress callback
 * @returns {Promise<File>} - ZIP file with compressed images (or original if processing fails)
 */
export async function compressImagesInZip(zipFile, options = COMPRESSION_OPTIONS.default, onProgress = null) {
  try {
    // Note: For ZIP files, we'll compress them on the backend
    // Frontend compression of ZIP contents is complex and may not be worth it
    // This function exists for future enhancement if needed
    
    console.log('ZIP file detected:', zipFile.name);
    console.log('Note: Images in ZIP will be processed by backend');
    
    if (onProgress) {
      onProgress(100);
    }
    
    return zipFile;
  } catch (error) {
    console.error('ZIP processing failed:', error);
    return zipFile;
  }
}

/**
 * Check if file is an image
 * @param {File} file - File to check
 * @returns {boolean}
 */
export function isImageFile(file) {
  return file && file.type.startsWith('image/');
}

/**
 * Check if file is a ZIP
 * @param {File} file - File to check
 * @returns {boolean}
 */
export function isZipFile(file) {
  return file && (file.type === 'application/zip' || file.type === 'application/x-zip-compressed' || file.name.endsWith('.zip'));
}

/**
 * Get file size in human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
