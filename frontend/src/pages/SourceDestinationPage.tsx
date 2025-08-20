import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  TextField,
  FormControlLabel,
  Switch,
  Divider,
} from '@mui/material';
import {
  ArrowForward as ArrowIcon,
  PlayArrow as StartIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { MigrationRequest, SystemConfig } from '../types';

interface IDPSystemInfo {
  id: string;
  name: string;
  description: string;
  features: string[];
  userCount?: number;
}

const SourceDestinationPage: React.FC = () => {
  const navigate = useNavigate();
  const [sourceSystem, setSourceSystem] = useState<string>('');
  const [destinationSystem, setDestinationSystem] = useState<string>('');
  const [migrationType, setMigrationType] = useState<'one_time' | 'runtime'>('one_time');
  const [batchSize, setBatchSize] = useState<number>(1000);
  const [includeHistorical, setIncludeHistorical] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [supportedSystems, setSupportedSystems] = useState<string[]>([]);
  const [systemConfigs, setSystemConfigs] = useState<Record<string, SystemConfig>>({});

  const idpSystems: Record<string, IDPSystemInfo> = {
    'AUTHE1.0': {
      id: 'AUTHE1.0',
      name: 'AUTHE 1.0',
      description: 'Legacy authentication system with nested data structures',
      features: ['User Management', 'Role-based Access', 'Session Management', 'Audit Logging'],
    },
    'AUTHE2.0': {
      id: 'AUTHE2.0',
      name: 'AUTHE 2.0',
      description: 'Modern authentication system with flattened schema',
      features: ['OAuth 2.0', 'MFA Support', 'API-first Design', 'Real-time Sync'],
    },
    'AUTHENG': {
      id: 'AUTHENG',
      name: 'AUTHENG',
      description: 'Enterprise authentication with compliance focus',
      features: ['Enterprise SSO', 'Compliance Tracking', 'Advanced Security', 'Audit Trail'],
    },
  };

  useEffect(() => {
    loadSupportedSystems();
  }, []);

  useEffect(() => {
    if (sourceSystem) {
      loadSystemUserCount(sourceSystem);
    }
  }, [sourceSystem]);

  const loadSupportedSystems = async () => {
    try {
      const systems = await apiService.getSupportedSystems();
      setSupportedSystems(systems);
      
      // Load system configurations
      const configs: Record<string, SystemConfig> = {};
      for (const system of systems) {
        try {
          const config = await apiService.getSystemConfig(system);
          configs[system] = config;
        } catch (err) {
          console.warn(`Failed to load config for ${system}`);
        }
      }
      setSystemConfigs(configs);
    } catch (err) {
      setError('Failed to load supported systems');
    }
  };

  const loadSystemUserCount = async (systemType: string) => {
    try {
      const result = await apiService.getSystemUserCount(systemType);
      if (idpSystems[systemType]) {
        idpSystems[systemType].userCount = result.count;
      }
    } catch (err) {
      console.warn(`Failed to load user count for ${systemType}`);
    }
  };

  const handleStartMigration = async () => {
    if (!sourceSystem || !destinationSystem) {
      setError('Please select both source and destination systems');
      return;
    }

    if (sourceSystem === destinationSystem) {
      setError('Source and destination systems must be different');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const migrationRequest: MigrationRequest = {
        source_system: sourceSystem,
        destination_system: destinationSystem,
        migration_type: migrationType,
        batch_size: batchSize,
        include_historical: includeHistorical,
        transformation_rules: {},
      };

      const job = await apiService.createMigrationJob(migrationRequest);
      setSuccess(`Migration job created successfully! Job ID: ${job.id}`);
      
      // Navigate to status page after a short delay
      setTimeout(() => {
        navigate('/status');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create migration job');
    } finally {
      setLoading(false);
    }
  };

  const renderSystemCard = (systemId: string, isSource: boolean) => {
    const system = idpSystems[systemId];
    const config = systemConfigs[systemId];
    const isSelected = isSource ? sourceSystem === systemId : destinationSystem === systemId;

    return (
      <Card
        key={systemId}
        sx={{
          cursor: 'pointer',
          border: isSelected ? 2 : 1,
          borderColor: isSelected ? 'primary.main' : 'grey.300',
          '&:hover': {
            borderColor: 'primary.main',
            boxShadow: 2,
          },
        }}
        onClick={() => {
          if (isSource) {
            setSourceSystem(systemId);
          } else {
            setDestinationSystem(systemId);
          }
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Typography variant="h6" component="h3">
              {system.name}
            </Typography>
            {config && (
              <Chip
                icon={<SettingsIcon />}
                label="Configured"
                size="small"
                color="success"
                variant="outlined"
              />
            )}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {system.description}
          </Typography>
          {system.userCount !== undefined && (
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Users:</strong> {system.userCount.toLocaleString()}
            </Typography>
          )}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {system.features.map((feature) => (
              <Chip
                key={feature}
                label={feature}
                size="small"
                variant="outlined"
                color="primary"
              />
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Migration Setup
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Select source and destination systems to configure your data migration
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={4}>
        {/* Source System Selection */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Source System
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Select the system you want to migrate data from
            </Typography>
            <Grid container spacing={2}>
              {supportedSystems.map((systemId) => (
                <Grid item xs={12} key={systemId}>
                  {renderSystemCard(systemId, true)}
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Arrow */}
        <Grid item xs={12} md={2}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              minHeight: 200,
            }}
          >
            <ArrowIcon sx={{ fontSize: 48, color: 'primary.main' }} />
          </Box>
        </Grid>

        {/* Destination System Selection */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Destination System
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Select the system you want to migrate data to
            </Typography>
            <Grid container spacing={2}>
              {supportedSystems.map((systemId) => (
                <Grid item xs={12} key={systemId}>
                  {renderSystemCard(systemId, false)}
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Migration Configuration */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Migration Configuration
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Migration Type</InputLabel>
                  <Select
                    value={migrationType}
                    label="Migration Type"
                    onChange={(e) => setMigrationType(e.target.value as 'one_time' | 'runtime')}
                  >
                    <MenuItem value="one_time">One-time Migration</MenuItem>
                    <MenuItem value="runtime">Runtime Migration</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Batch Size"
                  type="number"
                  value={batchSize}
                  onChange={(e) => setBatchSize(Number(e.target.value))}
                  inputProps={{ min: 100, max: 10000 }}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeHistorical}
                      onChange={(e) => setIncludeHistorical(e.target.checked)}
                    />
                  }
                  label="Include Historical Data"
                />
              </Grid>
            </Grid>

            {/* Migration Summary */}
            {sourceSystem && destinationSystem && (
              <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="h6" gutterBottom>
                  Migration Summary
                </Typography>
                <Typography variant="body2">
                  <strong>From:</strong> {idpSystems[sourceSystem]?.name} ({sourceSystem})
                </Typography>
                <Typography variant="body2">
                  <strong>To:</strong> {idpSystems[destinationSystem]?.name} ({destinationSystem})
                </Typography>
                <Typography variant="body2">
                  <strong>Type:</strong> {migrationType === 'one_time' ? 'One-time Migration' : 'Runtime Migration'}
                </Typography>
                <Typography variant="body2">
                  <strong>Batch Size:</strong> {batchSize.toLocaleString()} records
                </Typography>
                {idpSystems[sourceSystem]?.userCount && (
                  <Typography variant="body2">
                    <strong>Estimated Records:</strong> {idpSystems[sourceSystem].userCount!.toLocaleString()}
                  </Typography>
                )}
              </Box>
            )}

            {/* Start Migration Button */}
            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} /> : <StartIcon />}
                onClick={handleStartMigration}
                disabled={!sourceSystem || !destinationSystem || loading}
                sx={{ minWidth: 200 }}
              >
                {loading ? 'Creating Migration...' : 'Start Migration'}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SourceDestinationPage;