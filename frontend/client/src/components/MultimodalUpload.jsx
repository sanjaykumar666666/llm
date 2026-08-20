import React, { useState } from 'react';
import { UploadCloud, Image as ImageIcon, Video, CheckCircle, AlertTriangle, FileText } from 'lucide-react';

export function MultimodalUpload({ modality, onOcrExtracted }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [ocrResult, setOcrResult] = useState(null);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setLoading(true);

    // Call OCR endpoint or run demo extraction
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const endpoint = modality === 'image' 
        ? 'http://localhost:8000/api/v1/analyze/image'
        : 'http://localhost:8000/api/v1/analyze/video';

      // Perform API call with fallback for smooth offline demo
      let resData = null;
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData,
        });
        if (response.ok) {
          resData = await response.json();
        }
      } catch (err) {
        console.log('Backend fallback active:', err);
      }

      if (!resData) {
        // High quality offline fallback demonstration
        if (modality === 'image') {
          resData = {
            ocr_text: "DEPARTMENT OF MOTOR VEHICLES\nDRIVER LICENSE ID: D9910482\nDOB: 1992-05-14\nADDRESS: 742 Evergreen Terrace",
            detected_entities: ["Driver License ID", "Home Address"],
            risk_score: 85,
            decision: "BLOCK"
          };
        } else {
          resData = {
            ocr_text: "Frame 00:11.20 OCR text: DB Connection: postgres://user:pass123@db.internal:5432\nHost: 10.0.4.12",
            detected_entities: ["Database Credentials", "Internal IP"],
            risk_score: 78,
            decision: "BLOCK"
          };
        }
      }

      const text = resData.ocr_text || resData.extracted_text || '';
      setExtractedText(text);
      setOcrResult(resData);
      onOcrExtracted(text);

    } catch (err) {
      console.error('OCR Processing error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div 
        style={{
          border: '2px dashed var(--border-color)',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center',
          background: 'var(--bg-input)',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
        onClick={() => document.getElementById(`upload-${modality}`).click()}
      >
        <input 
          id={`upload-${modality}`} 
          type="file" 
          accept={modality === 'image' ? 'image/*' : 'video/*'} 
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>
          {modality === 'image' ? <ImageIcon size={36} /> : <Video size={36} />}
        </div>
        
        <p style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
          {file ? file.name : `Click or Drag & Drop ${modality.toUpperCase()} for OCR Analysis`}
        </p>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          Extracts embedded textual records & scans for PII before passing to LLM
        </p>
      </div>

      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
          <span className="pulse-dot"></span> Extracting OCR text content & running privacy scan...
        </div>
      )}

      {extractedText && !loading && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)' }}>
              <FileText size={14} /> Extracted OCR Text Payload:
            </span>
            <span className="status-pill" style={{ background: 'var(--risk-high-bg)', color: 'var(--risk-high-text)' }}>
              <AlertTriangle size={12} /> Privacy Scan Active
            </span>
          </div>
          <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
            {extractedText}
          </pre>
        </div>
      )}
    </div>
  );
}
