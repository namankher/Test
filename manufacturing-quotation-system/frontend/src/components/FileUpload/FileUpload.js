import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  Delete,
  CheckCircle,
} from '@mui/icons-material';

const acceptedFileTypes = {
  'application/step': ['.step', '.stp'],
  'application/octet-stream': ['.stl'],
  'application/acad': ['.dwg'],
  'application/dxf': ['.dxf'],
  'application/pdf': ['.pdf'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/tiff': ['.tiff', '.tif'],
};

const maxFileSize = 50 * 1024 * 1024; // 50MB

function FileUpload({ onFileUpload, uploadedFiles, loading }) {
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      console.error('Rejected files:', rejectedFiles);
      return;
    }
    
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    maxSize: maxFileSize,
    multiple: true,
  });

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'cad_3d':
        return '🧊';
      case 'cad_2d':
        return '📐';
      case 'pdf':
        return '📄';
      case 'image':
        return '🖼️';
      default:
        return '📁';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'primary.light' : 'grey.50',
          cursor: 'pointer',
          textAlign: 'center',
          mb: 3,
          transition: 'all 0.3s ease',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'primary.light',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          or click to browse files
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Chip label="STEP" size="small" sx={{ mr: 1 }} />
          <Chip label="STL" size="small" sx={{ mr: 1 }} />
          <Chip label="DWG" size="small" sx={{ mr: 1 }} />
          <Chip label="DXF" size="small" sx={{ mr: 1 }} />
          <Chip label="PDF" size="small" sx={{ mr: 1 }} />
          <Chip label="Images" size="small" />
        </Box>
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          Maximum file size: 50MB per file
        </Typography>
      </Paper>

      {loading && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" gutterBottom>
            Uploading files...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      {uploadedFiles.length > 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Uploaded Files ({uploadedFiles.length})
          </Typography>
          <List>
            {uploadedFiles.map((file, index) => (
              <ListItem
                key={index}
                sx={{
                  border: 1,
                  borderColor: 'grey.200',
                  borderRadius: 1,
                  mb: 1,
                }}
              >
                <ListItemIcon>
                  <Box sx={{ fontSize: '24px' }}>
                    {getFileIcon(file.file_type)}
                  </Box>
                </ListItemIcon>
                <ListItemText
                  primary={file.filename}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        Type: {file.file_type} • Size: {formatFileSize(file.file_size)}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Uploaded: {new Date(file.upload_timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                />
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <IconButton
                  edge="end"
                  color="error"
                  onClick={() => {
                    // In a real implementation, you would call an API to delete the file
                    console.log('Delete file:', file.file_id);
                  }}
                >
                  <Delete />
                </IconButton>
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  );
}

export default FileUpload;