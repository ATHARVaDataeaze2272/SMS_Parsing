import React from 'react';
import { Upload, FilePlus, Check, X } from 'lucide-react';

const FileUploader = ({
  selectedFile,
  processing,
  processingStatus,
  uploadResponse,
  handleFileChange,
  handleFileUpload,
  handleProcessExistingFile,
}) => {
  // Renders progress bar based on processingStatus
  const renderProgressBar = () => {
    const percentage = processingStatus.total > 0
      ? Math.floor((processingStatus.processed / processingStatus.total) * 100)
      : 0;
  
    console.log('Rendering progress bar with status:', processingStatus, 'Percentage:', percentage);
  
    return (
      <div className="mt-4">
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium">Processing Progress</span>
          <span className="text-sm font-medium">{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>Processed: {processingStatus.processed}/{processingStatus.total}</span>
          <span>Success: {processingStatus.succeeded} | Failed: {processingStatus.failed}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="mb-6 border rounded-lg overflow-hidden card">
      <div className="bg-gray-100 p-4 border-b">
        <h3 className="text-lg font-medium">Upload Messages</h3>
      </div>
      <div className="p-4">
        <div className="mb-5">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Select JSON File</label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500"
                    >
                      <span>Upload a file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        className="sr-only"
                        accept=".json"
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-gray-500">JSON files only (array of objects with 'message' or 'body' field)</p>
                </div>
              </div>
              {selectedFile && (
                <p className="mt-2 text-sm text-gray-500">Selected file: {selectedFile.name}</p>
              )}
            </div>
            <div className="flex flex-col space-y-2">
              {/* Upload button, disabled during processing or if no file selected */}
              <button
                onClick={handleFileUpload}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                disabled={!selectedFile || processing}
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload & Process
              </button>
              {/* Process existing file button, disabled during processing */}
              <button
                onClick={handleProcessExistingFile}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                disabled={processing}
              >
                <FilePlus className="w-4 h-4 mr-2" />
                Process Existing File
              </button>
            </div>
          </div>
        </div>
        {/* Display upload response (success or error) */}
        {uploadResponse && (
          <div
            className={`p-4 rounded mb-4 ${
              uploadResponse.status === 'accepted' || uploadResponse.status === 'success'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="flex items-start">
              {(uploadResponse.status === 'accepted' || uploadResponse.status === 'success') ? (
                <Check className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
              ) : (
                <X className="w-5 h-5 text-red-500 mr-2 mt-0.5" />
              )}
              <p
                className={
                  (uploadResponse.status === 'accepted' || uploadResponse.status === 'success')
                    ? 'text-green-700'
                    : 'text-red-700'
                }
              >
                {uploadResponse.message}
              </p>
            </div>
          </div>
        )}
        {/* Render progress bar during processing */}
        {processing && renderProgressBar()}
      </div>
    </div>
  );
};

export default FileUploader;