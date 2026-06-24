import React, { useEffect, useState } from 'react';
import {
  FluentProvider,
  webDarkTheme,
  webLightTheme,
  Button,
  TabList,
  Tab,
  Select,
  Input,
  Label,
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Card,
  CardHeader,
  makeStyles,
  shorthands,
  tokens,
  Spinner,
  Text,
  Badge,
} from '@fluentui/react-components';
import {
  DatabaseRegular,
  MoneyRegular,
  BranchCompareRegular,
  SaveRegular,
  AddRegular,
  DeleteRegular,
  CheckmarkCircleRegular,
  WarningRegular,
  ArrowDownloadRegular,
  DualScreenHeaderRegular,
  ArrowSyncRegular,
  WeatherMoonRegular,
  WeatherSunnyRegular,
} from '@fluentui/react-icons';

import { useAppStore } from './store';
import type { Override } from './store';

const tokensAny = tokens as any;

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexDirection: 'row',
    height: '100vh',
    width: '100vw',
    boxSizing: 'border-box',
    overflow: 'hidden',
    backgroundColor: tokensAny.colorNeutralBackground1,
    fontFamily: "'Segoe UI Variable', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif",
  },
  sidebar: {
    width: '320px',
    minWidth: '320px',
    flexShrink: 0,
    backgroundColor: tokensAny.colorNeutralBackground2,
    borderRight: `1px solid ${tokensAny.colorNeutralStroke1}`,
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.padding('16px'),
    boxSizing: 'border-box',
    overflowY: 'auto',
  },
  sidebarSection: {
    marginBottom: '20px',
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('8px'),
  },
  sidebarTitle: {
    fontWeight: 600,
    fontSize: '12px',
    color: tokensAny.colorNeutralText4,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    marginBottom: '8px',
  },
  workspace: {
    flexGrow: 1,
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.padding('20px'),
    boxSizing: 'border-box',
    overflowY: 'auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  titleArea: {
    display: 'flex',
    flexDirection: 'column',
  },
  mainTitle: {
    fontSize: '24px',
    fontWeight: 600,
    color: tokensAny.colorNeutralText1,
  },
  subTitle: {
    fontSize: '13px',
    color: tokensAny.colorNeutralText3,
    marginTop: '4px',
  },
  tabList: {
    marginBottom: '16px',
    borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`,
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    ...shorthands.gap('16px'),
    marginBottom: '20px',
  },
  kpiCard: {
    position: 'relative',
    backgroundColor: tokensAny.colorNeutralBackground1,
    border: `1px solid ${tokensAny.colorNeutralStroke1}`,
    ...shorthands.borderRadius('8px'),
    ...shorthands.padding('16px'),
    boxSizing: 'border-box',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.02)',
    display: 'flex',
    flexDirection: 'column',
  },
  kpiHighlight: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
    backgroundColor: '#0078D4', // Fluent blue highlight
    ...shorthands.borderRadius('8px', '8px', 0, 0),
  },
  kpiTitle: {
    fontSize: '12px',
    color: tokensAny.colorNeutralText3,
    fontWeight: 500,
  },
  kpiValue: {
    fontSize: '20px',
    fontWeight: 600,
    marginTop: '8px',
    color: tokensAny.colorNeutralText1,
  },
  kpiUnit: {
    fontSize: '11px',
    color: tokensAny.colorNeutralText4,
    marginTop: '4px',
  },
  contentArea: {
    flexGrow: 1,
    display: 'flex',
    flexDirection: 'column',
    minHeight: 0,
  },
  tableContainer: {
    maxHeight: '400px',
    overflow: 'auto',
    border: `1px solid ${tokensAny.colorNeutralStroke2}`,
    ...shorthands.borderRadius('8px'),
    backgroundColor: tokensAny.colorNeutralBackground1,
  },
  denseTable: {
    '& th': {
      fontSize: '11px',
      fontWeight: 600,
      backgroundColor: tokensAny.colorNeutralBackground3,
      color: tokensAny.colorNeutralText2,
      ...shorthands.padding('8px', '12px'),
    },
    '& td': {
      fontSize: '12px',
      ...shorthands.padding('6px', '12px'),
      borderBottom: `1px solid ${tokensAny.colorNeutralStroke3}`,
    },
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    ...shorthands.gap('12px'),
    alignItems: 'end',
    backgroundColor: tokensAny.colorNeutralBackground1,
    ...shorthands.padding('16px'),
    border: `1px solid ${tokensAny.colorNeutralStroke2}`,
    ...shorthands.borderRadius('8px'),
    marginBottom: '16px',
  },
  uploadZone: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.padding('24px'),
    border: `2px dashed ${tokensAny.colorNeutralStroke2}`,
    ...shorthands.borderRadius('8px'),
    backgroundColor: tokensAny.colorNeutralBackground2,
    textAlign: 'center',
    marginBottom: '16px',
    cursor: 'pointer',
    ':hover': {
      backgroundColor: tokensAny.colorNeutralBackground1,
      ...shorthands.borderColor('#0078D4'),
    },
  },
  flexRow: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
  },
  checklistRow: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
    fontSize: '13px',
    color: tokensAny.colorNeutralText2,
  },
  greenText: {
    color: 'green',
  },
  redText: {
    color: 'red',
  },
  changeLogContainer: {
    maxHeight: '180px',
    overflowY: 'auto',
    backgroundColor: tokensAny.colorNeutralBackground3,
    ...shorthands.padding('12px'),
    ...shorthands.borderRadius('8px'),
    fontSize: '12px',
    color: tokensAny.colorNeutralText2,
    border: `1px solid ${tokensAny.colorNeutralStroke2}`,
  },
  copilotShimmer: {
    position: 'relative',
    ...shorthands.padding('1px'),
    backgroundImage: 'linear-gradient(135deg, #2870EA 0%, #F54EA2 100%)',
    ...shorthands.borderRadius('8px'),
  },
  copilotInner: {
    backgroundColor: tokensAny.colorNeutralBackground1,
    ...shorthands.padding('12px'),
    ...shorthands.borderRadius('8px'),
    fontSize: '12px',
  },
});

function App() {
  const styles = useStyles();
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>('dark');

  // Load from store
  const {
    scenarios,
    selectedScenario,
    selectedScenarioMeta,
    activePreviewTab,
    activeResultsTab,
    previewData,
    overrides,
    calculatedMetrics,
    calculatedPreview,
    currencyMode,
    calculationError,
    loadingScenarios,
    loadingData,
    loadingCalculation,
    compareScenarioA,
    compareScenarioB,
    compareResult,
    loadingCompare,
    compareError,

    fetchScenarios,
    selectScenario,
    createScenario,
    saveScenario,
    uploadScenarioFile,
    addOverride,
    removeOverride,
    clearAllOverrides,
    runComparison,
    setCurrencyMode,
    setActivePreviewTab,
    setActiveResultsTab,
    setCompareScenarioA,
    setCompareScenarioB,
  } = useAppStore();

  // Local UI States
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<'inputs' | 'pricing' | 'calculations' | 'comparison'>('inputs');
  const [newScenName, setNewScenName] = useState('');
  const [newScenDesc, setNewScenDesc] = useState('');
  const [newScenClone, setNewScenClone] = useState('');

  // File staging and diffing states
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const [stagedDiffLogs, setStagedDiffLogs] = useState<string[] | null>(null);
  const [stagedIsNew, setStagedIsNew] = useState<boolean | null>(null);
  const [stagedLoadingDiff, setStagedLoadingDiff] = useState<boolean>(false);
  const [volumeDeltaByMaterial, setVolumeDeltaByMaterial] = useState<{material_id: string; base_volume: number; new_volume: number; delta: number}[] | null>(null);
  const [priceDeltaByMaterial, setPriceDeltaByMaterial] = useState<{material_id: string; base_avg_price: number; new_avg_price: number; delta: number; pct_change: number | null}[] | null>(null);

  // Reset staged files when preview tab or active scenario changes
  useEffect(() => {
    setStagedFile(null);
    setStagedDiffLogs(null);
    setStagedIsNew(null);
    setVolumeDeltaByMaterial(null);
    setPriceDeltaByMaterial(null);
  }, [activePreviewTab, selectedScenario]);

  // Overrides form inputs
  const [ovMat, setOvMat] = useState('');
  const [ovCust, setOvCust] = useState('');
  const [ovShip, setOvShip] = useState('');
  const [ovDate, setOvDate] = useState('');
  const [ovPrice, setOvPrice] = useState('');

  // Fetch initial scenario list
  useEffect(() => {
    fetchScenarios();
  }, []);

  // Format currency helpers
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(val);
  };

  const formatCurrencyLocal = (val: number, symbol = '') => {
    return `${symbol} ${new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(val)}`;
  };

  const formatDecimal = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 3,
    }).format(val);
  };

  // Checklist Validation Status Helper
  const hasVolume = selectedScenarioMeta?.files_status?.['volume_data'] ?? false;
  const hasFX = selectedScenarioMeta?.files_status?.['fx_rates'] ?? false;
  const hasPlantMap = selectedScenarioMeta?.files_status?.['plant_currency'] ?? false;
  const hasCosts = selectedScenarioMeta?.files_status?.['base_costs'] ?? false;
  const hasPrices = selectedScenarioMeta?.files_status?.['base_prices'] ?? false;
  const hasVarCosts = selectedScenarioMeta?.files_status?.['base_var_costs'] ?? false;
  const hasDistCosts = selectedScenarioMeta?.files_status?.['base_dist_costs'] ?? false;

  // Handle file selection
  const handleFileSelection = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setStagedFile(file);
      setStagedDiffLogs(null);
      setStagedIsNew(null);
    }
  };

  // Dry-run upload to fetch validation and diff results
  const handleUploadClick = async () => {
    if (!stagedFile || !selectedScenario) return;
    setStagedLoadingDiff(true);
    useAppStore.setState({ calculationError: null });

    const formData = new FormData();
    formData.append('file', stagedFile);

    try {
      const res = await fetch(`/api/scenarios/${selectedScenario}/diff-file/${activePreviewTab}`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errDetail = await res.json();
        throw new Error(errDetail.detail || 'Validation/Diff check failed');
      }

      const result = await res.json();
      setStagedDiffLogs(result.diff);
      setStagedIsNew(result.is_new);
      setVolumeDeltaByMaterial(result.volume_delta_by_material ?? null);
      setPriceDeltaByMaterial(result.price_delta_by_material ?? null);
    } catch (err: any) {
      useAppStore.setState({ calculationError: err.message });
      alert(err.message);
    } finally {
      setStagedLoadingDiff(false);
    }
  };

  // Perform actual overwrite of file after diff review
  const handleOverwriteClick = async () => {
    if (!stagedFile) return;
    try {
      await uploadScenarioFile(activePreviewTab, stagedFile);
      // Reset staging states
      setStagedFile(null);
      setStagedDiffLogs(null);
      setStagedIsNew(null);
      setVolumeDeltaByMaterial(null);
      setPriceDeltaByMaterial(null);
    } catch (err) {
      console.error(err);
    }
  };

  // Submit override helper
  const handleAddOverride = () => {
    if (!ovMat || !ovCust || !ovShip || !ovDate || !ovPrice) {
      alert('Please fill out all fields.');
      return;
    }
    const newOverride: Override = {
      'Material ID': ovMat.trim(),
      'Sold to ID': ovCust.trim(),
      'Ship to ID': ovShip.trim(),
      Date: ovDate.trim(),
      Price: parseFloat(ovPrice),
    };
    addOverride(newOverride);
    // Clear price field
    setOvPrice('');
  };

  // Create scenario helper
  const handleCreateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newScenName) return;
    try {
      await createScenario(newScenName, newScenClone || null, newScenDesc);
      setNewScenName('');
      setNewScenDesc('');
      setNewScenClone('');
      setActiveWorkspaceTab('calculations');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <FluentProvider theme={themeMode === 'dark' ? webDarkTheme : webLightTheme}>
      <div className={styles.root}>
        {/* Left Sidebar */}
        <aside className={styles.sidebar}>
          <div className={styles.sidebarSection}>
            <div className={styles.sidebarTitle}>Active Scenario</div>
            {loadingScenarios ? (
              <Spinner size="tiny" label="Loading..." />
            ) : (
              <Select
                value={selectedScenario || ''}
                onChange={(e) => selectScenario(e.target.value)}
                style={{ width: '100%' }}
              >
                {scenarios.map((s) => (
                  <option key={s.name} value={s.name}>
                    {s.name}
                  </option>
                ))}
              </Select>
            )}
            {selectedScenarioMeta && (
              <Text size={200} style={{ color: tokensAny.colorNeutralText3, fontStyle: 'italic' }}>
                {selectedScenarioMeta.description || 'No description provided.'}
              </Text>
            )}
            <Button
              icon={<SaveRegular />}
              appearance="primary"
              disabled={loadingCalculation || !selectedScenario}
              onClick={saveScenario}
              style={{ marginTop: '8px' }}
            >
              Save Active Scenario
            </Button>
          </div>

          <div className={styles.sidebarSection}>
            <div className={styles.sidebarTitle}>Completeness Check</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div className={styles.checklistRow}>
                {hasVolume ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>Volumes Ingested</span>
              </div>
              <div className={styles.checklistRow}>
                {hasPrices ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>Base Prices Configuration</span>
              </div>
              <div className={styles.checklistRow}>
                {hasCosts ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>RM Costs Configuration</span>
              </div>
              <div className={styles.checklistRow}>
                {hasVarCosts ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>Var Costs Configuration</span>
              </div>
              <div className={styles.checklistRow}>
                {hasDistCosts ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>Dist Costs Configuration</span>
              </div>
              <div className={styles.checklistRow}>
                {hasFX ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>Exchange Rates Ingested</span>
              </div>
              <div className={styles.checklistRow}>
                {hasPlantMap ? (
                  <CheckmarkCircleRegular className={styles.greenText} />
                ) : (
                  <WarningRegular className={styles.redText} />
                )}
                <span>Plant Currencies Ingested</span>
              </div>
            </div>
          </div>

          {/* Create New Scenario Form */}
          <form className={styles.sidebarSection} onSubmit={handleCreateScenario}>
            <div className={styles.sidebarTitle}>New Scenario</div>
            <Input
              placeholder="Scenario Name (e.g. Price_Up_10)"
              value={newScenName}
              onChange={(e) => setNewScenName(e.target.value)}
              required
              style={{ width: '100%' }}
            />
            <Input
              placeholder="Description/Notes"
              value={newScenDesc}
              onChange={(e) => setNewScenDesc(e.target.value)}
              style={{ width: '100%' }}
            />
            <Select
              value={newScenClone}
              onChange={(e) => setNewScenClone(e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="">Clone From (None)</option>
              {scenarios.map((s) => (
                <option key={s.name} value={s.name}>
                  Clone: {s.name}
                </option>
              ))}
            </Select>
            <Button type="submit" icon={<AddRegular />} appearance="secondary" style={{ width: '100%' }}>
              Create Scenario
            </Button>
          </form>

          {/* Change Log */}
          {selectedScenarioMeta && selectedScenarioMeta.change_log && (
            <div className={styles.sidebarSection}>
              <div className={styles.sidebarTitle}>Scenario Change Log</div>
              <div className={styles.changeLogContainer}>
                {selectedScenarioMeta.change_log.map((log, i) => (
                  <div key={i} style={{ marginBottom: '6px' }}>
                    • {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Right Workspace Area */}
        <main className={styles.workspace}>
          <header className={styles.header}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '48px', height: '48px', flexShrink: 0 }}>
                <img src="/icon.png" alt="Financial Planner Studio Icon" style={{ width: '100%', height: '100%', objectFit: 'contain', borderRadius: '10px' }} />
              </div>
              <div className={styles.titleArea}>
                <h1 className={styles.mainTitle} style={{ margin: 0 }}>Financial Planner Studio</h1>
                <span className={styles.subTitle}>
                  Fluent 2 planning interface for corporate volume-to-margin scenario modeling.
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                icon={themeMode === 'dark' ? <WeatherSunnyRegular /> : <WeatherMoonRegular />}
                onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
              >
                {themeMode === 'dark' ? 'Light Mode' : 'Dark Mode'}
              </Button>
              <Button
                icon={<ArrowSyncRegular />}
                onClick={() => selectedScenario && selectScenario(selectedScenario)}
              >
                Reload
              </Button>
              <Button
                icon={<DualScreenHeaderRegular />}
                onClick={() => window.open(window.location.href, '_blank')}
              >
                Open in Side Window
              </Button>
            </div>
          </header>

          {/* Top Pivot Menu tabs */}
          <TabList
            selectedValue={activeWorkspaceTab}
            onTabSelect={(_, data) => setActiveWorkspaceTab(data.value as any)}
            className={styles.tabList}
          >
            <Tab value="inputs" icon={<DatabaseRegular />}>
              Assumptions Upload
            </Tab>
            <Tab value="pricing" icon={<MoneyRegular />}>
              Price Planning
            </Tab>
            <Tab value="calculations" icon={<MoneyRegular />}>
              Calculations & Results
            </Tab>
            <Tab value="comparison" icon={<BranchCompareRegular />}>
              Scenario Comparison
            </Tab>
          </TabList>

          {/* Error Banner */}
          {calculationError && (
            <div style={{ backgroundColor: 'rgba(255, 0, 0, 0.1)', border: '1px solid red', padding: '12px', borderRadius: '8px', marginBottom: '16px', color: 'red' }}>
              <strong>Calculation/Ingestion Error: </strong> {calculationError}
            </div>
          )}

          {/* Tab 1: Calculations & Results */}
          {activeWorkspaceTab === 'calculations' && (
            <div className={styles.contentArea}>
              {loadingCalculation ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                  <Spinner size="large" label="Running simulation calculations..." />
                </div>
              ) : calculatedMetrics ? (
                <>
                  <div className={styles.flexRow} style={{ marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Text size={400} weight="semibold">Simulation KPI Summary</Text>
                      <Badge color={currencyMode === 'USD' ? 'brand' : 'subtle'}>
                        {currencyMode}
                      </Badge>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <Button
                        appearance={currencyMode === 'USD' ? 'primary' : 'secondary'}
                        onClick={() => setCurrencyMode('USD')}
                      >
                        USD ($)
                      </Button>
                      <Button
                        appearance={currencyMode === 'LC' ? 'primary' : 'secondary'}
                        onClick={() => setCurrencyMode('LC')}
                      >
                        Local Currency (LC)
                      </Button>
                      <Button
                        icon={<ArrowDownloadRegular />}
                        appearance="secondary"
                        onClick={() => {
                          window.open(`/api/scenarios/${selectedScenario}/export`);
                        }}
                      >
                        Export SAC CSV
                      </Button>
                    </div>
                  </div>

                  {/* Summary Metric Cards */}
                  <div className={styles.cardGrid} style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                    <div className={styles.kpiCard}>
                      <div className={styles.kpiHighlight} />
                      <div className={styles.kpiTitle}>Total Planned Volume</div>
                      <div className={styles.kpiValue}>
                        {formatDecimal(calculatedMetrics.total_volume)}
                      </div>
                      <div className={styles.kpiUnit}>Metric Tons</div>
                    </div>

                    <div className={styles.kpiCard}>
                      <div className={styles.kpiHighlight} />
                      <div className={styles.kpiTitle}>Total Revenue</div>
                      <div className={styles.kpiValue}>
                        {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.total_revenue_usd)
                          : formatCurrencyLocal(calculatedMetrics.total_revenue_lc)}
                      </div>
                      <div className={styles.kpiUnit}>
                        Avg: {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.weighted_avg_price_usd)
                          : formatCurrencyLocal(calculatedMetrics.weighted_avg_price_lc)} / T
                      </div>
                    </div>

                    <div className={styles.kpiCard}>
                      <div className={styles.kpiHighlight} />
                      <div className={styles.kpiTitle}>Raw Material Cost</div>
                      <div className={styles.kpiValue}>
                        {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.total_rm_cost_usd)
                          : formatCurrencyLocal(calculatedMetrics.total_rm_cost_lc)}
                      </div>
                      <div className={styles.kpiUnit}>USD or LC values</div>
                    </div>

                    <div className={styles.kpiCard}>
                      <div className={styles.kpiHighlight} />
                      <div className={styles.kpiTitle}>Variable Costs</div>
                      <div className={styles.kpiValue}>
                        {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.total_var_cost_usd)
                          : formatCurrencyLocal(calculatedMetrics.total_var_cost_lc)}
                      </div>
                      <div className={styles.kpiUnit}>USD or LC values</div>
                    </div>

                    <div className={styles.kpiCard}>
                      <div className={styles.kpiHighlight} />
                      <div className={styles.kpiTitle}>Distribution Costs</div>
                      <div className={styles.kpiValue}>
                        {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.total_dist_cost_usd)
                          : formatCurrencyLocal(calculatedMetrics.total_dist_cost_lc)}
                      </div>
                      <div className={styles.kpiUnit}>USD or LC values</div>
                    </div>

                    <div className={styles.kpiCard}>
                      <div className={styles.kpiHighlight} />
                      <div className={styles.kpiTitle}>Total VCM</div>
                      <div className={styles.kpiValue}>
                        {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.total_vcm_usd)
                          : formatCurrencyLocal(calculatedMetrics.total_vcm_lc)}
                      </div>
                      <div className={styles.kpiUnit}>
                        Avg VCM: {currencyMode === 'USD'
                          ? formatCurrency(calculatedMetrics.weighted_avg_vcm_usd)
                          : formatCurrencyLocal(calculatedMetrics.weighted_avg_vcm_lc)} / T
                      </div>
                    </div>
                  </div>

                  {/* Results Tabs */}
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                    <Button appearance={activeResultsTab === 'revenue' ? 'primary' : 'secondary'} size="small" onClick={() => setActiveResultsTab('revenue')}>Revenue</Button>
                    <Button appearance={activeResultsTab === 'rm_costs' ? 'primary' : 'secondary'} size="small" onClick={() => setActiveResultsTab('rm_costs')}>RM Costs</Button>
                    <Button appearance={activeResultsTab === 'var_costs' ? 'primary' : 'secondary'} size="small" onClick={() => setActiveResultsTab('var_costs')}>Variable Costs</Button>
                    <Button appearance={activeResultsTab === 'dist_costs' ? 'primary' : 'secondary'} size="small" onClick={() => setActiveResultsTab('dist_costs')}>Dist Costs</Button>
                    <Button appearance={activeResultsTab === 'vcm' ? 'primary' : 'secondary'} size="small" onClick={() => setActiveResultsTab('vcm')}>VCM Summary</Button>
                  </div>

                  {/* Calculated Data Grid Preview */}
                  <div className={styles.flexRow} style={{ marginBottom: '8px' }}>
                    <Text size={300} weight="semibold">
                      {activeResultsTab === 'revenue' && 'Revenue Preview (First 100 rows)'}
                      {activeResultsTab === 'rm_costs' && 'Raw Material Costs Preview (First 100 rows)'}
                      {activeResultsTab === 'var_costs' && 'Variable Costs Preview (First 100 rows)'}
                      {activeResultsTab === 'dist_costs' && 'Distribution Costs Preview (First 100 rows)'}
                      {activeResultsTab === 'vcm' && 'VCM Summary Preview (First 100 rows)'}
                    </Text>
                  </div>
                  <div className={styles.tableContainer}>
                    <Table className={styles.denseTable}>
                      {activeResultsTab === 'revenue' && (
                        <>
                          <TableHeader>
                            <TableRow>
                              <TableHeaderCell>Material ID</TableHeaderCell>
                              <TableHeaderCell>Plant</TableHeaderCell>
                              <TableHeaderCell>Sold to ID</TableHeaderCell>
                              <TableHeaderCell>Ship to ID</TableHeaderCell>
                              <TableHeaderCell>Period</TableHeaderCell>
                              <TableHeaderCell>Volume (MT)</TableHeaderCell>
                              <TableHeaderCell>Revenue USD</TableHeaderCell>
                              <TableHeaderCell>Revenue LC</TableHeaderCell>
                              <TableHeaderCell>Unit Price USD</TableHeaderCell>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {calculatedPreview.map((row, i) => (
                              <TableRow key={i}>
                                <TableCell>{row['Material ID']}</TableCell>
                                <TableCell>{row['Plant']}</TableCell>
                                <TableCell>{row['Sold to ID']}</TableCell>
                                <TableCell>{row['Ship to ID']}</TableCell>
                                <TableCell>{row['Date']}</TableCell>
                                <TableCell>{formatDecimal(row['Volume'])}</TableCell>
                                <TableCell>{formatCurrency(row['Revenue_USD'])}</TableCell>
                                <TableCell>{formatCurrencyLocal(row['Revenue_LC'])}</TableCell>
                                <TableCell>{formatCurrency(row['Price_USD'])}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </>
                      )}
                      {activeResultsTab === 'rm_costs' && (
                        <>
                          <TableHeader>
                            <TableRow>
                              <TableHeaderCell>Material ID</TableHeaderCell>
                              <TableHeaderCell>Plant</TableHeaderCell>
                              <TableHeaderCell>Sold to ID</TableHeaderCell>
                              <TableHeaderCell>Period</TableHeaderCell>
                              <TableHeaderCell>Volume (MT)</TableHeaderCell>
                              <TableHeaderCell>RM Cost USD</TableHeaderCell>
                              <TableHeaderCell>RM Cost LC</TableHeaderCell>
                              <TableHeaderCell>Unit RM Cost USD</TableHeaderCell>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {calculatedPreview.map((row, i) => (
                              <TableRow key={i}>
                                <TableCell>{row['Material ID']}</TableCell>
                                <TableCell>{row['Plant']}</TableCell>
                                <TableCell>{row['Sold to ID']}</TableCell>
                                <TableCell>{row['Date']}</TableCell>
                                <TableCell>{formatDecimal(row['Volume'])}</TableCell>
                                <TableCell>{formatCurrency(row['Total_RM_Cost_USD'])}</TableCell>
                                <TableCell>{formatCurrencyLocal(row['Total_RM_Cost_LC'])}</TableCell>
                                <TableCell>{formatCurrency(row['RM_Cost_USD'])}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </>
                      )}
                      {activeResultsTab === 'var_costs' && (
                        <>
                          <TableHeader>
                            <TableRow>
                              <TableHeaderCell>Material ID</TableHeaderCell>
                              <TableHeaderCell>Plant</TableHeaderCell>
                              <TableHeaderCell>Sold to ID</TableHeaderCell>
                              <TableHeaderCell>Period</TableHeaderCell>
                              <TableHeaderCell>Volume (MT)</TableHeaderCell>
                              <TableHeaderCell>Var Cost USD</TableHeaderCell>
                              <TableHeaderCell>Var Cost LC</TableHeaderCell>
                              <TableHeaderCell>Unit Var Cost USD</TableHeaderCell>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {calculatedPreview.map((row, i) => (
                              <TableRow key={i}>
                                <TableCell>{row['Material ID']}</TableCell>
                                <TableCell>{row['Plant']}</TableCell>
                                <TableCell>{row['Sold to ID']}</TableCell>
                                <TableCell>{row['Date']}</TableCell>
                                <TableCell>{formatDecimal(row['Volume'])}</TableCell>
                                <TableCell>{formatCurrency(row['Total_Variable_Cost_USD'])}</TableCell>
                                <TableCell>{formatCurrencyLocal(row['Total_Variable_Cost_LC'])}</TableCell>
                                <TableCell>{formatCurrency(row['Var_Cost_USD'])}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </>
                      )}
                      {activeResultsTab === 'dist_costs' && (
                        <>
                          <TableHeader>
                            <TableRow>
                              <TableHeaderCell>Material ID</TableHeaderCell>
                              <TableHeaderCell>Plant</TableHeaderCell>
                              <TableHeaderCell>Ship to ID</TableHeaderCell>
                              <TableHeaderCell>Period</TableHeaderCell>
                              <TableHeaderCell>Volume (MT)</TableHeaderCell>
                              <TableHeaderCell>Dist Cost USD</TableHeaderCell>
                              <TableHeaderCell>Dist Cost LC</TableHeaderCell>
                              <TableHeaderCell>Unit Dist Cost USD</TableHeaderCell>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {calculatedPreview.map((row, i) => (
                              <TableRow key={i}>
                                <TableCell>{row['Material ID']}</TableCell>
                                <TableCell>{row['Plant']}</TableCell>
                                <TableCell>{row['Ship to ID']}</TableCell>
                                <TableCell>{row['Date']}</TableCell>
                                <TableCell>{formatDecimal(row['Volume'])}</TableCell>
                                <TableCell>{formatCurrency(row['Total_Distribution_Cost_USD'])}</TableCell>
                                <TableCell>{formatCurrencyLocal(row['Total_Distribution_Cost_LC'])}</TableCell>
                                <TableCell>{formatCurrency(row['Dist_Cost_USD'])}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </>
                      )}
                      {activeResultsTab === 'vcm' && (
                        <>
                          <TableHeader>
                            <TableRow>
                              <TableHeaderCell>Material ID</TableHeaderCell>
                              <TableHeaderCell>Plant</TableHeaderCell>
                              <TableHeaderCell>Sold to ID</TableHeaderCell>
                              <TableHeaderCell>Period</TableHeaderCell>
                              <TableHeaderCell>Volume (MT)</TableHeaderCell>
                              <TableHeaderCell>VCM USD</TableHeaderCell>
                              <TableHeaderCell>VCM LC</TableHeaderCell>
                              <TableHeaderCell>Unit VCM USD</TableHeaderCell>
                              <TableHeaderCell>Unit VCM LC</TableHeaderCell>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {calculatedPreview.map((row, i) => (
                              <TableRow key={i}>
                                <TableCell>{row['Material ID']}</TableCell>
                                <TableCell>{row['Plant']}</TableCell>
                                <TableCell>{row['Sold to ID']}</TableCell>
                                <TableCell>{row['Date']}</TableCell>
                                <TableCell>{formatDecimal(row['Volume'])}</TableCell>
                                <TableCell>{formatCurrency(row['VCM_USD'])}</TableCell>
                                <TableCell>{formatCurrencyLocal(row['VCM_LC'])}</TableCell>
                                <TableCell>{formatCurrency(row['Unit_VCM_USD'])}</TableCell>
                                <TableCell>{formatCurrencyLocal(row['Unit_VCM_LC'])}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </>
                      )}
                    </Table>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Text size={300} style={{ color: tokensAny.colorNeutralText3 }}>
                    Please load volume, pricing, and cost files in the tabs below to compute metrics.
                  </Text>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Price Planning & Overrides */}
          {activeWorkspaceTab === 'pricing' && (
            <div className={styles.contentArea}>
              <div className={styles.flexRow} style={{ marginBottom: '16px' }}>
                <Text size={400} weight="semibold">Add Price Override Adjustment</Text>
              </div>

              {/* Add Overrides Form Row */}
              <div className={styles.formRow}>
                <div>
                  <Label size="small">Material ID</Label>
                  <Input value={ovMat} onChange={(e) => setOvMat(e.target.value)} placeholder="e.g. MAT-1001" style={{ width: '100%' }} />
                </div>
                <div>
                  <Label size="small">Sold to ID</Label>
                  <Input value={ovCust} onChange={(e) => setOvCust(e.target.value)} placeholder="e.g. CUST-001" style={{ width: '100%' }} />
                </div>
                <div>
                  <Label size="small">Ship to ID</Label>
                  <Input value={ovShip} onChange={(e) => setOvShip(e.target.value)} placeholder="e.g. SHIP-001-NL" style={{ width: '100%' }} />
                </div>
                <div>
                  <Label size="small">Date</Label>
                  <Input value={ovDate} onChange={(e) => setOvDate(e.target.value)} placeholder="e.g. 2026-01" style={{ width: '100%' }} />
                </div>
                <div>
                  <Label size="small">Override Price (LC)</Label>
                  <Input type="number" value={ovPrice} onChange={(e) => setOvPrice(e.target.value)} placeholder="e.g. 450.00" style={{ width: '100%' }} />
                </div>
                <Button appearance="primary" onClick={handleAddOverride} style={{ minWidth: '120px' }}>
                  Add Override
                </Button>
              </div>

              {/* Active Overrides Table */}
              <div className={styles.flexRow} style={{ marginBottom: '8px' }}>
                <Text size={300} weight="semibold">Active Scenario Overrides</Text>
                {overrides.length > 0 && (
                  <Button icon={<DeleteRegular />} appearance="secondary" onClick={clearAllOverrides}>
                    Clear All
                  </Button>
                )}
              </div>
              <div className={styles.tableContainer} style={{ marginBottom: '20px' }}>
                <Table className={styles.denseTable}>
                  <TableHeader>
                    <TableRow>
                      <TableHeaderCell>Material ID</TableHeaderCell>
                      <TableHeaderCell>Sold to ID</TableHeaderCell>
                      <TableHeaderCell>Ship to ID</TableHeaderCell>
                      <TableHeaderCell>Date</TableHeaderCell>
                      <TableHeaderCell>Override Price</TableHeaderCell>
                      <TableHeaderCell>Action</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {overrides.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} style={{ textAlign: 'center', fontStyle: 'italic', padding: '16px' }}>
                          No overrides active.
                        </TableCell>
                      </TableRow>
                    ) : (
                      overrides.map((row, i) => (
                        <TableRow key={i}>
                          <TableCell>{row['Material ID']}</TableCell>
                          <TableCell>{row['Sold to ID']}</TableCell>
                          <TableCell>{row['Ship to ID']}</TableCell>
                          <TableCell>{row['Date']}</TableCell>
                          <TableCell>{formatCurrencyLocal(row['Price'])}</TableCell>
                          <TableCell>
                            <Button
                              icon={<DeleteRegular />}
                              onClick={() => removeOverride(i)}
                              size="small"
                              appearance="subtle"
                            />
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* Tab 3: Input Ingestion Preview */}
          {activeWorkspaceTab === 'inputs' && (
            <div className={styles.contentArea}>
              <div className={styles.flexRow} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <Button appearance={activePreviewTab === 'volume_data' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('volume_data')}>Volumes</Button>
                  <Button appearance={activePreviewTab === 'base_prices' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('base_prices')}>Prices</Button>
                  <Button appearance={activePreviewTab === 'base_costs' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('base_costs')}>RM Costs</Button>
                  <Button appearance={activePreviewTab === 'base_var_costs' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('base_var_costs')}>Var Costs</Button>
                  <Button appearance={activePreviewTab === 'base_dist_costs' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('base_dist_costs')}>Dist Costs</Button>
                  <Button appearance={activePreviewTab === 'fx_rates' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('fx_rates')}>FX Rates</Button>
                  <Button appearance={activePreviewTab === 'plant_currency' ? 'primary' : 'secondary'} onClick={() => setActivePreviewTab('plant_currency')}>Plant Currencies</Button>
                </div>
              </div>
              {/* ── Top row: Upload + Diff Summary ── */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>

                {/* Upload & Replace CSV */}
                <Card style={{ padding: '16px' }}>
                  <CardHeader header={<Text weight="semibold">Upload &amp; Replace CSV</Text>} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileSelection}
                      disabled={loadingData}
                      style={{
                        padding: '6px 8px',
                        border: `1px solid ${tokensAny.colorNeutralStroke1}`,
                        borderRadius: '4px',
                        backgroundColor: tokensAny.colorNeutralBackground3,
                        color: tokensAny.colorNeutralText1,
                        fontSize: '12px',
                        cursor: 'pointer',
                        width: '100%',
                        boxSizing: 'border-box',
                      }}
                    />
                    {!stagedFile && (
                      <Text size={100} style={{ color: tokensAny.colorNeutralText3 }}>
                        Select a CSV file to inspect changes before overwriting scenario configs.
                      </Text>
                    )}
                    {stagedFile && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <Text size={200} weight="semibold" style={{ wordBreak: 'break-all' }}>
                          📄 {stagedFile.name}
                        </Text>
                        <Text size={100} style={{ color: tokensAny.colorNeutralText3 }}>
                          {(stagedFile.size / 1024).toFixed(1)} KB
                        </Text>
                        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                          {stagedDiffLogs === null ? (
                            <Button
                              appearance="primary"
                              disabled={stagedLoadingDiff || loadingData}
                              onClick={handleUploadClick}
                              style={{ flexGrow: 1 }}
                            >
                              {stagedLoadingDiff ? 'Comparing...' : 'Compare with Current'}
                            </Button>
                          ) : (
                            <Button
                              appearance="primary"
                              disabled={loadingData}
                              onClick={handleOverwriteClick}
                              style={{ flexGrow: 1, backgroundColor: stagedIsNew ? '#0f7b0f' : 'orange', borderColor: stagedIsNew ? '#0f7b0f' : 'orange', color: 'white' }}
                            >
                              {stagedIsNew ? '⬆ Upload New File' : '⚠ Overwrite File'}
                            </Button>
                          )}
                          <Button
                            appearance="secondary"
                            disabled={loadingData}
                            onClick={() => {
                              setStagedFile(null);
                              setStagedDiffLogs(null);
                              setStagedIsNew(null);
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>

                {/* Diff Summary Panel */}
                <Card style={{ padding: '16px', position: 'relative', overflow: 'hidden' }}>
                  {/* Accent bar */}
                  <div style={{
                    position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
                    background: stagedDiffLogs === null
                      ? tokensAny.colorNeutralStroke2
                      : stagedIsNew
                        ? '#0f7b0f'
                        : stagedDiffLogs.length === 0
                          ? '#0078d4'
                          : '#f7630c',
                    borderRadius: '8px 8px 0 0',
                  }} />
                  <CardHeader header={<Text weight="semibold">Diff Summary</Text>} />

                  {/* No file staged */}
                  {!stagedFile && (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 0', gap: '8px', color: tokensAny.colorNeutralText3 }}>
                      <div style={{ fontSize: '32px' }}>📊</div>
                      <Text size={200} style={{ color: tokensAny.colorNeutralText3, textAlign: 'center' }}>
                        Select and compare a file to see differences against the current scenario version.
                      </Text>
                    </div>
                  )}

                  {/* File staged, not yet compared */}
                  {stagedFile && stagedDiffLogs === null && !stagedLoadingDiff && (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 0', gap: '8px' }}>
                      <div style={{ fontSize: '32px' }}>⏳</div>
                      <Text size={200} style={{ color: tokensAny.colorNeutralText3, textAlign: 'center' }}>
                        Click <strong>Compare with Current</strong> to analyse differences.
                      </Text>
                    </div>
                  )}

                  {/* Loading */}
                  {stagedLoadingDiff && (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
                      <Spinner size="medium" label="Comparing file versions..." />
                    </div>
                  )}

                  {/* Diff results ready */}
                  {stagedDiffLogs !== null && !stagedLoadingDiff && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>

                      {/* Status badge */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {stagedIsNew ? (
                          <Badge color="success" style={{ fontSize: '12px', padding: '4px 10px' }}>🆕 New File</Badge>
                        ) : stagedDiffLogs.length === 0 ? (
                          <Badge color="brand" style={{ fontSize: '12px', padding: '4px 10px' }}>✅ Identical — No Changes</Badge>
                        ) : (
                          <Badge color="warning" style={{ fontSize: '12px', padding: '4px 10px' }}>⚠ {stagedDiffLogs.length} Change{stagedDiffLogs.length > 1 ? 's' : ''} Detected</Badge>
                        )}
                      </div>

                      {/* Change breakdown */}
                      {stagedDiffLogs.length > 0 && (
                        <div style={{
                          display: 'flex', flexDirection: 'column', gap: '6px',
                          backgroundColor: tokensAny.colorNeutralBackground3,
                          borderRadius: '6px', padding: '12px',
                          border: `1px solid ${tokensAny.colorNeutralStroke2}`,
                        }}>
                          {stagedDiffLogs.map((log, i) => {
                            const isAdded = log.includes('added');
                            const isDeleted = log.includes('deleted');
                            const icon = isAdded ? '➕' : isDeleted ? '➖' : '✏️';
                            const color = isAdded ? '#0f7b0f' : isDeleted ? '#c50f1f' : '#f7630c';
                            return (
                              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '14px' }}>{icon}</span>
                                <Text size={200} style={{ color }}>{log}</Text>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Volume Delta by Material — only for volume_data tab */}
                      {activePreviewTab === 'volume_data' && volumeDeltaByMaterial !== null && volumeDeltaByMaterial.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <Text size={100} weight="semibold" style={{ color: tokensAny.colorNeutralText2 }}>
                            📦 Volume Delta by Material (MT)
                          </Text>
                          <div style={{
                            border: `1px solid ${tokensAny.colorNeutralStroke2}`,
                            borderRadius: '6px',
                            overflow: 'hidden',
                            maxHeight: '220px',
                            overflowY: 'auto',
                          }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                              <thead>
                                <tr style={{ backgroundColor: tokensAny.colorNeutralBackground3, position: 'sticky', top: 0 }}>
                                  <th style={{ textAlign: 'left', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Material</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Base (MT)</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>New (MT)</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Δ (MT)</th>
                                </tr>
                              </thead>
                              <tbody>
                                {volumeDeltaByMaterial.map((row, i) => {
                                  const deltaColor = row.delta > 0 ? '#0f7b0f' : '#c50f1f';
                                  const deltaPrefix = row.delta > 0 ? '+' : '';
                                  return (
                                    <tr key={i} style={{ borderBottom: `1px solid ${tokensAny.colorNeutralStroke3}` }}>
                                      <td style={{ padding: '5px 10px', fontFamily: 'monospace', color: tokensAny.colorNeutralText1 }}>{row.material_id}</td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', color: tokensAny.colorNeutralText2 }}>{formatDecimal(row.base_volume)}</td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', color: tokensAny.colorNeutralText2 }}>{formatDecimal(row.new_volume)}</td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', fontWeight: 600, color: deltaColor }}>
                                        {deltaPrefix}{formatDecimal(row.delta)}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                              <tfoot>
                                {(() => {
                                  const totalBase = volumeDeltaByMaterial.reduce((s, r) => s + r.base_volume, 0);
                                  const totalNew  = volumeDeltaByMaterial.reduce((s, r) => s + r.new_volume,  0);
                                  const totalDelta = volumeDeltaByMaterial.reduce((s, r) => s + r.delta, 0);
                                  const totalDeltaColor = totalDelta > 0 ? '#0f7b0f' : totalDelta < 0 ? '#c50f1f' : tokensAny.colorNeutralText2;
                                  const totalDeltaPrefix = totalDelta > 0 ? '+' : '';
                                  return (
                                    <tr style={{
                                      borderTop: `2px solid ${tokensAny.colorNeutralStroke1}`,
                                      backgroundColor: tokensAny.colorNeutralBackground3,
                                      position: 'sticky', bottom: 0,
                                    }}>
                                      <td style={{ padding: '6px 10px', fontWeight: 700, color: tokensAny.colorNeutralText1, fontSize: '12px' }}>TOTAL</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: tokensAny.colorNeutralText1 }}>{formatDecimal(totalBase)}</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: tokensAny.colorNeutralText1 }}>{formatDecimal(totalNew)}</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: totalDeltaColor }}>
                                        {totalDeltaPrefix}{formatDecimal(totalDelta)}
                                      </td>
                                    </tr>
                                  );
                                })()}
                              </tfoot>
                            </table>
                          </div>
                        </div>
                      )}

                      {activePreviewTab === 'volume_data' && volumeDeltaByMaterial !== null && volumeDeltaByMaterial.length === 0 && !stagedIsNew && (
                        <Text size={100} style={{ color: tokensAny.colorNeutralText3, fontStyle: 'italic' }}>
                          No volume changes detected at material level.
                        </Text>
                      )}

                      {/* Price Delta by Material — only for base_prices tab */}
                      {activePreviewTab === 'base_prices' && priceDeltaByMaterial !== null && priceDeltaByMaterial.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <Text size={100} weight="semibold" style={{ color: tokensAny.colorNeutralText2 }}>
                            💰 Avg Price Change by Material (LC / T)
                          </Text>
                          <div style={{
                            border: `1px solid ${tokensAny.colorNeutralStroke2}`,
                            borderRadius: '6px',
                            overflow: 'hidden',
                            maxHeight: '240px',
                            overflowY: 'auto',
                          }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                              <thead>
                                <tr style={{ backgroundColor: tokensAny.colorNeutralBackground3, position: 'sticky', top: 0 }}>
                                  <th style={{ textAlign: 'left',  padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Material</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Base Avg</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>New Avg</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Δ Price</th>
                                  <th style={{ textAlign: 'right', padding: '6px 10px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}`, fontWeight: 600, color: tokensAny.colorNeutralText2 }}>Δ %</th>
                                </tr>
                              </thead>
                              <tbody>
                                {priceDeltaByMaterial.map((row, i) => {
                                  const deltaColor = row.delta > 0 ? '#0f7b0f' : '#c50f1f';
                                  const deltaPrefix = row.delta > 0 ? '+' : '';
                                  const pctDisplay = row.pct_change !== null
                                    ? `${row.pct_change > 0 ? '+' : ''}${row.pct_change.toFixed(1)}%`
                                    : '—';
                                  return (
                                    <tr key={i} style={{ borderBottom: `1px solid ${tokensAny.colorNeutralStroke3}` }}>
                                      <td style={{ padding: '5px 10px', fontFamily: 'monospace', color: tokensAny.colorNeutralText1 }}>{row.material_id}</td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', color: tokensAny.colorNeutralText2 }}>{formatDecimal(row.base_avg_price)}</td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', color: tokensAny.colorNeutralText2 }}>{formatDecimal(row.new_avg_price)}</td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', fontWeight: 600, color: deltaColor }}>
                                        {deltaPrefix}{formatDecimal(row.delta)}
                                      </td>
                                      <td style={{ padding: '5px 10px', textAlign: 'right', fontWeight: 600, color: deltaColor }}>{pctDisplay}</td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                              <tfoot>
                                {(() => {
                                  const n = priceDeltaByMaterial.length;
                                  const avgBase  = priceDeltaByMaterial.reduce((s, r) => s + r.base_avg_price, 0) / n;
                                  const avgNew   = priceDeltaByMaterial.reduce((s, r) => s + r.new_avg_price, 0) / n;
                                  const avgDelta = avgNew - avgBase;
                                  const avgPct   = avgBase !== 0 ? avgDelta / avgBase * 100 : null;
                                  const totalDeltaColor = avgDelta > 0 ? '#0f7b0f' : avgDelta < 0 ? '#c50f1f' : tokensAny.colorNeutralText2;
                                  const prefix = avgDelta > 0 ? '+' : '';
                                  return (
                                    <tr style={{
                                      borderTop: `2px solid ${tokensAny.colorNeutralStroke1}`,
                                      backgroundColor: tokensAny.colorNeutralBackground3,
                                      position: 'sticky', bottom: 0,
                                    }}>
                                      <td style={{ padding: '6px 10px', fontWeight: 700, color: tokensAny.colorNeutralText1, fontSize: '12px' }}>AVG ({n} mat.)</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: tokensAny.colorNeutralText1 }}>{formatDecimal(avgBase)}</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: tokensAny.colorNeutralText1 }}>{formatDecimal(avgNew)}</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: totalDeltaColor }}>{prefix}{formatDecimal(avgDelta)}</td>
                                      <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: totalDeltaColor }}>
                                        {avgPct !== null ? `${avgPct > 0 ? '+' : ''}${avgPct.toFixed(1)}%` : '—'}
                                      </td>
                                    </tr>
                                  );
                                })()}
                              </tfoot>
                            </table>
                          </div>
                        </div>
                      )}

                      {activePreviewTab === 'base_prices' && priceDeltaByMaterial !== null && priceDeltaByMaterial.length === 0 && !stagedIsNew && (
                        <Text size={100} style={{ color: tokensAny.colorNeutralText3, fontStyle: 'italic' }}>
                          No average price changes detected at material level.
                        </Text>
                      )}

                      {/* No changes message */}
                      {!stagedIsNew && stagedDiffLogs.length === 0 && (
                        <Text size={200} style={{ color: tokensAny.colorNeutralText3, fontStyle: 'italic' }}>
                          The staged file is identical to the current scenario file. No changes will be applied.
                        </Text>
                      )}

                      {/* New file message */}
                      {stagedIsNew && (
                        <Text size={200} style={{ color: tokensAny.colorNeutralText3, fontStyle: 'italic' }}>
                          No existing file found in this scenario. Uploading will create a new configuration file.
                        </Text>
                      )}

                      {/* Metadata row */}
                      <div style={{
                        display: 'flex', gap: '16px', flexWrap: 'wrap',
                        borderTop: `1px solid ${tokensAny.colorNeutralStroke3}`,
                        paddingTop: '8px', marginTop: '4px',
                      }}>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <Text size={100} style={{ color: tokensAny.colorNeutralText3 }}>File</Text>
                          <Text size={200} weight="semibold" style={{ wordBreak: 'break-all' }}>{stagedFile?.name ?? '—'}</Text>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <Text size={100} style={{ color: tokensAny.colorNeutralText3 }}>Size</Text>
                          <Text size={200} weight="semibold">{stagedFile ? `${(stagedFile.size / 1024).toFixed(1)} KB` : '—'}</Text>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <Text size={100} style={{ color: tokensAny.colorNeutralText3 }}>Type</Text>
                          <Text size={200} weight="semibold">{activePreviewTab.replace(/_/g, ' ')}</Text>
                        </div>
                      </div>
                    </div>
                  )}
                </Card>
              </div>

              {/* ── Full-width preview table ── */}
              <Card style={{ padding: '0' }}>
                <div style={{ padding: '12px 16px', borderBottom: `1px solid ${tokensAny.colorNeutralStroke2}` }}>
                  <Text weight="semibold" size={300}>
                    Current File Preview — {activePreviewTab.replace(/_/g, ' ')} (first 100 rows)
                  </Text>
                </div>
                <div className={styles.tableContainer}>
                  {loadingData ? (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                      <Spinner label="Loading file preview..." />
                    </div>
                  ) : (
                    <Table className={styles.denseTable}>
                      <TableHeader>
                        <TableRow>
                          {previewData[activePreviewTab] && previewData[activePreviewTab].length > 0 &&
                            Object.keys(previewData[activePreviewTab][0]).map((col) => (
                              <TableHeaderCell key={col}>{col}</TableHeaderCell>
                            ))
                          }
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {!previewData[activePreviewTab] || previewData[activePreviewTab].length === 0 ? (
                          <TableRow>
                            <TableCell style={{ fontStyle: 'italic', textAlign: 'center', padding: '16px' }}>
                              No preview data loaded.
                            </TableCell>
                          </TableRow>
                        ) : (
                          previewData[activePreviewTab].slice(0, 100).map((row, i) => (
                            <TableRow key={i}>
                              {Object.values(row).map((val: any, idx) => (
                                <TableCell key={idx}>
                                  {typeof val === 'number' ? formatDecimal(val) : String(val)}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Tab 4: Scenario Comparison */}
          {activeWorkspaceTab === 'comparison' && (
            <div className={styles.contentArea}>
              {/* Compare Selectors */}
              <div className={styles.formRow}>
                <div>
                  <Label size="small">Scenario A (Base)</Label>
                  <Select value={compareScenarioA} onChange={(e) => setCompareScenarioA(e.target.value)} style={{ width: '100%' }}>
                    <option value="">Select Scenario A</option>
                    {scenarios.map((s) => (
                      <option key={s.name} value={s.name}>{s.name}</option>
                    ))}
                  </Select>
                </div>
                <div>
                  <Label size="small">Scenario B (Comparison)</Label>
                  <Select value={compareScenarioB} onChange={(e) => setCompareScenarioB(e.target.value)} style={{ width: '100%' }}>
                    <option value="">Select Scenario B</option>
                    {scenarios.map((s) => (
                      <option key={s.name} value={s.name}>{s.name}</option>
                    ))}
                  </Select>
                </div>
                <Button appearance="primary" icon={<BranchCompareRegular />} disabled={loadingCompare} onClick={runComparison}>
                  Calculate Variance
                </Button>
              </div>

              {compareError && (
                <div style={{ backgroundColor: 'rgba(255, 0, 0, 0.1)', border: '1px solid red', padding: '12px', borderRadius: '8px', marginBottom: '16px', color: 'red' }}>
                  {compareError}
                </div>
              )}

              {loadingCompare ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                  <Spinner label="Performing scenario comparison and delta variance analysis..." />
                </div>
              ) : compareResult ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <Text size={400} weight="semibold">Profitability Delta Analysis (USD)</Text>
                  
                  {/* KPI Deltas side-by-side */}
                  <div className={styles.cardGrid}>
                    <Card style={{ padding: '16px' }}>
                      <Text size={200} style={{ color: tokensAny.colorNeutralText3 }}>Volume Delta</Text>
                      <Text size={500} weight="bold" style={{ color: compareResult.absolute_diff.total_volume >= 0 ? 'green' : 'red' }}>
                        {formatDecimal(compareResult.absolute_diff.total_volume)} T
                      </Text>
                      <Text size={100}>{compareResult.percentage_diff.total_volume}</Text>
                    </Card>

                    <Card style={{ padding: '16px' }}>
                      <Text size={200} style={{ color: tokensAny.colorNeutralText3 }}>Revenue Delta</Text>
                      <Text size={500} weight="bold" style={{ color: compareResult.absolute_diff.total_revenue_usd >= 0 ? 'green' : 'red' }}>
                        {formatCurrency(compareResult.absolute_diff.total_revenue_usd)}
                      </Text>
                      <Text size={100}>{compareResult.percentage_diff.total_revenue_usd}</Text>
                    </Card>

                    <Card style={{ padding: '16px' }}>
                      <Text size={200} style={{ color: tokensAny.colorNeutralText3 }}>VCM Profitability Delta</Text>
                      <Text size={500} weight="bold" style={{ color: compareResult.absolute_diff.total_vcm_usd >= 0 ? 'green' : 'red' }}>
                        {formatCurrency(compareResult.absolute_diff.total_vcm_usd)}
                      </Text>
                      <Text size={100}>{compareResult.percentage_diff.total_vcm_usd}</Text>
                    </Card>
                  </div>

                  {/* Change Log between the two */}
                  {compareResult.change_log && compareResult.change_log.length > 0 && (
                    <Card style={{ padding: '16px' }}>
                      <CardHeader header={<Text weight="semibold">Scenario Input Audit Diff Log</Text>} />
                      <div className={styles.changeLogContainer} style={{ maxHeight: '120px', marginTop: '10px' }}>
                        {compareResult.change_log.map((log, i) => (
                          <div key={i} style={{ marginBottom: '4px' }}>
                            • {log}
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                  {/* Plant variance table */}
                  <Card style={{ padding: '16px' }}>
                    <CardHeader header={<Text weight="semibold">VCM Variance Analysis by Manufacturing Plant</Text>} />
                    <div className={styles.tableContainer} style={{ marginTop: '12px' }}>
                      <Table className={styles.denseTable}>
                        <TableHeader>
                          <TableRow>
                            <TableHeaderCell>Plant</TableHeaderCell>
                            <TableHeaderCell>Volume (A)</TableHeaderCell>
                            <TableHeaderCell>Volume (B)</TableHeaderCell>
                            <TableHeaderCell>Volume Delta</TableHeaderCell>
                            <TableHeaderCell>VCM (A)</TableHeaderCell>
                            <TableHeaderCell>VCM (B)</TableHeaderCell>
                            <TableHeaderCell>VCM Delta</TableHeaderCell>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {compareResult.vcm_variance_by_plant.map((row, i) => (
                            <TableRow key={i}>
                              <TableCell>{row.Plant}</TableCell>
                              <TableCell>{formatDecimal(row.Volume_A)}</TableCell>
                              <TableCell>{formatDecimal(row.Volume_B)}</TableCell>
                              <TableCell style={{ color: row['Volume Delta'] >= 0 ? 'green' : 'red' }}>
                                {formatDecimal(row['Volume Delta'])}
                              </TableCell>
                              <TableCell>{formatCurrency(row.VCM_USD_A)}</TableCell>
                              <TableCell>{formatCurrency(row.VCM_USD_B)}</TableCell>
                              <TableCell style={{ color: row['VCM Delta'] >= 0 ? 'green' : 'red' }}>
                                {formatCurrency(row['VCM Delta'])}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </Card>

                  {/* Material variance table */}
                  <Card style={{ padding: '16px' }}>
                    <CardHeader header={<Text weight="semibold">VCM Variance Analysis by Product Material</Text>} />
                    <div className={styles.tableContainer} style={{ marginTop: '12px' }}>
                      <Table className={styles.denseTable}>
                        <TableHeader>
                          <TableRow>
                            <TableHeaderCell>Material</TableHeaderCell>
                            <TableHeaderCell>Material ID</TableHeaderCell>
                            <TableHeaderCell>Volume (A)</TableHeaderCell>
                            <TableHeaderCell>Volume (B)</TableHeaderCell>
                            <TableHeaderCell>Volume Delta</TableHeaderCell>
                            <TableHeaderCell>VCM (A)</TableHeaderCell>
                            <TableHeaderCell>VCM (B)</TableHeaderCell>
                            <TableHeaderCell>VCM Delta</TableHeaderCell>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {compareResult.vcm_variance_by_material.map((row, i) => (
                            <TableRow key={i}>
                              <TableCell>{row.Material}</TableCell>
                              <TableCell>{row['Material ID']}</TableCell>
                              <TableCell>{formatDecimal(row.Volume_A)}</TableCell>
                              <TableCell>{formatDecimal(row.Volume_B)}</TableCell>
                              <TableCell style={{ color: row['Volume Delta'] >= 0 ? 'green' : 'red' }}>
                                {formatDecimal(row['Volume Delta'])}
                              </TableCell>
                              <TableCell>{formatCurrency(row.VCM_USD_A)}</TableCell>
                              <TableCell>{formatCurrency(row.VCM_USD_B)}</TableCell>
                              <TableCell style={{ color: row['VCM Delta'] >= 0 ? 'green' : 'red' }}>
                                {formatCurrency(row['VCM Delta'])}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </Card>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Text size={300} style={{ color: tokensAny.colorNeutralText3 }}>
                    Please select Scenario A and Scenario B above to calculate deltas.
                  </Text>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </FluentProvider>
  );
}

export default App;
