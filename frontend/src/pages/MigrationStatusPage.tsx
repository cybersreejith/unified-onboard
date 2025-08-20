import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Box,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import apiService from '../services/api';
import { MigrationJob } from '../types';

const MigrationStatusPage: React.FC = () => {
  const [jobs, setJobs] = useState<MigrationJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [selectedJob, setSelectedJob] = useState<MigrationJob | null>(null);
  const [detailsOpen, setDetailsOpen] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  useEffect(() => {
    loadMigrationJobs();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        loadMigrationJobs();
      }, 5000); // Refresh every 5 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const loadMigrationJobs = async () => {
    try {
      const jobsData = await apiService.getMigrationJobs();
      setJobs(jobsData);
      setError('');
    } catch (err: any) {
      setError('Failed to load migration jobs');
      console.error('Error loading jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleJobAction = async (jobId: string, action: 'pause' | 'resume' | 'delete') => {
    try {
      switch (action) {
        case 'pause':
          await apiService.pauseMigrationJob(jobId);
          break;
        case 'resume':
          await apiService.resumeMigrationJob(jobId);
          break;
        case 'delete':
          await apiService.deleteMigrationJob(jobId);
          break;
      }
      await loadMigrationJobs();
    } catch (err: any) {
      setError(`Failed to ${action} migration job`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'failed':
        return 'error';
      case 'paused':
        return 'warning';
      case 'pending':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'pending':
        return <PendingIcon />;
      default:
        return undefined;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const openJobDetails = (job: MigrationJob) => {
    setSelectedJob(job);
    setDetailsOpen(true);
  };

  const closeJobDetails = () => {
    setSelectedJob(null);
    setDetailsOpen(false);
  };

  const renderJobCard = (job: MigrationJob) => (
    <Card key={job.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="h3">
              {job.source_system} → {job.destination_system}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Job ID: {job.id}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={getStatusIcon(job.status)}
              label={job.status.replace('_', ' ').toUpperCase()}
              color={getStatusColor(job.status) as any}
              size="small"
            />
            <Chip
              label={job.migration_type.replace('_', ' ').toUpperCase()}
              variant="outlined"
              size="small"
            />
          </Box>
        </Box>

        {/* Progress Bar */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Progress</Typography>
            <Typography variant="body2">{job.progress_percentage.toFixed(1)}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={job.progress_percentage}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Statistics */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">Total</Typography>
            <Typography variant="h6">{job.total_records.toLocaleString()}</Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">Migrated</Typography>
            <Typography variant="h6" color="success.main">
              {job.migrated_records.toLocaleString()}
            </Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">Failed</Typography>
            <Typography variant="h6" color="error.main">
              {job.failed_records.toLocaleString()}
            </Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="body2" color="text.secondary">Duration</Typography>
            <Typography variant="h6">
              {formatDuration(job.created_at, job.status === 'completed' ? job.updated_at : undefined)}
            </Typography>
          </Grid>
        </Grid>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {job.status === 'in_progress' && (
              <Button
                size="small"
                startIcon={<PauseIcon />}
                onClick={() => handleJobAction(job.id, 'pause')}
              >
                Pause
              </Button>
            )}
            {job.status === 'paused' && (
              <Button
                size="small"
                startIcon={<PlayIcon />}
                onClick={() => handleJobAction(job.id, 'resume')}
              >
                Resume
              </Button>
            )}
            {(job.status === 'completed' || job.status === 'failed') && (
              <Button
                size="small"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => handleJobAction(job.id, 'delete')}
              >
                Delete
              </Button>
            )}
          </Box>
          <Button
            size="small"
            startIcon={<InfoIcon />}
            onClick={() => openJobDetails(job)}
          >
            Details
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1">
          Migration Status
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}>
            <IconButton
              onClick={() => setAutoRefresh(!autoRefresh)}
              color={autoRefresh ? 'primary' : 'default'}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadMigrationJobs}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && jobs.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <LinearProgress sx={{ width: '50%' }} />
        </Box>
      ) : jobs.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No migration jobs found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Create a new migration job from the Migration Setup page
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {jobs.map((job) => (
            <Grid item xs={12} key={job.id}>
              {renderJobCard(job)}
            </Grid>
          ))}
        </Grid>
      )}

      {/* Job Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={closeJobDetails}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Migration Job Details
          {selectedJob && (
            <Typography variant="body2" color="text.secondary">
              Job ID: {selectedJob.id}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedJob && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Source System</Typography>
                  <Typography variant="body1">{selectedJob.source_system}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Destination System</Typography>
                  <Typography variant="body1">{selectedJob.destination_system}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Migration Type</Typography>
                  <Typography variant="body1">
                    {selectedJob.migration_type.replace('_', ' ').toUpperCase()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Status</Typography>
                  <Chip
                    icon={getStatusIcon(selectedJob.status)}
                    label={selectedJob.status.replace('_', ' ').toUpperCase()}
                    color={getStatusColor(selectedJob.status) as any}
                    size="small"
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Created At</Typography>
                  <Typography variant="body1">
                    {format(new Date(selectedJob.created_at), 'PPpp')}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Last Updated</Typography>
                  <Typography variant="body1">
                    {format(new Date(selectedJob.updated_at), 'PPpp')}
                  </Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Progress Statistics
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={3}>
                  <Typography variant="subtitle2">Total Records</Typography>
                  <Typography variant="h5">{selectedJob.total_records.toLocaleString()}</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="subtitle2">Migrated</Typography>
                  <Typography variant="h5" color="success.main">
                    {selectedJob.migrated_records.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="subtitle2">Failed</Typography>
                  <Typography variant="h5" color="error.main">
                    {selectedJob.failed_records.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="subtitle2">Success Rate</Typography>
                  <Typography variant="h5">
                    {selectedJob.migrated_records > 0
                      ? ((selectedJob.migrated_records / (selectedJob.migrated_records + selectedJob.failed_records)) * 100).toFixed(1)
                      : 0}%
                  </Typography>
                </Grid>
              </Grid>

              {selectedJob.error_message && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Error Information
                  </Typography>
                  <Alert severity="error">
                    {selectedJob.error_message}
                  </Alert>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeJobDetails}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MigrationStatusPage;