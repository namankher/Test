import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

function Settings() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>
      <Card>
        <CardContent>
          <Typography color="textSecondary">
            This page will provide configuration options for:
            <br />• Company information and branding
            <br />• Default pricing parameters
            <br />• Material cost database
            <br />• Email templates and settings
            <br />• User management
            <br />• Model training parameters
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Settings;