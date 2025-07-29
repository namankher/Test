import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  CircularProgress,
} from '@mui/material';
import {
  Add,
  Visibility,
  Edit,
  Delete,
  TrendingUp,
  Assessment,
  AttachMoney,
  Schedule,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getQuotesDashboard, deleteQuote } from '../services/api';
import { useSnackbar } from 'notistack';

function Dashboard() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  
  const { data: dashboardData, isLoading, refetch } = useQuery(
    'quotes-dashboard',
    () => getQuotesDashboard(),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const quotes = dashboardData?.data?.quotes || [];
  const totalCount = dashboardData?.data?.total_count || 0;

  const getStatusColor = (status) => {
    const statusColors = {
      pending: 'default',
      analyzing: 'info',
      ready_for_review: 'warning',
      approved: 'success',
      sent_to_client: 'primary',
      accepted: 'success',
      rejected: 'error',
    };
    return statusColors[status] || 'default';
  };

  const getStatusLabel = (status) => {
    const statusLabels = {
      pending: 'Pending',
      analyzing: 'Analyzing',
      ready_for_review: 'Ready for Review',
      approved: 'Approved',
      sent_to_client: 'Sent to Client',
      accepted: 'Accepted',
      rejected: 'Rejected',
    };
    return statusLabels[status] || status;
  };

  const handleDeleteQuote = async (quoteId) => {
    if (window.confirm('Are you sure you want to delete this quote?')) {
      try {
        await deleteQuote(quoteId);
        enqueueSnackbar('Quote deleted successfully', { variant: 'success' });
        refetch();
      } catch (error) {
        enqueueSnackbar('Failed to delete quote', { variant: 'error' });
      }
    }
  };

  const formatCurrency = (amount) => {
    if (!amount) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const calculateStats = () => {
    const totalValue = quotes.reduce((sum, quote) => sum + (quote.total_value || 0), 0);
    const totalMargin = quotes.reduce((sum, quote) => sum + (quote.margin_amount || 0), 0);
    const avgDeliveryDays = quotes.reduce((sum, quote) => sum + (quote.delivery_days || 0), 0) / quotes.length || 0;
    
    return {
      totalValue,
      totalMargin,
      avgDeliveryDays: Math.round(avgDeliveryDays),
      activeQuotes: quotes.filter(q => !['accepted', 'rejected'].includes(q.status)).length,
    };
  };

  const stats = calculateStats();

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Manufacturing Quotes Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => navigate('/new-quote')}
        >
          New Quote
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AttachMoney color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Value
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(stats.totalValue)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Margin
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(stats.totalMargin)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assessment color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Quotes
                  </Typography>
                  <Typography variant="h6">
                    {stats.activeQuotes}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Schedule color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Avg. Delivery
                  </Typography>
                  <Typography variant="h6">
                    {stats.avgDeliveryDays} days
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quotes Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Quotes ({totalCount})
          </Typography>
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Quote ID</TableCell>
                  <TableCell>Client</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Parts</TableCell>
                  <TableCell>Value</TableCell>
                  <TableCell>Delivery</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {quotes.map((quote) => (
                  <TableRow key={quote.quote_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {quote.quote_id.substring(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {quote.client_name}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {quote.client_email}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(quote.status)}
                        color={getStatusColor(quote.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{quote.parts_count || 0}</TableCell>
                    <TableCell>
                      {formatCurrency(quote.total_value)}
                    </TableCell>
                    <TableCell>
                      {quote.delivery_days ? `${quote.delivery_days} days` : '-'}
                    </TableCell>
                    <TableCell>
                      {new Date(quote.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/quote/${quote.quote_id}`)}
                      >
                        <Visibility />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteQuote(quote.quote_id)}
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {quotes.length === 0 && (
            <Box textAlign="center" py={4}>
              <Typography color="textSecondary">
                No quotes found. Create your first quote to get started.
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => navigate('/new-quote')}
                sx={{ mt: 2 }}
              >
                Create New Quote
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default Dashboard;