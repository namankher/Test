import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon } from '@heroicons/react/24/outline';

const Upload: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setUploadedFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.dwg', '.step', '.stp', '.iges', '.igs'],
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg']
    },
    multiple: true
  });

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload CAD Files</h1>
        <p className="mt-2 text-gray-600">
          Upload your CAD drawings and technical specifications for AI analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div
            {...getRootProps()}
            className={`card p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-primary-300 bg-primary-50' : 'border-gray-300'
            }`}
          >
            <input {...getInputProps()} />
            <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
            <div className="mt-4">
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
              </p>
              <p className="text-gray-600">
                or <span className="text-primary-600 font-medium">browse</span> to choose files
              </p>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Supports: DWG, STEP, IGES, PDF, PNG, JPG (max 100MB)
            </div>
          </div>

          {uploadedFiles.length > 0 && (
            <div className="mt-6 card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Uploaded Files ({uploadedFiles.length})
              </h3>
              <div className="space-y-3">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center">
                      <DocumentIcon className="h-8 w-8 text-gray-400" />
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-error-600 hover:text-error-700 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setUploadedFiles([])}
                  className="btn-outline"
                >
                  Clear All
                </button>
                <button className="btn-primary">
                  Process Files with AI
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Supported Formats
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">DWG</span>
                <span className="text-gray-900">AutoCAD drawings</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">STEP</span>
                <span className="text-gray-900">3D CAD models</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">IGES</span>
                <span className="text-gray-900">3D surface models</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">PDF</span>
                <span className="text-gray-900">Technical drawings</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Images</span>
                <span className="text-gray-900">PNG, JPG drawings</span>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              AI Processing
            </h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>✓ Automatic dimension extraction</p>
              <p>✓ Material type detection</p>
              <p>✓ Machining operation analysis</p>
              <p>✓ Cost & time estimation</p>
              <p>✓ Complexity assessment</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;