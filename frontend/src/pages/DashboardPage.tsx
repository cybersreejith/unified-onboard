import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Box,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Assignment as JobsIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  Speed as PerformanceIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts';
import { format, subDays } from 'date-fns';
import apiService from '../services/api';
import { DashboardStats, MigrationJob } from '../types';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 48,
            height: 48,
            borderRadius: 2,
            bgcolor: `${color}.light`,
            color: `${color}.main`,
            mr: 2,
          }}
        >
          {icon}
        </Box>
        <Box>
          <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [jobs, setJobs] = useState<MigrationJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, jobsData] = await Promise.all([
        apiService.getDashboardStats(),
        apiService.getMigrationJobs(),
      ]);
      
      setStats(statsData);
      setJobs(jobsData);
      setError('');
    } catch (err: any) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Generate mock historical data for charts
  const generateHistoricalData = () => {
    const data = [];
    for (let i = 6; i >= 0; i--) {
      const date = subDays(new Date(), i);
      data.push({
        date: format(date, 'MMM dd'),
        migrations: Math.floor(Math.random() * 10) + 5,
        success_rate: Math.floor(Math.random() * 20) + 80,
        records: Math.floor(Math.random() * 5000) + 10000,
      });
    }
    return data;
  };

  const historicalData = generateHistoricalData();

  // Prepare data for charts
  const systemMigrationData = jobs.reduce((acc, job) => {
    const key = `${job.source_system} → ${job.destination_system}`;
    if (!acc[key]) {
      acc[key] = { name: key, count: 0, success: 0, failed: 0 };
    }
    acc[key].count += 1;
    if (job.status === 'completed') acc[key].success += 1;
    if (job.status === 'failed') acc[key].failed += 1;
    return acc;
  }, {} as Record<string, any>);

  const systemMigrationChartData = Object.values(systemMigrationData);

  const statusDistributionData = [
    { name: 'Completed', value: stats?.completed_jobs || 0, color: '#4caf50' },
    { name: 'In Progress', value: stats?.in_progress_jobs || 0, color: '#2196f3' },
    { name: 'Failed', value: stats?.failed_jobs || 0, color: '#f44336' },
    { name: 'Pending', value: (stats?.total_jobs || 0) - (stats?.completed_jobs || 0) - (stats?.in_progress_jobs || 0) - (stats?.failed_jobs || 0), color: '#ff9800' },
  ].filter(item => item.value > 0);

  const recentJobs = jobs
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Migration Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Overview of migration activities and system performance
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {stats && (
        <>
          {/* Key Metrics */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Total Jobs"
                value={stats.total_jobs}
                icon={<JobsIcon />}
                color="primary"
                subtitle="All migration jobs"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Success Rate"
                value={`${stats.success_rate.toFixed(1)}%`}
                icon={<TrendingUpIcon />}
                color="success"
                subtitle="Overall success rate"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Records Migrated"
                value={stats.total_migrated_records}
                icon={<SuccessIcon />}
                color="info"
                subtitle="Successfully migrated"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Failed Records"
                value={stats.total_failed_records}
                icon={<ErrorIcon />}
                color="error"
                subtitle="Migration failures"
              />
            </Grid>
          </Grid>

          {/* Charts Section */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {/* Migration Trends */}
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Migration Trends (Last 7 Days)
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="migrations"
                      stackId="1"
                      stroke="#2196f3"
                      fill="#2196f3"
                      fillOpacity={0.6}
                      name="Migrations"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Status Distribution */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Job Status Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={statusDistributionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {statusDistributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* System Migration Patterns */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Migration Patterns by System
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={systemMigrationChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="success" stackId="a" fill="#4caf50" name="Successful" />
                    <Bar dataKey="failed" stackId="a" fill="#f44336" name="Failed" />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Success Rate Trend */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Success Rate Trend
                </Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value) => [`${value}%`, 'Success Rate']} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="success_rate"
                      stroke="#4caf50"
                      strokeWidth={3}
                      dot={{ fill: '#4caf50', strokeWidth: 2, r: 4 }}
                      name="Success Rate (%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          </Grid>

          {/* Recent Jobs Table */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Migration Jobs
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Job ID</TableCell>
                    <TableCell>Source → Destination</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Records</TableCell>
                    <TableCell>Created</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentJobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {job.id.substring(0, 8)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {job.source_system} → {job.destination_system}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={job.migration_type.replace('_', ' ').toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={job.status.replace('_', ' ').toUpperCase()}
                          size="small"
                          color={
                            job.status === 'completed' ? 'success' :
                            job.status === 'failed' ? 'error' :
                            job.status === 'in_progress' ? 'primary' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {job.progress_percentage.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {job.migrated_records.toLocaleString()} / {job.total_records.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {format(new Date(job.created_at), 'MMM dd, HH:mm')}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {recentJobs.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  No migration jobs found
                </Typography>
              </Box>
            )}
          </Paper>
        </>
      )}
    </Container>
  );
};

export default DashboardPage;