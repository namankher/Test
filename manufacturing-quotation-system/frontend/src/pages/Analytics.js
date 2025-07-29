import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

function Analytics() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics & Reports
      </Typography>
      <Card>
        <CardContent>
          <Typography color="textSecondary">
            This page will display analytics and insights including:
            <br />• Model accuracy trends
            <br />• Quote conversion rates
            <br />• Profitability analysis
            <br />• Material and complexity breakdowns
            <br />• Performance metrics
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Analytics;