import React, { useState } from 'react';

export default function DocumentUpload({ onUploaded, apiUrl }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onload = (event) => {
        setPreview(event.target.result.substring(0, 500) + '...');
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${apiUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.status === 'success') {
        onUploaded(file.name);
        setFile(null);
        setPreview(null);
      } else {
        alert('Upload failed: ' + result.message);
      }
    } catch (error) {
      alert('Error uploading file: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="document-upload">
      <h2>📄 Upload Requirements Document</h2>
      <div className="upload-input">
        <input
          type="file"
          onChange={handleFileChange}
          accept=".txt,.md,.pdf,.docx"
          disabled={uploading}
        />
        {file && <span className="selected-file">{file.name}</span>}
      </div>

      {preview && (
        <div className="preview">
          <h3>Preview</h3>
          <p>{preview}</p>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="btn btn-primary"
      >
        {uploading ? 'Uploading...' : '✅ Upload Document'}
      </button>
    </div>
  );
}
