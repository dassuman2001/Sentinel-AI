import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import { 
  Shield, 
  Key, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  User, 
  LogOut, 
  Plus, 
  Search, 
  RefreshCw, 
  FileText, 
  X, 
  Moon, 
  Sun, 
  Lock, 
  Mail, 
  Layers, 
  Sparkles
} from 'lucide-react';

// Setup base URL for axios
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api/v1';
axios.defaults.baseURL = API_BASE_URL;

// Add request interceptor to attach JWT token
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default function App() {
  // Theme state (Dark Mode by default)
  const [darkMode, setDarkMode] = useState<boolean>(true);

  // Authentication State
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [user, setUser] = useState<any>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLogin, setIsLogin] = useState<boolean>(true);
  const [authLoading, setAuthLoading] = useState<boolean>(false);

  // Auth fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  // Active navigation tab
  const [activeTab, setActiveTab] = useState<string>('dashboard');

  // Application Data States
  const [repos, setRepos] = useState<any[]>([]);
  const [scans, setScans] = useState<any[]>([]);
  const [secrets, setSecrets] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any | null>(null);

  // Table selections, searching, filtering
  const [selectedSecret, setSelectedSecret] = useState<any | null>(null);
  const [secretFilter, setSecretFilter] = useState<string>('all');
  const [secretSearch, setSecretSearch] = useState<string>('');

  // AI Security Engine states
  const [aiAnalysis, setAiAnalysis] = useState<any | null>(null);
  const [loadingAi, setLoadingAi] = useState<boolean>(false);
  const [aiChatHistory, setAiChatHistory] = useState<Array<{ role: 'user' | 'assistant', text: string }>>([]);
  const [aiChatInput, setAiChatInput] = useState<string>('');
  const [sendingAiChat, setSendingAiChat] = useState<boolean>(false);
  
  // Register repo fields
  const [isRegisteringRepo, setIsRegisteringRepo] = useState(false);
  const [repoName, setRepoName] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [repoBranch, setRepoBranch] = useState('main');
  const [repoProvider, setRepoProvider] = useState('github');
  const [repoSchedule, setRepoSchedule] = useState('manual');
  const [repoAccessToken, setRepoAccessToken] = useState('');
  
  // Scan branch selection states
  const [isScanBranchModalOpen, setIsScanBranchModalOpen] = useState(false);
  const [scanBranchModalRepo, setScanBranchModalRepo] = useState<any | null>(null);
  const [remoteBranches, setRemoteBranches] = useState<string[]>([]);
  const [loadingRemoteBranches, setLoadingRemoteBranches] = useState(false);
  const [selectedScanBranch, setSelectedScanBranch] = useState('main');

  // Loaders
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [loadingScans, setLoadingScans] = useState(false);
  const [loadingSecrets, setLoadingSecrets] = useState(false);
  const [loadingAudits, setLoadingAudits] = useState(false);
  const [scanningRepoId, setScanningRepoId] = useState<number | null>(null);

  const getPlaceholderByProvider = () => {
    switch (repoProvider) {
      case 'github':
        return 'https://github.com/user/repo.git';
      case 'gitlab':
        return 'https://gitlab.com/user/repo.git';
      case 'bitbucket':
        return 'https://bitbucket.org/user/repo.git';
      case 'azure':
        return 'https://dev.azure.com/org/repo.git';
      case 'local':
        return '/path/to/local/repo';
      default:
        return 'https://example.com/user/repo.git';
    }
  };

  // Apply dark mode CSS class
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }, [darkMode]);

  // Fetch initial profile when token is set
  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setUser(null);
    }
  }, [token]);

  // Once user profile is loaded, fetch all data
  useEffect(() => {
    if (user) {
      refreshAllData();
    }
  }, [user]);

  // Load AI Analysis when a secret is selected
  useEffect(() => {
    if (!selectedSecret) {
      setAiAnalysis(null);
      setAiChatHistory([]);
      return;
    }
    
    const fetchAiAnalysis = async () => {
      setLoadingAi(true);
      try {
        const res = await axios.get(`/ai/explain/${selectedSecret.id}`);
        setAiAnalysis(res.data);
      } catch (err) {
        console.error('Error fetching AI analysis:', err);
      } finally {
        setLoadingAi(false);
      }
    };
    
    fetchAiAnalysis();
  }, [selectedSecret]);

  const handleSendAiQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSecret || !aiChatInput.trim()) return;
    
    const userMsg = aiChatInput.trim();
    setAiChatInput('');
    setAiChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setSendingAiChat(true);
    
    try {
      const res = await axios.post(`/ai/chat/${selectedSecret.id}`, { question: userMsg });
      setAiChatHistory(prev => [...prev, { role: 'assistant', text: res.data.answer }]);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || 'Error getting response from AI Assistant.';
      setAiChatHistory(prev => [...prev, { role: 'assistant', text: errMsg }]);
    } finally {
      setSendingAiChat(false);
    }
  };

  // Initialize Google Sign-In button
  useEffect(() => {
    if (!token) {
      // Define global callback handler
      (window as any).handleGoogleCredentialResponse = async (response: any) => {
        setAuthLoading(true);
        setAuthError(null);
        try {
          const res = await axios.post('/auth/google-login', { 
            credential: response.credential,
            is_signup: !isLogin
          });
          const accessToken = res.data.access_token;
          localStorage.setItem('access_token', accessToken);
          setToken(accessToken);
        } catch (err: any) {
          const detail = err.response?.data?.detail || 'Google sign-in failed.';
          setAuthError(detail);
          if (detail.includes("already exists")) {
            setIsLogin(true);
          } else if (detail.includes("Please sign up first")) {
            setIsLogin(false);
          }
        } finally {
          setAuthLoading(false);
        }
      };

      // If google script is loaded, initialize and render
      const interval = setInterval(() => {
        if ((window as any).google?.accounts?.id) {
          clearInterval(interval);
          (window as any).google.accounts.id.initialize({
            client_id: "1013404657869-a536nha6mudlr2u2cupfrt7klsmnaaud.apps.googleusercontent.com",
            callback: (window as any).handleGoogleCredentialResponse,
            context: isLogin ? "signin" : "signup",
            ux_mode: "popup",
            auto_select: false,
            itp_support: true
          });
          const buttonElement = document.getElementById("google-signin-btn-container");
          if (buttonElement) {
            (window as any).google.accounts.id.renderButton(buttonElement, {
              type: "standard",
              shape: "rectangular",
              theme: "outline",
              text: isLogin ? "signin_with" : "signup_with",
              size: "large",
              logo_alignment: "left",
              width: buttonElement.clientWidth || 320
            });
          }
        }
      }, 100);

      return () => {
        clearInterval(interval);
        delete (window as any).handleGoogleCredentialResponse;
      };
    }
  }, [token, isLogin]);

  const refreshAllData = () => {
    fetchDashboardAnalytics();
    fetchRepositories();
    fetchScans();
    fetchSecrets();
    fetchAuditLogs();
  };

  // ------------------ API METHODS ------------------

  const fetchProfile = async () => {
    try {
      const res = await axios.get('/users/me');
      setUser(res.data);
    } catch (err: any) {
      handleLogout();
    }
  };



  const fetchDashboardAnalytics = async () => {
    try {
      // Load severity counts
      const resSev = await axios.get('/dashboard/charts/secrets-by-severity');
      // Load type counts
      const resType = await axios.get('/dashboard/charts/secrets-by-type');
      
      setAnalytics({
        severity: resSev.data,
        type: resType.data
      });
    } catch (err) {
      console.error('Error loading dashboard analytics:', err);
    }
  };

  const fetchRepositories = async () => {
    setLoadingRepos(true);
    try {
      const res = await axios.get('/repositories/');
      setRepos(res.data);
    } catch (err) {
      console.error('Error loading repositories:', err);
    } finally {
      setLoadingRepos(false);
    }
  };

  const fetchScans = async () => {
    setLoadingScans(true);
    try {
      const res = await axios.get('/scans/');
      setScans(res.data);
    } catch (err) {
      console.error('Error loading scans:', err);
    } finally {
      setLoadingScans(false);
    }
  };

  const fetchSecrets = async () => {
    setLoadingSecrets(true);
    try {
      const res = await axios.get('/secrets/');
      setSecrets(res.data);
    } catch (err) {
      console.error('Error loading secrets:', err);
    } finally {
      setLoadingSecrets(false);
    }
  };

  const fetchAuditLogs = async () => {
    setLoadingAudits(true);
    try {
      const res = await axios.get('/audit-logs/');
      setAuditLogs(res.data);
    } catch (err) {
      console.error('Error loading audit logs:', err);
    } finally {
      setLoadingAudits(false);
    }
  };

  const handleRegisterRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoName || !repoUrl) return;
    try {
      const res = await axios.post('/repositories/', {
        name: repoName,
        clone_url: repoUrl,
        provider: repoProvider,
        access_token: repoAccessToken,
        scan_schedule: repoSchedule
      });
      setRepos([...repos, res.data]);
      setIsRegisteringRepo(false);
      setRepoName('');
      setRepoUrl('');
      setRepoAccessToken('');
      setRepoSchedule('manual');
      setRepoProvider('github');
      // Refresh list
      fetchRepositories();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error registering repository');
    }
  };

  const openScanBranchModal = async (repo: any) => {
    setScanBranchModalRepo(repo);
    setIsScanBranchModalOpen(true);
    setLoadingRemoteBranches(true);
    setSelectedScanBranch('main');
    try {
      const res = await axios.get(`/repositories/${repo.id}/branches/remote`);
      setRemoteBranches(res.data.branches);
      if (res.data.branches && res.data.branches.length > 0) {
        setSelectedScanBranch(res.data.branches[0]);
      }
    } catch (err) {
      console.error("Error fetching remote branches:", err);
      setRemoteBranches(['main', 'master']);
      setSelectedScanBranch('main');
    } finally {
      setLoadingRemoteBranches(false);
    }
  };

  const handleTriggerScanWithBranch = async () => {
    if (!scanBranchModalRepo) return;
    const repoId = scanBranchModalRepo.id;
    setIsScanBranchModalOpen(false);
    setScanningRepoId(repoId);
    try {
      const res = await axios.post(`/repositories/${repoId}/scan?branch_name=${selectedScanBranch}`);
      alert(`Scan triggered successfully on branch [${selectedScanBranch}]! Scan ID: ${res.data.id}. Worker is processing in the background.`);
      
      // Start polling for scan completion
      pollScanStatus(res.data.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error triggering scan');
      setScanningRepoId(null);
    }
  };


  const pollScanStatus = (scanId: number) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`/scans/${scanId}`);
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          clearInterval(interval);
          setScanningRepoId(null);
          refreshAllData();
          alert(`Scan #${scanId} completed! Found ${res.data.secrets_found} secrets.`);
        }
      } catch (err) {
        clearInterval(interval);
        setScanningRepoId(null);
      }
    }, 3000);
  };

  const handleUpdateSecretStatus = async (secretId: number, status: string) => {
    try {
      await axios.patch(`/secrets/${secretId}/status`, { status });
      // Update local state
      setSecrets(secrets.map(s => s.id === secretId ? { ...s, status } : s));
      if (selectedSecret && selectedSecret.id === secretId) {
        setSelectedSecret({ ...selectedSecret, status });
      }
      refreshAllData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error updating status');
    }
  };

  const handleProvisionDemoData = async () => {
    try {
      // 1. Register the local mock vulnerable repo
      const repoRes = await axios.post('/repositories/', {
        name: 'Vulnerable Repo Demo',
        clone_url: '/Users/sd-mac/Documents/Sentinel AI/sample-repositories/vulnerable-repo',
        provider: 'local',
        access_token: ''
      });
      
      setRepos(prev => [...prev, repoRes.data]);
      alert('Vulnerable repository registered! Triggering immediate background scan...');
      
      // 2. Trigger scan
      setScanningRepoId(repoRes.data.id);
      const scanRes = await axios.post(`/repositories/${repoRes.data.id}/scan`);
      pollScanStatus(scanRes.data.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error provisioning demo repo');
    }
  };

  // ------------------ AUTHENTICATION METHODS ------------------

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const res = await axios.post('/auth/login', formData);
      const accessToken = res.data.access_token;
      localStorage.setItem('access_token', accessToken);
      setToken(accessToken);
    } catch (err: any) {
      setAuthError(err.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  const validatePassword = (pass: string): string | null => {
    if (pass.length < 8) {
      return "Password must be at least 8 characters long.";
    }
    if (!/[A-Z]/.test(pass)) {
      return "Password must contain at least one uppercase letter.";
    }
    if (!/[a-z]/.test(pass)) {
      return "Password must contain at least one lowercase letter.";
    }
    if (!/[0-9]/.test(pass)) {
      return "Password must contain at least one number.";
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pass)) {
      return "Password must contain at least one special character or symbol.";
    }
    return null;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    
    const pwdErr = validatePassword(password);
    if (pwdErr) {
      setAuthError(pwdErr);
      return;
    }

    setAuthLoading(true);
    try {
      await axios.post('/auth/register', {
        email,
        password,
        first_name: firstName,
        last_name: lastName
      });
      // Auto login after registration
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      const loginRes = await axios.post('/auth/login', formData);
      const accessToken = loginRes.data.access_token;
      localStorage.setItem('access_token', accessToken);
      setToken(accessToken);
    } catch (err: any) {
      setAuthError(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setAuthLoading(false);
    }
  };



  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  // ------------------ CHART OPTIONS ------------------

  const getSeverityChartOption = () => {
    if (!analytics || !analytics.severity) return {};
    const data = Object.entries(analytics.severity).map(([name, value]) => ({
      name: name.toUpperCase(),
      value
    }));

    return {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        textStyle: { color: darkMode ? '#e4e4e7' : '#09090b' }
      },
      color: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
      series: [
        {
          name: 'Severity',
          type: 'pie',
          radius: ['45%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: darkMode ? '#0c0c0f' : '#ffffff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
              color: darkMode ? '#ffffff' : '#000000'
            }
          },
          labelLine: {
            show: false
          },
          data
        }
      ]
    };
  };

  const getTypeChartOption = () => {
    if (!analytics || !analytics.type) return {};
    const entries = Object.entries(analytics.type);
    const names = entries.map(([k]) => k);
    const values = entries.map(([, v]) => v);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        top: '10%',
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: darkMode ? '#27272a' : '#e4e4e7' } },
        axisLabel: { color: darkMode ? '#a1a1aa' : '#71717a' }
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: darkMode ? '#27272a' : '#e4e4e7' } },
        axisLabel: { color: darkMode ? '#a1a1aa' : '#71717a' }
      },
      series: [
        {
          type: 'bar',
          data: values,
          itemStyle: {
            color: '#3b82f6',
            borderRadius: [0, 4, 4, 0]
          }
        }
      ]
    };
  };

  // ------------------ FRONTEND VIEWS ------------------

  if (!token) {
    // LOGIN / REGISTER SPLIT SCREEN
    return (
      <div className={`min-h-screen flex ${darkMode ? 'dark bg-[#09090b]' : 'bg-zinc-50'}`}>
        {/* Left Hand Art Banner */}
        <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-indigo-950 via-purple-900 to-zinc-950 p-12 flex-col justify-between text-white relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(139,92,246,0.15),transparent_45%)]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent,rgba(0,0,0,0.4))]" />
          
          <div className="flex items-center gap-2.5 z-10">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
              <Shield className="h-6 w-6" />
            </div>
            <span className="font-bold text-xl tracking-tight">Sentinel AI</span>
          </div>

          <div className="z-10 max-w-md">
            <h1 className="text-4xl font-extrabold tracking-tight text-white mb-4">
              Real-time Secret Leak Prevention.
            </h1>
            <p className="text-zinc-300 text-lg leading-relaxed">
              Detect, analyze, and remediate API keys, database credentials, and certificates before they become enterprise liabilities.
            </p>
          </div>

          <div className="z-10 flex gap-4 text-xs text-zinc-400">
            <span>Version 1.0.0</span>
            <span>•</span>
            <span>Enterprise Grade Developer Security</span>
          </div>
        </div>

        {/* Right Hand Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 md:p-16">
          <div className="w-full max-w-md space-y-8">
            <div className="flex justify-between items-center">
              <div className="lg:hidden flex items-center gap-2">
                <Shield className="h-6 w-6 text-emerald-500" />
                <span className="font-bold text-lg dark:text-zinc-50">Sentinel AI</span>
              </div>
              
              <button 
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 transition-colors ml-auto"
              >
                {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
            </div>

            <div className="space-y-2">
              <h2 className="text-3xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
                {isLogin ? 'Sign in to Sentinel' : 'Create an Account'}
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                {isLogin ? 'Use email credentials or OAuth providers.' : 'Provide details below to create your developer profile.'}
              </p>
            </div>

            {authError && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 dark:bg-rose-950/20 dark:border-rose-800/30 rounded-lg text-rose-600 dark:text-rose-400 text-sm flex gap-2">
                <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                <span>{authError}</span>
              </div>
            )}

            <form className="space-y-4" onSubmit={isLogin ? handleLogin : handleRegister}>
              {!isLogin && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-1.5">First Name</label>
                    <input 
                      type="text" 
                      required
                      placeholder=""
                      value={firstName} 
                      onChange={e => setFirstName(e.target.value)}
                      className="w-full bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-1.5">Last Name</label>
                    <input 
                      type="text" 
                      required
                      placeholder=""
                      value={lastName} 
                      onChange={e => setLastName(e.target.value)}
                      className="w-full bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4.5 w-4.5 text-zinc-400" />
                  <input 
                    type="email" 
                    required
                    placeholder=""
                    value={email} 
                    onChange={e => setEmail(e.target.value)}
                    className="w-full bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-lg pl-10 pr-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4.5 w-4.5 text-zinc-400" />
                  <input 
                    type="password" 
                    required
                    placeholder={isLogin ? "••••••••••••" : "Min 8 chars (1 uppercase, 1 lowercase, 1 digit, 1 symbol)"}
                    value={password} 
                    onChange={e => setPassword(e.target.value)}
                    className="w-full bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-lg pl-10 pr-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>
              </div>

              <button 
                type="submit" 
                disabled={authLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg py-2.5 font-semibold text-sm transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {authLoading && <RefreshCw className="h-4.5 w-4.5 animate-spin" />}
                {isLogin ? 'Sign In' : 'Create Developer Profile'}
              </button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-zinc-200 dark:border-zinc-800" /></div>
              <div className="relative flex justify-center text-xs uppercase"><span className="bg-zinc-50 dark:bg-[#09090b] px-2 text-zinc-500">Or Continue With</span></div>
            </div>

            <div className="w-full flex justify-center py-1">
              <div id="google-signin-btn-container" className="w-full flex justify-center"></div>
            </div>

            <p className="text-center text-sm text-zinc-500">
              {isLogin ? "Don't have an account? " : 'Already registered? '}
              <button 
                onClick={() => setIsLogin(!isLogin)} 
                className="text-emerald-600 hover:underline font-semibold"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ------------------ MAIN DASHBOARD VIEWS ------------------

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? 'dark bg-[#09090b] text-zinc-200' : 'bg-zinc-50 text-zinc-900'}`}>
      
      {/* Top Glassmorphic Navigation Header */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-[#09090b]/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-850 transition-colors">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-500">
                <Shield className="h-5.5 w-5.5" />
              </div>
              <span className="font-extrabold text-lg tracking-tight dark:text-zinc-50">Sentinel AI</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button 
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-900 dark:hover:bg-zinc-800 text-zinc-650 dark:text-zinc-400 transition-colors"
            >
              {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>

            <div className="flex items-center gap-2 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-1.5">
              <User className="h-4.5 w-4.5 text-zinc-400" />
              <span className="text-xs font-semibold hidden md:inline text-zinc-600 dark:text-zinc-300">
                {user?.first_name || 'Developer'}
              </span>
            </div>

            <button 
              onClick={handleLogout}
              className="p-2 rounded-lg text-rose-500 hover:bg-rose-500/10 transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Frame */}
      <div className="flex-1 max-w-[1600px] w-full mx-auto px-6 py-8 flex flex-col md:flex-row gap-8">
        
        {/* Left Navigation Bar */}
        <aside className="w-full md:w-60 flex-shrink-0 space-y-1">
          <button 
            onClick={() => { setActiveTab('dashboard'); refreshAllData(); }}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'dashboard' 
                ? 'bg-emerald-600 text-white shadow-sm' 
                : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850'
            }`}
          >
            <Activity className="h-5 w-5" />
            <span>Dashboard</span>
          </button>

          <button 
            onClick={() => { setActiveTab('repos'); fetchRepositories(); }}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'repos' 
                ? 'bg-emerald-600 text-white shadow-sm' 
                : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850'
            }`}
          >
            <Layers className="h-5 w-5" />
            <span>Repositories</span>
          </button>

          <button 
            onClick={() => { setActiveTab('scans'); fetchScans(); }}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'scans' 
                ? 'bg-emerald-600 text-white shadow-sm' 
                : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850'
            }`}
          >
            <Layers className="h-5 w-5" />
            <span>Scan History</span>
          </button>

          <button 
            onClick={() => { setActiveTab('secrets'); fetchSecrets(); }}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'secrets' 
                ? 'bg-emerald-600 text-white shadow-sm' 
                : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850'
            }`}
          >
            <Key className="h-5 w-5" />
            <span>Secrets & Leaks</span>
          </button>

          <button 
            onClick={() => { setActiveTab('audit'); fetchAuditLogs(); }}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'audit' 
                ? 'bg-emerald-600 text-white shadow-sm' 
                : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-850'
            }`}
          >
            <FileText className="h-5 w-5" />
            <span>Audit Logs</span>
          </button>
        </aside>

        {/* Right Active View Frame */}
        <main className="flex-1 min-w-0">
          <>
              {/* -------------------- TAB: DASHBOARD -------------------- */}
              {activeTab === 'dashboard' && (
                <div className="space-y-8">
                  {/* KPI Summary Cards Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-2">
                      <div className="flex justify-between items-center text-zinc-500">
                        <span className="text-xs font-semibold uppercase tracking-wider">Total Active Leaks</span>
                        <div className="p-1.5 bg-rose-500/10 rounded-lg text-rose-500"><AlertTriangle className="h-5 w-5" /></div>
                      </div>
                      <div className="text-3xl font-extrabold tracking-tight dark:text-zinc-50">
                        {secrets.filter(s => s.status === 'active').length}
                      </div>
                      <div className="text-xs text-zinc-500">Secrets requiring urgent validation</div>
                    </div>

                    <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-2">
                      <div className="flex justify-between items-center text-zinc-500">
                        <span className="text-xs font-semibold uppercase tracking-wider">Monitored Repos</span>
                        <div className="p-1.5 bg-blue-500/10 rounded-lg text-blue-500"><Layers className="h-5 w-5" /></div>
                      </div>
                      <div className="text-3xl font-extrabold tracking-tight dark:text-zinc-50">
                        {repos.length}
                      </div>
                      <div className="text-xs text-zinc-500">Active repository targets</div>
                    </div>

                    <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-2">
                      <div className="flex justify-between items-center text-zinc-500">
                        <span className="text-xs font-semibold uppercase tracking-wider">Scans Conducted</span>
                        <div className="p-1.5 bg-purple-500/10 rounded-lg text-purple-500"><Activity className="h-5 w-5" /></div>
                      </div>
                      <div className="text-3xl font-extrabold tracking-tight dark:text-zinc-50">
                        {scans.length}
                      </div>
                      <div className="text-xs text-zinc-500">Background engine executions</div>
                    </div>

                    <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-2">
                      <div className="flex justify-between items-center text-zinc-500">
                        <span className="text-xs font-semibold uppercase tracking-wider">Mitigated Leaks</span>
                        <div className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-500"><CheckCircle className="h-5 w-5" /></div>
                      </div>
                      <div className="text-3xl font-extrabold tracking-tight dark:text-zinc-50">
                        {secrets.filter(s => s.status !== 'active').length}
                      </div>
                      <div className="text-xs text-zinc-500">Vulnerabilities marked safe/resolved</div>
                    </div>
                  </div>

                  {/* Empty state alert / Quick starter */}
                  {repos.length === 0 && (
                    <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-emerald-500 inline-flex items-center gap-1.5">
                          <Sparkles className="h-4 w-4" />
                          <span>Get Started: Scan the Vulnerable Repository Demo</span>
                        </h4>
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">
                          Sentinel AI detects API keys, Postgres strings, and secrets inside codebases. Click to register and run the scanner engine on our mock vulnerable repo.
                        </p>
                      </div>
                      <button 
                        onClick={handleProvisionDemoData}
                        disabled={scanningRepoId !== null}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg px-4 py-2 flex items-center gap-1.5 transition-colors flex-shrink-0 disabled:opacity-50"
                      >
                        {scanningRepoId !== null ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Layers className="h-3.5 w-3.5" />}
                        <span>Register & Scan Demo Repo</span>
                      </button>
                    </div>
                  )}

                  {/* Apache ECharts Rows */}
                  {analytics && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-4">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500">Leaks by Severity Level</h3>
                        <div className="h-64">
                          <ReactECharts 
                            option={getSeverityChartOption()} 
                            style={{ height: '100%', width: '100%' }}
                            theme={darkMode ? 'dark' : ''}
                          />
                        </div>
                      </div>

                      <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-4">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500">Top Secret Classes Found</h3>
                        <div className="h-64">
                          <ReactECharts 
                            option={getTypeChartOption()} 
                            style={{ height: '100%', width: '100%' }}
                            theme={darkMode ? 'dark' : ''}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* -------------------- TAB: REPOSITORIES -------------------- */}
              {activeTab === 'repos' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <div className="space-y-1">
                      <h2 className="text-xl font-bold dark:text-zinc-50">Repositories</h2>
                      <p className="text-xs text-zinc-500 dark:text-zinc-400">List registered repositories monitored for secrets.</p>
                    </div>
                    <button 
                      onClick={() => setIsRegisteringRepo(true)}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg px-3 py-2 flex items-center gap-1 transition-colors"
                    >
                      <Plus className="h-4 w-4" />
                      <span>Add Repository</span>
                    </button>
                  </div>

                  <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl overflow-hidden shadow-sm">
                    {loadingRepos ? (
                      <div className="p-8 text-center"><RefreshCw className="h-8 w-8 animate-spin text-zinc-450 mx-auto" /></div>
                    ) : repos.length === 0 ? (
                      <div className="p-12 text-center text-zinc-550">No repositories registered yet. Click Add Repository or Provision Demo Data to start.</div>
                    ) : (
                      <table className="w-full text-left text-sm border-collapse">
                        <thead>
                          <tr className="border-b border-zinc-200 dark:border-zinc-850 bg-zinc-50 dark:bg-zinc-900/50 text-zinc-500">
                            <th className="p-4 font-semibold">Repository Name</th>
                            <th className="p-4 font-semibold">Git Location</th>
                            <th className="p-4 font-semibold">Default Branch</th>
                            <th className="p-4 font-semibold">Provider</th>
                            <th className="p-4 font-semibold">Schedule</th>
                            <th className="p-4 font-semibold text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {repos.map(repo => (
                            <tr key={repo.id} className="border-b border-zinc-200 dark:border-zinc-850 hover:bg-zinc-50 dark:hover:bg-zinc-850/50 text-zinc-700 dark:text-zinc-200">
                              <td className="p-4 font-semibold">{repo.name}</td>
                              <td className="p-4 font-mono text-xs max-w-xs truncate">{repo.clone_url}</td>
                              <td className="p-4">
                                <span className="inline-flex bg-zinc-100 dark:bg-zinc-800 text-zinc-650 dark:text-zinc-300 rounded px-1.5 py-0.5 text-xs font-mono">
                                  {repo.branches?.map((b: any) => b.name).join(', ') || 'main'}
                                </span>
                              </td>
                              <td className="p-4 uppercase text-xs font-semibold">{repo.provider}</td>
                              <td className="p-4">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                  repo.scan_schedule === 'manual' ? 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800/40 dark:text-zinc-300' :
                                  repo.scan_schedule === 'daily' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300' :
                                  'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300'
                                }`}>
                                  {repo.scan_schedule || 'manual'}
                                </span>
                              </td>
                              <td className="p-4 text-right">
                                <button 
                                  onClick={() => openScanBranchModal(repo)}
                                  disabled={scanningRepoId !== null}
                                  className="bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 font-semibold text-xs rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                                >
                                  {scanningRepoId === repo.id ? (
                                    <>
                                      <RefreshCw className="h-3 w-3 animate-spin" />
                                      <span>Scanning...</span>
                                    </>
                                  ) : (
                                    <>
                                      <Activity className="h-3 w-3" />
                                      <span>Scan Now</span>
                                    </>
                                  )}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              )}

              {/* -------------------- TAB: SCANS -------------------- */}
              {activeTab === 'scans' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold dark:text-zinc-50">Scan Executions</h2>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">Review past pipeline scanner execution logs.</p>
                  </div>

                  <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl overflow-hidden shadow-sm">
                    {loadingScans ? (
                      <div className="p-8 text-center"><RefreshCw className="h-8 w-8 animate-spin text-zinc-450 mx-auto" /></div>
                    ) : scans.length === 0 ? (
                      <div className="p-12 text-center text-zinc-550">No scans executed yet. Use "Scan Now" inside repositories to execute.</div>
                    ) : (
                      <table className="w-full text-left text-sm border-collapse">
                        <thead>
                          <tr className="border-b border-zinc-200 dark:border-zinc-850 bg-zinc-50 dark:bg-zinc-900/50 text-zinc-500">
                            <th className="p-4 font-semibold">Scan ID</th>
                            <th className="p-4 font-semibold">Repository</th>
                            <th className="p-4 font-semibold">Commit Target</th>
                            <th className="p-4 font-semibold">Status</th>
                            <th className="p-4 font-semibold">Secrets Found</th>
                            <th className="p-4 font-semibold">Executed At</th>
                          </tr>
                        </thead>
                        <tbody>
                          {scans.map(scan => (
                            <tr key={scan.id} className="border-b border-zinc-200 dark:border-zinc-850 hover:bg-zinc-50 dark:hover:bg-zinc-850/50 text-zinc-700 dark:text-zinc-200">
                              <td className="p-4 font-mono text-xs">#{scan.id}</td>
                              <td className="p-4 font-semibold">Repo ID: {scan.repository_id}</td>
                              <td className="p-4 font-mono text-xs">{scan.commit_hash?.substring(0, 7) || 'N/A'}</td>
                              <td className="p-4">
                                <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                                  scan.status === 'completed' 
                                    ? 'bg-emerald-500/10 text-emerald-500' 
                                    : scan.status === 'scanning' || scan.status === 'queued'
                                      ? 'bg-blue-500/10 text-blue-500'
                                      : 'bg-rose-500/10 text-rose-500'
                                }`}>
                                  {scan.status}
                                </span>
                              </td>
                              <td className="p-4 font-bold">{scan.secrets_found}</td>
                              <td className="p-4 text-xs text-zinc-500">
                                {new Date(scan.created_at).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              )}

              {/* -------------------- TAB: SECRETS -------------------- */}
              {activeTab === 'secrets' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold dark:text-zinc-50">Secrets Detected</h2>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">List of all active and triaged credentials leaked inside repositories.</p>
                  </div>

                  {/* Filters / Search Bar */}
                  <div className="flex flex-col sm:flex-row gap-4 justify-between">
                    <div className="relative w-full sm:w-72">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                      <input 
                        type="text" 
                        placeholder="Search secrets, files..."
                        value={secretSearch}
                        onChange={e => setSecretSearch(e.target.value)}
                        className="w-full bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-lg pl-9 pr-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 shadow-sm"
                      />
                    </div>

                    <div className="flex gap-2">
                      <select
                        value={secretFilter}
                        onChange={e => setSecretFilter(e.target.value)}
                        className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-700 dark:text-zinc-300 focus:outline-none cursor-pointer shadow-sm"
                      >
                        <option value="all">All Leaks</option>
                        <option value="active">Active Only</option>
                        <option value="resolved">Resolved</option>
                        <option value="false_positive">False Positives</option>
                      </select>
                    </div>
                  </div>

                  {/* Split Screen Layout */}
                  <div className="flex flex-col lg:flex-row gap-6">
                    {/* Left: Primary Data Table */}
                    <div className={`transition-all duration-300 ${selectedSecret ? 'w-full lg:w-2/3' : 'w-full'} bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl overflow-hidden shadow-sm`}>
                      {loadingSecrets ? (
                        <div className="p-8 text-center"><RefreshCw className="h-8 w-8 animate-spin text-zinc-450 mx-auto" /></div>
                      ) : secrets.length === 0 ? (
                        <div className="p-12 text-center text-zinc-550">No secrets found. Trigger a scan under Repositories to populate findings.</div>
                      ) : (
                        <table className="w-full text-left text-sm border-collapse">
                          <thead>
                            <tr className="border-b border-zinc-200 dark:border-zinc-850 bg-zinc-50 dark:bg-zinc-900/50 text-zinc-500">
                              <th className="p-4 font-semibold">Classification</th>
                              <th className="p-4 font-semibold">Location File</th>
                              <th className="p-4 font-semibold">Severity</th>
                              <th className="p-4 font-semibold">Status</th>
                              {!selectedSecret && <th className="p-4 font-semibold">Confidence</th>}
                            </tr>
                          </thead>
                          <tbody>
                            {secrets
                              .filter(s => {
                                if (secretFilter === 'active') return s.status === 'active';
                                if (secretFilter === 'resolved') return s.status === 'resolved';
                                if (secretFilter === 'false_positive') return s.status === 'false_positive';
                                return true;
                              })
                              .filter(s => {
                                const q = secretSearch.toLowerCase();
                                return s.secret_type.toLowerCase().includes(q) || s.file_path.toLowerCase().includes(q);
                              })
                              .map(sec => (
                                <tr 
                                  key={sec.id} 
                                  onClick={() => setSelectedSecret(sec)}
                                  className={`border-b border-zinc-200 dark:border-zinc-850 hover:bg-zinc-50 dark:hover:bg-zinc-850/50 cursor-pointer text-zinc-700 dark:text-zinc-200 transition-colors ${
                                    selectedSecret?.id === sec.id ? 'bg-emerald-500/5 dark:bg-emerald-500/5' : ''
                                  }`}
                                >
                                  <td className="p-4 font-semibold flex items-center gap-2">
                                    <Key className="h-4.5 w-4.5 text-zinc-450" />
                                    <span>{sec.secret_type}</span>
                                  </td>
                                  <td className="p-4 font-mono text-xs truncate max-w-xs">{sec.file_path}</td>
                                  <td className="p-4">
                                    <span className={`inline-flex rounded px-2 py-0.5 text-xs font-bold ${
                                      sec.severity === 'critical' 
                                        ? 'bg-rose-500/10 text-rose-500' 
                                        : sec.severity === 'high'
                                          ? 'bg-orange-500/10 text-orange-500'
                                          : 'bg-blue-500/10 text-blue-500'
                                    }`}>
                                      {sec.severity}
                                    </span>
                                  </td>
                                  <td className="p-4">
                                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                                      sec.status === 'active' 
                                        ? 'bg-rose-500/10 text-rose-500' 
                                        : sec.status === 'resolved'
                                          ? 'bg-emerald-500/10 text-emerald-500'
                                          : 'bg-zinc-500/10 text-zinc-500'
                                    }`}>
                                      {sec.status}
                                    </span>
                                  </td>
                                  {!selectedSecret && (
                                    <td className="p-4">
                                      <div className="w-full bg-zinc-205 dark:bg-zinc-800 rounded-full h-1.5 max-w-[80px]">
                                        <div 
                                          className="bg-emerald-500 h-1.5 rounded-full" 
                                          style={{ width: `${Math.round(sec.confidence_score * 100)}%` }}
                                        />
                                      </div>
                                    </td>
                                  )}
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      )}
                    </div>

                    {/* Right: Detail Side Panel */}
                    {/* Right: Detail Side Panel */}
                    {selectedSecret && (
                      <div className="w-full lg:w-1/3 bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl p-5 shadow-sm space-y-6 flex flex-col relative h-[calc(100vh-220px)] lg:h-auto overflow-hidden transition-all duration-350">
                        {/* Header */}
                        <div className="flex justify-between items-center border-b border-zinc-150 dark:border-zinc-850 pb-3 flex-shrink-0">
                          <div className="space-y-0.5">
                            <h3 className="font-bold text-sm dark:text-zinc-50">Secret Leak Context</h3>
                            <span className="text-xs text-zinc-500">{selectedSecret.secret_type}</span>
                          </div>
                          <button 
                            onClick={() => setSelectedSecret(null)}
                            className="p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-850 text-zinc-400"
                          >
                            <X className="h-5.5 w-5.5" />
                          </button>
                        </div>

                        {/* Scrollable Content Area */}
                        <div className="flex-1 overflow-y-auto pr-1 space-y-6 scrollbar-thin">
                          {/* File Details */}
                          <div className="space-y-4 text-xs">
                            <div>
                              <span className="block font-semibold text-zinc-500 mb-1">File Location</span>
                              <div className="p-2.5 bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-850 rounded-lg font-mono break-all text-zinc-700 dark:text-zinc-300">
                                {selectedSecret.file_path}
                              </div>
                            </div>

                            <div>
                              <span className="block font-semibold text-zinc-500 mb-1">Masked Leak</span>
                              <div className="p-2.5 bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-850 rounded-lg font-mono break-all text-rose-500 font-bold">
                                {selectedSecret.masked_secret}
                              </div>
                            </div>

                            {selectedSecret.context_before && (
                              <div>
                                <span className="block font-semibold text-zinc-500 mb-1">Leaked Snippet Context</span>
                                <div className="p-2.5 bg-zinc-950 text-zinc-200 border border-zinc-850 rounded-lg font-mono whitespace-pre overflow-x-auto text-[11px] leading-relaxed">
                                  {selectedSecret.context_before}
                                  <span className="bg-rose-500/20 text-rose-350 px-1 border border-rose-500/40 rounded block my-1">
                                    {selectedSecret.context_match}
                                  </span>
                                  {selectedSecret.context_after}
                                </div>
                              </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <span className="block font-semibold text-zinc-500 mb-1">Line Number</span>
                                <span className="text-sm font-bold dark:text-zinc-50">Line {selectedSecret.line_number}</span>
                              </div>
                              <div>
                                <span className="block font-semibold text-zinc-500 mb-1">Entropy Score</span>
                                <span className="text-sm font-bold dark:text-zinc-50">{selectedSecret.entropy?.toFixed(4) || 'N/A'}</span>
                              </div>
                            </div>
                          </div>

                          {/* AI Threats & Remediation */}
                          <div className="border-t border-zinc-150 dark:border-zinc-850 pt-4 space-y-4">
                            <div className="flex items-center gap-1.5 text-zinc-800 dark:text-zinc-200 font-bold text-xs">
                              <Sparkles className="h-4.5 w-4.5 text-emerald-500 animate-pulse" />
                              <span>Sentinel AI Security Insights</span>
                            </div>

                            {loadingAi ? (
                              <div className="p-4 bg-zinc-50 dark:bg-zinc-900/30 border border-zinc-200 dark:border-zinc-850 rounded-xl text-center space-y-2">
                                <RefreshCw className="h-6 w-6 animate-spin text-emerald-500 mx-auto" />
                                <p className="text-xs text-zinc-500">Generating AI explanations & remediation steps...</p>
                              </div>
                            ) : aiAnalysis ? (
                              <div className="space-y-4 text-xs">
                                {/* Explanation Card */}
                                <div className="bg-emerald-500/5 border border-emerald-500/10 dark:border-emerald-500/20 rounded-xl p-4 space-y-2.5">
                                  <div className="flex justify-between items-center">
                                    <span className="font-semibold text-emerald-700 dark:text-emerald-400">Threat Explanation</span>
                                    <span className={`inline-flex rounded px-1.5 py-0.5 text-[10px] font-extrabold uppercase ${
                                      aiAnalysis.explanation.risk_level === 'critical' || aiAnalysis.explanation.risk_level === 'high'
                                        ? 'bg-rose-500/10 text-rose-500'
                                        : 'bg-orange-500/10 text-orange-500'
                                    }`}>
                                      {aiAnalysis.explanation.risk_level} Risk
                                    </span>
                                  </div>
                                  <p className="text-zinc-600 dark:text-zinc-300 leading-relaxed">
                                    {aiAnalysis.explanation.danger_description}
                                  </p>
                                  <div>
                                    <span className="block font-semibold text-zinc-500 mb-0.5">Exploit Scenario:</span>
                                    <p className="text-zinc-600 dark:text-zinc-300 italic">
                                      "{aiAnalysis.explanation.exploitation_scenario}"
                                    </p>
                                  </div>
                                  <div>
                                    <span className="block font-semibold text-zinc-500 mb-0.5">Business Impact:</span>
                                    <p className="text-zinc-600 dark:text-zinc-300">
                                      {aiAnalysis.explanation.business_impact}
                                    </p>
                                  </div>
                                </div>

                                {/* Remediation Card */}
                                <div className="bg-zinc-50 dark:bg-zinc-900/30 border border-zinc-200 dark:border-zinc-850 rounded-xl p-4 space-y-3">
                                  <span className="font-semibold text-zinc-800 dark:text-zinc-200 block border-b border-zinc-200 dark:border-zinc-800 pb-1.5">Safe Code Refactoring</span>
                                  
                                  <div className="space-y-1">
                                    <span className="block font-semibold text-zinc-500">Secure Code Pattern:</span>
                                    <pre className="p-2.5 bg-zinc-950 text-emerald-400 border border-zinc-855 rounded-lg font-mono text-[10px] whitespace-pre overflow-x-auto leading-relaxed">
                                      {aiAnalysis.remediation.safe_code}
                                    </pre>
                                  </div>

                                  <div className="space-y-1">
                                    <span className="block font-semibold text-zinc-500">Environment Template (.env):</span>
                                    <pre className="p-2 bg-zinc-950 text-zinc-300 border border-zinc-855 rounded font-mono text-[10px] whitespace-pre overflow-x-auto">
                                      {aiAnalysis.remediation.env_template}
                                    </pre>
                                  </div>

                                  <div className="space-y-1">
                                    <span className="block font-semibold text-zinc-500">Recommended Rotation Steps:</span>
                                    <p className="text-zinc-600 dark:text-zinc-300 whitespace-pre-line leading-relaxed">
                                      {aiAnalysis.remediation.rotation_steps}
                                    </p>
                                  </div>
                                </div>

                                {/* Q&A Chat Section */}
                                <div className="border-t border-zinc-150 dark:border-zinc-850 pt-4 space-y-3">
                                  <span className="font-semibold text-zinc-800 dark:text-zinc-200 block">AI Security Assistant Chat</span>
                                  
                                  {/* Chat bubble list */}
                                  <div className="space-y-2.5 max-h-[180px] overflow-y-auto pr-1 border border-zinc-200 dark:border-zinc-850 rounded-lg p-2.5 bg-zinc-50/50 dark:bg-[#08080a]">
                                    {aiChatHistory.length === 0 ? (
                                      <p className="text-center text-[11px] text-zinc-500 py-3">Ask any security questions about rotating or protecting this key.</p>
                                    ) : (
                                      aiChatHistory.map((msg, index) => (
                                        <div key={index} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                          <div className={`max-w-[90%] rounded-lg px-2.5 py-1.5 text-[11px] leading-relaxed shadow-sm ${
                                            msg.role === 'user' 
                                              ? 'bg-emerald-600 text-white' 
                                              : 'bg-zinc-200 dark:bg-zinc-850 text-zinc-800 dark:text-zinc-200'
                                          }`}>
                                            {msg.text}
                                          </div>
                                        </div>
                                      ))
                                    )}
                                    {sendingAiChat && (
                                      <div className="flex items-center gap-1.5 text-zinc-500 text-[10px]">
                                        <RefreshCw className="h-3 w-3 animate-spin" />
                                        <span>AI is typing...</span>
                                      </div>
                                    )}
                                  </div>

                                  {/* Chat Form */}
                                  <div className="flex gap-2">
                                    <input 
                                      type="text" 
                                      value={aiChatInput}
                                      onChange={(e) => setAiChatInput(e.target.value)}
                                      onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                          handleSendAiQuestion(e);
                                        }
                                      }}
                                      placeholder="How to rotate this?"
                                      disabled={sendingAiChat}
                                      className="flex-1 min-w-0 bg-white dark:bg-zinc-950 border border-zinc-250 dark:border-zinc-800 rounded-lg px-2.5 py-1.5 text-[11px] focus:outline-none focus:border-emerald-500 text-zinc-800 dark:text-zinc-200"
                                    />
                                    <button 
                                      type="button"
                                      onClick={(e) => handleSendAiQuestion(e)}
                                      disabled={sendingAiChat || !aiChatInput.trim()}
                                      className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-400 text-white rounded-lg px-3 py-1.5 font-semibold text-[11px] transition-colors"
                                    >
                                      Send
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ) : (
                              <p className="text-center text-xs text-zinc-500">Failed to load AI Insights.</p>
                            )}
                          </div>
                        </div>

                        {/* Actions (Footer) */}
                        {selectedSecret.status === 'active' && (
                          <div className="border-t border-zinc-150 dark:border-zinc-850 pt-4 flex gap-2.5 flex-shrink-0 bg-white dark:bg-[#0c0c0f]">
                            <button 
                              onClick={() => handleUpdateSecretStatus(selectedSecret.id, 'resolved')}
                              className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg py-2.5 font-semibold text-xs transition-colors shadow-sm"
                            >
                              Mark Resolved
                            </button>
                            <button 
                              onClick={() => handleUpdateSecretStatus(selectedSecret.id, 'false_positive')}
                              className="flex-1 border border-zinc-200 dark:border-zinc-850 hover:bg-zinc-100 dark:hover:bg-zinc-850 text-zinc-700 dark:text-zinc-300 rounded-lg py-2.5 font-semibold text-xs transition-colors"
                            >
                              False Positive
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* -------------------- TAB: AUDIT LOGS -------------------- */}
              {activeTab === 'audit' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold dark:text-zinc-50">Audit Trail</h2>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">Verifiable log of all configuration alterations and status overrides.</p>
                  </div>

                  <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-850 rounded-xl overflow-hidden shadow-sm">
                    {loadingAudits ? (
                      <div className="p-8 text-center"><RefreshCw className="h-8 w-8 animate-spin text-zinc-450 mx-auto" /></div>
                    ) : auditLogs.length === 0 ? (
                      <div className="p-12 text-center text-zinc-550">No events audited in this organization yet.</div>
                    ) : (
                      <table className="w-full text-left text-sm border-collapse">
                        <thead>
                          <tr className="border-b border-zinc-200 dark:border-zinc-850 bg-zinc-50 dark:bg-zinc-900/50 text-zinc-500">
                            <th className="p-4 font-semibold">Actor Email</th>
                            <th className="p-4 font-semibold">Action Triggered</th>
                            <th className="p-4 font-semibold">Entity Target</th>
                            <th className="p-4 font-semibold">Network IP</th>
                            <th className="p-4 font-semibold">Audited Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {auditLogs.map(log => (
                            <tr key={log.id} className="border-b border-zinc-200 dark:border-zinc-850 hover:bg-zinc-50 dark:hover:bg-zinc-850/50 text-zinc-700 dark:text-zinc-200">
                              <td className="p-4 font-semibold">User ID: {log.user_id}</td>
                              <td className="p-4 font-mono text-xs">{log.action}</td>
                              <td className="p-4">{log.target_type} ({log.target_id})</td>
                              <td className="p-4 font-mono text-xs">{log.ip_address || '127.0.0.1'}</td>
                              <td className="p-4 text-xs text-zinc-500">
                                {new Date(log.created_at).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              )}
            </>
        </main>
      </div>



      {/* -------------------- WORKSPACE MODAL: REGISTER REPO -------------------- */}
      {isRegisteringRepo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-100 dark:border-zinc-850 pb-2">
              <h3 className="font-bold text-sm dark:text-zinc-50">Register Repository</h3>
              <button onClick={() => setIsRegisteringRepo(false)} className="text-zinc-400 hover:text-zinc-650"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleRegisterRepo} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-zinc-500 mb-1.5">Repository Display Name</label>
                  <input 
                    type="text" 
                    required
                    placeholder="Frontend Repo"
                    value={repoName} 
                    onChange={e => setRepoName(e.target.value)}
                    className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-zinc-500 mb-1.5">Git Provider</label>
                  <select
                    value={repoProvider}
                    onChange={e => setRepoProvider(e.target.value)}
                    className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none"
                  >
                    <option value="github">GitHub</option>
                    <option value="gitlab">GitLab</option>
                    <option value="bitbucket">Bitbucket</option>
                    <option value="azure">Azure DevOps</option>
                    <option value="local">Local Folder</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block font-semibold text-zinc-500 mb-1.5">Clone URL (Git HTTPS or Local Absolute Path)</label>
                <input 
                  type="text" 
                  required
                  placeholder={getPlaceholderByProvider()}
                  value={repoUrl} 
                  onChange={e => setRepoUrl(e.target.value)}
                  className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none font-mono text-[11px]"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-zinc-500 mb-1.5">Default Scan Branch</label>
                  <input 
                    type="text" 
                    required
                    value={repoBranch} 
                    onChange={e => setRepoBranch(e.target.value)}
                    className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-zinc-500 mb-1.5">Scan Schedule</label>
                  <select
                    value={repoSchedule}
                    onChange={e => setRepoSchedule(e.target.value)}
                    className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none"
                  >
                    <option value="manual">Manual Trigger Only</option>
                    <option value="daily">Daily Auto-Scan</option>
                    <option value="weekly">Weekly Auto-Scan</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block font-semibold text-zinc-500 mb-1.5">Access Token / Credentials (Optional)</label>
                <input 
                  type="password" 
                  placeholder="Personal Access Token (for private repos)"
                  value={repoAccessToken} 
                  onChange={e => setRepoAccessToken(e.target.value)}
                  className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none"
                />
              </div>
              <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg py-2.5 font-semibold text-sm transition-colors">
                Register Repository
              </button>
            </form>
          </div>
        </div>
      )}

      {/* -------------------- WORKSPACE MODAL: SCAN BRANCH SELECTOR -------------------- */}
      {isScanBranchModalOpen && scanBranchModalRepo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#0c0c0f] border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-100 dark:border-zinc-850 pb-2">
              <h3 className="font-bold text-sm dark:text-zinc-50">Select Scan Branch</h3>
              <button onClick={() => setIsScanBranchModalOpen(false)} className="text-zinc-400 hover:text-zinc-650"><X className="h-5 w-5" /></button>
            </div>
            
            <div className="text-xs space-y-4">
              <p className="text-zinc-500 dark:text-zinc-400">
                Triggering manual secrets scan for <strong className="text-zinc-900 dark:text-zinc-250">{scanBranchModalRepo.name}</strong>.
              </p>
              
              {loadingRemoteBranches ? (
                <div className="py-4 text-center space-y-2">
                  <RefreshCw className="h-6 w-6 animate-spin text-emerald-600 mx-auto" />
                  <span className="text-zinc-500 block">Fetching branches from remote origin...</span>
                </div>
              ) : (
                <div>
                  <label className="block font-semibold text-zinc-500 mb-1.5">Target Branch</label>
                  <select
                    value={selectedScanBranch}
                    onChange={e => setSelectedScanBranch(e.target.value)}
                    className="w-full bg-white dark:bg-[#09090b] border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-50 focus:outline-none"
                  >
                    {remoteBranches.map(b => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                  </select>
                </div>
              )}
              
              <div className="flex gap-2 pt-2">
                <button 
                  onClick={() => setIsScanBranchModalOpen(false)} 
                  className="flex-1 border border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg py-2 font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleTriggerScanWithBranch}
                  disabled={loadingRemoteBranches}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg py-2 font-semibold transition-colors disabled:opacity-50"
                >
                  Start Scan
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-850 py-4 text-center text-xs text-zinc-500">
        Sentinel AI Platform © 2026. Made with ❤️ for secure development workflows.
      </footer>
    </div>
  );
}
