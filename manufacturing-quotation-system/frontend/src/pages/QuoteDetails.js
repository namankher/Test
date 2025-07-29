import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Card, CardContent } from '@mui/material';

function QuoteDetails() {
  const { quoteId } = useParams();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Quote Details
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quote ID: {quoteId}
          </Typography>
          <Typography color="textSecondary">
            This page will show detailed information about the quote including:
            <br />• Analysis results and part details
            <br />• Cost breakdown and pricing
            <br />• Quote status and progress
            <br />• Actions (approve, generate client quote, etc.)
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default QuoteDetails;