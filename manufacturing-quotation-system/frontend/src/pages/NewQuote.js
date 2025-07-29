import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  CircularProgress,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import FileUpload from '../components/FileUpload/FileUpload';
import { createQuote, uploadFiles, startAnalysis } from '../services/api';

const steps = ['Quote Information', 'Upload Drawings', 'Review & Submit'];

function NewQuote() {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [quoteData, setQuoteData] = useState({
    clientName: '',
    clientEmail: '',
    projectDescription: '',
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [quoteId, setQuoteId] = useState(null);
  
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const handleNext = async () => {
    if (activeStep === 0) {
      // Validate quote information
      if (!quoteData.clientName || !quoteData.clientEmail) {
        enqueueSnackbar('Please fill in all required fields', { variant: 'error' });
        return;
      }
      
      try {
        setLoading(true);
        const response = await createQuote(quoteData);
        setQuoteId(response.data.quote_id);
        setActiveStep(activeStep + 1);
      } catch (error) {
        enqueueSnackbar('Failed to create quote', { variant: 'error' });
      } finally {
        setLoading(false);
      }
    } else if (activeStep === 1) {
      // Validate file uploads
      if (uploadedFiles.length === 0) {
        enqueueSnackbar('Please upload at least one drawing file', { variant: 'error' });
        return;
      }
      
      setActiveStep(activeStep + 1);
    } else if (activeStep === 2) {
      // Submit quote and start analysis
      try {
        setLoading(true);
        await startAnalysis(quoteId);
        enqueueSnackbar('Quote submitted successfully! Analysis started.', { variant: 'success' });
        navigate(`/quote/${quoteId}`);
      } catch (error) {
        enqueueSnackbar('Failed to start analysis', { variant: 'error' });
      } finally {
        setLoading(false);
      }
    }
  };

  const handleBack = () => {
    setActiveStep(activeStep - 1);
  };

  const handleInputChange = (field) => (event) => {
    setQuoteData({
      ...quoteData,
      [field]: event.target.value,
    });
  };

  const handleFileUpload = async (files) => {
    if (!quoteId) return;
    
    try {
      setLoading(true);
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await uploadFiles(quoteId, formData);
      setUploadedFiles(prev => [...prev, ...response.data]);
      enqueueSnackbar(`${files.length} file(s) uploaded successfully`, { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to upload files', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quote Information
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    required
                    fullWidth
                    label="Client Name"
                    value={quoteData.clientName}
                    onChange={handleInputChange('clientName')}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    required
                    fullWidth
                    label="Client Email"
                    type="email"
                    value={quoteData.clientEmail}
                    onChange={handleInputChange('clientEmail')}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Project Description"
                    value={quoteData.projectDescription}
                    onChange={handleInputChange('projectDescription')}
                    placeholder="Describe the project, any special requirements, materials preferences, etc."
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        );
      
      case 1:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Technical Drawings
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Upload 2D/3D drawings, CAD files, PDFs, or images. Supported formats: STEP, STL, DWG, DXF, PDF, PNG, JPG
              </Typography>
              <FileUpload
                onFileUpload={handleFileUpload}
                uploadedFiles={uploadedFiles}
                loading={loading}
              />
            </CardContent>
          </Card>
        );
      
      case 2:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Review & Submit
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    Quote Information:
                  </Typography>
                  <Typography variant="body2">Client: {quoteData.clientName}</Typography>
                  <Typography variant="body2">Email: {quoteData.clientEmail}</Typography>
                  {quoteData.projectDescription && (
                    <Typography variant="body2">Description: {quoteData.projectDescription}</Typography>
                  )}
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    Uploaded Files ({uploadedFiles.length}):
                  </Typography>
                  {uploadedFiles.map((file, index) => (
                    <Typography key={index} variant="body2">
                      • {file.filename} ({file.file_type})
                    </Typography>
                  ))}
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Clicking "Submit Quote" will start the AI analysis process. You'll be redirected 
                    to the quote details page where you can monitor the progress.
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        );
      
      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Create New Quote
      </Typography>
      
      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Box sx={{ mb: 4 }}>
        {renderStepContent(activeStep)}
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          disabled={activeStep === 0}
          onClick={handleBack}
          sx={{ mr: 1 }}
        >
          Back
        </Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={loading}
          startIcon={loading && <CircularProgress size={20} />}
        >
          {activeStep === steps.length - 1 ? 'Submit Quote' : 'Next'}
        </Button>
      </Box>
    </Box>
  );
}

export default NewQuote;