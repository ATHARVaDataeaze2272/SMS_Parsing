import React, { useState, useEffect } from 'react';
import { 
  ChevronDown, Upload, RefreshCw, AlertCircle, 
  FilePlus, Check, X, ChevronLeft, ChevronRight 
} from 'lucide-react';
import Chart from 'chart.js/auto';

const FinancialDashboard = () => {
  const API_BASE_URL = '/api';

  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState({
    total: 0,
    processed: 0,
    succeeded: 0,
    failed: 0,
    status: 'idle'
  });
  const [summaryData, setSummaryData] = useState({
    total_customers: 0,
    total_transactions: 0,
    message_type_stats: [],
    recent_transactions: []
  });
  const [uploadResponse, setUploadResponse] = useState(null);
  const [statsExpanded, setStatsExpanded] = useState(true);
  const [messagesExpanded, setMessagesExpanded] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [messageTypeCounts, setMessageTypeCounts] = useState({});
  const [selectedType, setSelectedType] = useState('');
  const [messagesByType, setMessagesByType] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [analyticsExpanded, setAnalyticsExpanded] = useState(true);
  const [chartInstance, setChartInstance] = useState(null);
  // New state for customer transactions
  const [customers, setCustomers] = useState([]);
  const [customersTotal, setCustomersTotal] = useState(0);
  const [customersPage, setCustomersPage] = useState(1);
  const [customersLimit] = useState(10);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [customerSummary, setCustomerSummary] = useState(null);
  const [customerTransactions, setCustomerTransactions] = useState([]);
  const [transactionsTotal, setTransactionsTotal] = useState(0);
  const [transactionsPage, setTransactionsPage] = useState(1);
  const [transactionsLimit] = useState(10);
  const [transactionFilterType, setTransactionFilterType] = useState('');
  const [customerSectionExpanded, setCustomerSectionExpanded] = useState(true);

  // Fetch initial data on component mount
  useEffect(() => {
    fetchDashboardData();
    fetchCustomers();
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  }, []);

  // Fetch customers when page changes
  useEffect(() => {
    fetchCustomers();
  }, [customersPage]);

  // Fetch customer summary and transactions when customer is selected
  useEffect(() => {
    if (selectedCustomerId) {
      fetchCustomerSummary();
      fetchCustomerTransactions();
    }
  }, [selectedCustomerId, transactionsPage, transactionFilterType]);

  // Start auto-refresh when processing begins
  useEffect(() => {
    if (processing) {
      const interval = setInterval(() => {
        fetchProcessingStatus();
        if (processingStatus.status === 'completed' || processingStatus.status === 'error') {
          setProcessing(false);
          fetchDashboardData();
          fetchCustomers();
          clearInterval(interval);
        }
      }, 2000);
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    }
  }, [processing, processingStatus.status]);

  // Fetch messages when a message type is selected
  useEffect(() => {
    if (selectedType) {
      fetchMessagesByType();
    }
  }, [selectedType]);

  // Update chart when message type counts change
  useEffect(() => {
    if (Object.keys(messageTypeCounts).length > 0) {
      renderChart();
    }
  }, [messageTypeCounts]);

  const fetchDashboardData = async () => {
    try {
      const summaryResponse = await fetch(`${API_BASE_URL}/analytics/summary`);
      if (!summaryResponse.ok) throw new Error('Failed to fetch summary');
      const summary = await summaryResponse.json();
      setSummaryData(summary);

      const countsResponse = await fetch(`${API_BASE_URL}/message-type-counts`);
      if (!countsResponse.ok) throw new Error('Failed to fetch message type counts');
      const countsData = await countsResponse.json();
      setMessageTypeCounts(countsData.counts || {});
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setUploadResponse({
        status: 'error',
        message: `Error fetching dashboard data: ${error.message}`
      });
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/customers?skip=${(customersPage - 1) * customersLimit}&limit=${customersLimit}`
      );
      if (!response.ok) throw new Error('Failed to fetch customers');
      const data = await response.json();
      setCustomers(data.customers || []);
      setCustomersTotal(data.total || 0);
    } catch (error) {
      console.error('Error fetching customers:', error);
      setUploadResponse({
        status: 'error',
        message: `Error fetching customers: ${error.message}`
      });
    }
  };

  const fetchCustomerSummary = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/customers/${selectedCustomerId}/summary`);
      if (!response.ok) throw new Error('Failed to fetch customer summary');
      const data = await response.json();
      setCustomerSummary(data);
    } catch (error) {
      console.error('Error fetching customer summary:', error);
      setUploadResponse({
        status: 'error',
        message: `Error fetching customer summary: ${error.message}`
      });
    }
  };

  const fetchCustomerTransactions = async () => {
    try {
      const queryParams = new URLSearchParams({
        skip: ((transactionsPage - 1) * transactionsLimit),
        limit: transactionsLimit
      });
      if (transactionFilterType) {
        queryParams.append('message_type', transactionFilterType);
      }
      const response = await fetch(
        `${API_BASE_URL}/customers/${selectedCustomerId}/transactions?${queryParams}`
      );
      if (!response.ok) throw new Error('Failed to fetch customer transactions');
      const data = await response.json();
      setCustomerTransactions(data.transactions || []);
      setTransactionsTotal(data.total || 0);
    } catch (error) {
      console.error('Error fetching customer transactions:', error);
      setUploadResponse({
        status: 'error',
        message: `Error fetching customer transactions: ${error.message}`
      });
    }
  };

  const fetchProcessingStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/processing-status`);
      if (!response.ok) throw new Error('Failed to fetch processing status');
      const status = await response.json();
      setProcessingStatus(status);
    } catch (error) {
      console.error('Error fetching processing status:', error);
    }
  };

  const fetchMessagesByType = async () => {
    setMessagesLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/messages?message_type=${encodeURIComponent(selectedType)}&limit=10`
      );
      if (!response.ok) throw new Error('Failed to fetch messages by type');
      const messages = await response.json();
      setMessagesByType(messages);
    } catch (error) {
      console.error('Error fetching messages by type:', error);
      setUploadResponse({
        status: 'error',
        message: `Error fetching messages: ${error.message}`
      });
    } finally {
      setMessagesLoading(false);
    }
  };

  const renderChart = () => {
    const ctx = document.getElementById('messageTypeChart')?.getContext('2d');
    if (!ctx) return;

    if (chartInstance) {
      chartInstance.destroy();
    }

    const labels = Object.keys(messageTypeCounts);
    const data = Object.values(messageTypeCounts);

    const newChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Message Type Counts',
          data: data,
          backgroundColor: [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#C9CBCF', '#7EC850'
          ],
          borderColor: [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#C9CBCF', '#7EC850'
          ],
          borderWidth: 1
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Number of Messages'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Message Type'
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Messages by Type'
          }
        }
      }
    });

    setChartInstance(newChart);
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      alert('Please select a file first');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('delimiter', ',');
      formData.append('has_header', 'true');

      const response = await fetch(`${API_BASE_URL}/upload-csv`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');
      const result = await response.json();
      setUploadResponse({
        status: result.status,
        message: result.message
      });

      if (result.status === 'accepted') {
        setProcessing(true);
        fetchProcessingStatus();
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadResponse({
        status: 'error',
        message: `Error uploading file: ${error.message}`
      });
    }
  };

  const handleProcessExistingFile = async () => {
    const filePath = prompt('Enter the path to the CSV file on the server:');
    if (!filePath) return;

    try {
      const response = await fetch(`${API_BASE_URL}/process-csv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_path: filePath,
          delimiter: ',',
          has_header: true
        })
      });

      if (!response.ok) throw new Error('Processing failed');
      const result = await response.json();
      setUploadResponse({
        status: result.status,
        message: result.message
      });

      if (result.status === 'success') {
        setProcessing(true);
        fetchProcessingStatus();
      }
    } catch (error) {
      console.error('Error processing file:', error);
      setUploadResponse({
        status: 'error',
        message: `Error processing file: ${error.message}`
      });
    }
  };

  const handleRefresh = () => {
    fetchDashboardData();
    fetchProcessingStatus();
    fetchCustomers();
    if (selectedType) {
      fetchMessagesByType();
    }
    if (selectedCustomerId) {
      fetchCustomerSummary();
      fetchCustomerTransactions();
    }
  };

  const renderProgressBar = () => {
    const percentage = processingStatus.total > 0 
      ? Math.floor((processingStatus.processed / processingStatus.total) * 100) 
      : 0;

    return (
      <div className="mt-4">
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium">Processing Progress</span>
          <span className="text-sm font-medium">{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full" 
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>Processed: {processingStatus.processed}/{processingStatus.total}</span>
          <span>Success: {processingStatus.succeeded} | Failed: {processingStatus.failed}</span>
        </div>
      </div>
    );
  };

  const formatCurrency = (amount) => {
    if (amount == null) return 'N/A';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    } catch (error) {
      return isoString;
    }
  };

  // const getTableHeaders = () => {
  //   const allFields = new Set();
  //   messagesByType.forEach(msg => {
  //     Object.keys(msg.extracted_data).forEach(field => allFields.add(field));
  //   });
  //   return Array.from(allFields);
  // };


  const renderSummaryStats = () => {
    const aggregateStats = () => {
      const stats = {
        salary: { transaction_count: 0, total_amount: 0, highest_salary: 0 },
        emi: { transaction_count: 0, total_amount: 0, unique_loans: 0 },
        credit_card: { transaction_count: 0, total_spent: 0, highest_outstanding: 0 },
        investments: { transaction_count: 0, total_invested: 0, unique_folios: 0 },
        insurance: { transaction_count: 0, total_amount: 0, unique_policies: 0 },
        general: { transaction_count: 0, total_amount: 0 }
      };

      summaryData.message_type_stats.forEach(stat => {
        const amount = Number(stat.total_amount) || 0;
        switch (stat.message_type ? stat.message_type.toUpperCase() : '') {
          case 'SALARY_CREDIT':
            stats.salary.transaction_count = stat.count;
            stats.salary.total_amount = amount;
            stats.salary.highest_salary = amount / Math.max(stat.count, 1);
            break;
          case 'EMI_PAYMENT':
            stats.emi.transaction_count = stat.count;
            stats.emi.total_amount = amount;
            stats.emi.unique_loans = stat.unique_loans || 0;
            break;
          case 'CREDIT_CARD_TRANSACTION':
            stats.credit_card.transaction_count = stat.count;
            stats.credit_card.total_spent = amount;
            stats.credit_card.highest_outstanding = stat.max_outstanding || 0;
            break;
          case 'SIP_INVESTMENT':
            stats.investments.transaction_count = stat.count;
            stats.investments.total_invested = amount;
            stats.investments.unique_folios = stat.unique_folios || 0;
            break;
          case 'INSURANCE_PAYMENT':
            stats.insurance.transaction_count = stat.count;
            stats.insurance.total_amount = amount;
            stats.insurance.unique_policies = stat.unique_policies || 0;
            break;
          case 'OTHER_FINANCIAL':
            stats.general.transaction_count = stat.count;
            stats.general.total_amount += amount;
            break;
          case 'CREDIT_TRANSACTION':
            stats.general.transaction_count += stat.count;
            stats.general.total_amount += amount;
            break;
          case 'DEBIT_TRANSACTION':
            stats.general.transaction_count += stat.count;
            stats.general.total_amount += amount;
            break;
          default:
            stats.general.transaction_count += stat.count;
            stats.general.total_amount += amount;
            break;
        }
      });

      return stats;
    };

    const stats = aggregateStats();

    return (
      <div className="mb-6">
        <div 
          className="flex justify-between items-center p-4 bg-gray-100 rounded-t cursor-pointer"
          onClick={() => setStatsExpanded(!statsExpanded)}
        >
          <h3 className="text-lg font-semibold">Summary Statistics</h3>
          <ChevronDown className={`w-5 h-5 transition-transform ${statsExpanded ? 'rotate-180' : ''}`} />
        </div>
        
        {statsExpanded && (
          <div className="p-4 border border-gray-200 rounded-b grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-blue-700">Salary Deposits</h4>
              <p className="text-sm text-gray-600">Total Transactions: {stats.salary.transaction_count}</p>
              <p className="text-2xl font-bold mt-2">{formatCurrency(stats.salary.total_amount)}</p>
              <p className="text-sm text-gray-600 mt-3">Highest Salary: {formatCurrency(stats.salary.highest_salary)}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-red-700">EMI Payments</h4>
              <p className="text-sm text-gray-600">Total Transactions: {stats.emi.transaction_count}</p>
              <p className="text-2xl font-bold mt-2">{formatCurrency(stats.emi.total_amount)}</p>
              <p className="text-sm text-gray-600 mt-3">Unique Loans: {stats.emi.unique_loans}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-purple-700">Credit Card Spending</h4>
              <p className="text-sm text-gray-600">Total Transactions: {stats.credit_card.transaction_count}</p>
              <p className="text-2xl font-bold mt-2">{formatCurrency(stats.credit_card.total_spent)}</p>
              <p className="text-sm text-gray-600 mt-3">Highest Outstanding: {formatCurrency(stats.credit_card.highest_outstanding)}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-green-700">Investments</h4>
              <p className="text-sm text-gray-600">Total Transactions: {stats.investments.transaction_count}</p>
              <p className="text-2xl font-bold mt-2">{formatCurrency(stats.investments.total_invested)}</p>
              <p className="text-sm text-gray-600 mt-3">Unique Folios: {stats.investments.unique_folios}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-teal-700">Insurance Payments</h4>
              <p className="text-sm text-gray-600">Total Transactions: {stats.insurance.transaction_count}</p>
              <p className="text-2xl font-bold mt-2">{formatCurrency(stats.insurance.total_amount)}</p>
              <p className="text-sm text-gray-600 mt-3">Unique Policies: {stats.insurance.unique_policies}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-gray-700">Other Transactions</h4>
              <p className="text-sm text-gray-600">Total Transactions: {stats.general.transaction_count}</p>
              <p className="text-2xl font-bold mt-2">{formatCurrency(stats.general.total_amount)}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h4 className="text-lg font-medium text-orange-700">Total Customers</h4>
              <p className="text-2xl font-bold mt-2">{summaryData.total_customers}</p>
              <p className="text-sm text-gray-600 mt-3">Total Transactions: {summaryData.total_transactions}</p>
            </div>
          </div>
        )}
      </div>
    );
  };


  const getTableHeaders = () => {
    const allFields = new Set();
    messagesByType.forEach(msg => {
      if (selectedType === 'PROMOTIONAL' && msg.important_points) {
        allFields.add('important_points');
      } else if (msg.extracted_data) {
        Object.keys(msg.extracted_data).forEach(field => allFields.add(field));
      }
    });
    return Array.from(allFields);
  };


  const renderMessageTypeAnalytics = () => {
    return (
      <div className="mb-6">
        <div 
          className="flex justify-between items-center p-4 bg-gray-100 rounded-t cursor-pointer"
          onClick={() => setAnalyticsExpanded(!analyticsExpanded)}
        >
          <h3 className="text-lg font-semibold">Message Type Analytics</h3>
          <ChevronDown className={`w-5 h-5 transition-transform ${analyticsExpanded ? 'rotate-180' : ''}`} />
        </div>
        
        {analyticsExpanded && (
          <div className="border border-gray-200 rounded-b p-4">
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-600 mb-2">Message Type Distribution</h4>
              <canvas id="messageTypeChart" className="max-w-full"></canvas>
            </div>
            <div>
              <label htmlFor="messageType" className="block text-sm font-medium text-gray-700 mb-2">
                Select Message Type
              </label>
              <select
                id="messageType"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none"
              >
                <option value="">Select a type</option>
                {Object.keys(messageTypeCounts).map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            {selectedType && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Messages for {selectedType}</h4>
                {messagesLoading ? (
                  <p className="text-gray-500">Loading...</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Original Message</th>
                          {getTableHeaders().map(field => (
                            <th key={field} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              {field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {messagesByType.map((msg, index) => (
                          <tr key={index}>
                            <td className="px-6 py-4 text-sm text-gray-500 max-w-md break-words">{msg.message}</td>
                            {getTableHeaders().map(field => (
                              <td key={field} className="px-6 py-4 text-sm text-gray-500">
                                {field === 'important_points' && selectedType === 'PROMOTIONAL'
                                  ? (msg.important_points ? msg.important_points.join(', ') : 'N/A')
                                  : (msg.extracted_data && msg.extracted_data[field] != null 
                                      ? String(msg.extracted_data[field]) 
                                      : 'N/A')}
                              </td>
                            ))}
                          </tr>
                        ))}
                        {messagesByType.length === 0 && (
                          <tr>
                            <td colSpan={getTableHeaders().length + 1} className="px-6 py-4 text-center text-sm text-gray-500">
                              No messages for this type
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };


  const renderRecentMessages = () => {
    return (
      <div className="mb-6">
        <div 
          className="flex justify-between items-center p-4 bg-gray-100 rounded-t cursor-pointer"
          onClick={() => setMessagesExpanded(!messagesExpanded)}
        >
          <h3 className="text-lg font-semibold">Recent Processed Transactions</h3>
          <ChevronDown className={`w-5 h-5 transition-transform ${messagesExpanded ? 'rotate-180' : ''}`} />
        </div>
        
        {messagesExpanded && (
          <div className="border border-gray-200 rounded-b overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Processed At</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {summaryData.recent_transactions.map((txn, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{txn.customer_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                          ${txn.message_type === 'SALARY_CREDIT' ? 'bg-blue-100 text-blue-800' : 
                            txn.message_type === 'EMI_PAYMENT' ? 'bg-red-100 text-red-800' : 
                            txn.message_type === 'CREDIT_CARD_TRANSACTION' ? 'bg-purple-100 text-purple-800' : 
                            txn.message_type === 'SIP_INVESTMENT' ? 'bg-green-100 text-green-800' : 
                            txn.message_type === 'INSURANCE_PAYMENT' ? 'bg-teal-100 text-teal-800' : 
                            txn.message_type === 'OTHER_FINANCIAL' ? 'bg-gray-100 text-gray-600' : 
                            'bg-gray-100 text-gray-800'}`}>
                          {txn.message_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{formatCurrency(txn.amount)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(txn.created_at)}</td>
                    </tr>
                  ))}
                  {summaryData.recent_transactions.length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-6 py-4 text-center text-sm text-gray-500">
                        No transactions processed yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCustomerTransactions = () => {
    const messageTypes = [
      'SALARY_CREDIT', 'EMI_PAYMENT', 'CREDIT_CARD_TRANSACTION',
      'SIP_INVESTMENT', 'INSURANCE_PAYMENT', 'OTHER_FINANCIAL',
      'CREDIT_TRANSACTION', 'DEBIT_TRANSACTION'
    ];

    return (
      <div className="mb-6">
        <div 
          className="flex justify-between items-center p-4 bg-gray-100 rounded-t cursor-pointer"
          onClick={() => setCustomerSectionExpanded(!customerSectionExpanded)}
        >
          <h3 className="text-lg font-semibold">Customer Transactions</h3>
          <ChevronDown className={`w-5 h-5 transition-transform ${customerSectionExpanded ? 'rotate-180' : ''}`} />
        </div>
        
        {customerSectionExpanded && (
          <div className="p-4 border border-gray-200 rounded-b">
            {/* Customers List */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Select Customer</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {customers.map((customer) => (
                      <tr key={customer.customer_id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.customer_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.phone_number}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(customer.created_at)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => {
                              setSelectedCustomerId(customer.customer_id);
                              setTransactionsPage(1);
                              setTransactionFilterType('');
                            }}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            View Transactions
                          </button>
                        </td>
                      </tr>
                    ))}
                    {customers.length === 0 && (
                      <tr>
                        <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                          No customers found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {/* Pagination */}
              <div className="flex justify-between items-center mt-4">
                <button
                  onClick={() => setCustomersPage(prev => Math.max(prev - 1, 1))}
                  disabled={customersPage === 1}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Previous
                </button>
                <span className="text-sm text-gray-700">
                  Page {customersPage} of {Math.ceil(customersTotal / customersLimit)}
                </span>
                <button
                  onClick={() => setCustomersPage(prev => prev + 1)}
                  disabled={customersPage * customersLimit >= customersTotal}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-2" />
                </button>
              </div>
            </div>

            {/* Customer Summary and Transactions */}
            {selectedCustomerId && customerSummary && (
              <div className="mt-6">
                <h4 className="text-lg font-medium text-gray-700 mb-4">
                  Transactions for {customerSummary.customer.name} (ID: {customerSummary.customer.customer_id})
                </h4>
                {/* Transaction Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {customerSummary.message_type_stats.map(stat => (
                    <div key={stat.message_type} className="bg-white p-4 rounded shadow">
                      <h5 className={`text-lg font-medium ${
                        stat.message_type === 'SALARY_CREDIT' ? 'text-blue-700' :
                        stat.message_type === 'EMI_PAYMENT' ? 'text-red-700' :
                        stat.message_type === 'CREDIT_CARD_TRANSACTION' ? 'text-purple-700' :
                        stat.message_type === 'SIP_INVESTMENT' ? 'text-green-700' :
                        stat.message_type === 'INSURANCE_PAYMENT' ? 'text-teal-700' :
                        'text-gray-700'
                      }`}>
                        {stat.message_type.replace(/_/g, ' ')}
                      </h5>
                      <p className="text-sm text-gray-600">Total Transactions: {stat.count}</p>
                      <p className="text-2xl font-bold mt-2">{formatCurrency(stat.total_amount)}</p>
                      {stat.unique_loans > 0 && (
                        <p className="text-sm text-gray-600 mt-3">Unique Loans: {stat.unique_loans}</p>
                      )}
                      {stat.unique_folios > 0 && (
                        <p className="text-sm text-gray-600 mt-3">Unique Folios: {stat.unique_folios}</p>
                      )}
                      {stat.unique_policies > 0 && (
                        <p className="text-sm text-gray-600 mt-3">Unique Policies: {stat.unique_policies}</p>
                      )}
                      {stat.max_outstanding > 0 && (
                        <p className="text-sm text-gray-600 mt-3">Highest Outstanding: {formatCurrency(stat.max_outstanding)}</p>
                      )}
                    </div>
                  ))}
                  <div className="bg-white p-4 rounded shadow">
                    <h5 className="text-lg font-medium text-orange-700">Total Transactions</h5>
                    <p className="text-2xl font-bold mt-2">{customerSummary.total_transactions}</p>
                  </div>
                </div>
                {/* Transaction Filter and List */}
                <div className="mb-4">
                  <label htmlFor="transactionFilter" className="block text-sm font-medium text-gray-700 mb-2">
                    Filter by Transaction Type
                  </label>
                  <select
                    id="transactionFilter"
                    value={transactionFilterType}
                    onChange={(e) => {
                      setTransactionFilterType(e.target.value);
                      setTransactionsPage(1);
                    }}
                    className="block w-full max-w-xs py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none"
                  >
                    <option value="">All Types</option>
                    {messageTypes.map(type => (
                      <option key={type} value={type}>
                        {type.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Processed At</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {customerTransactions.map((txn, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                              ${txn.message_type === 'SALARY_CREDIT' ? 'bg-blue-100 text-blue-800' : 
                                txn.message_type === 'EMI_PAYMENT' ? 'bg-red-100 text-red-800' : 
                                txn.message_type === 'CREDIT_CARD_TRANSACTION' ? 'bg-purple-100 text-purple-800' : 
                                txn.message_type === 'SIP_INVESTMENT' ? 'bg-green-100 text-green-800' : 
                                txn.message_type === 'INSURANCE_PAYMENT' ? 'bg-teal-100 text-teal-800' : 
                                txn.message_type === 'OTHER_FINANCIAL' ? 'bg-gray-100 text-gray-600' : 
                                'bg-gray-100 text-gray-800'}`}>
                              {txn.message_type}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">{formatCurrency(txn.amount)}</td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {txn.loan_reference && <span>Loan: {txn.loan_reference}<br /></span>}
                            {txn.folio_number && <span>Folio: {txn.folio_number}<br /></span>}
                            {txn.policy_number && <span>Policy: {txn.policy_number}<br /></span>}
                            {txn.total_outstanding && <span>Outstanding: {formatCurrency(txn.total_outstanding)}</span>}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(txn.created_at)}</td>
                        </tr>
                      ))}
                      {customerTransactions.length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-6 py-4 text-center text-sm text-gray-500">
                            No transactions found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                {/* Transaction Pagination */}
                <div className="flex justify-between items-center mt-4">
                  <button
                    onClick={() => setTransactionsPage(prev => Math.max(prev - 1, 1))}
                    disabled={transactionsPage === 1}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    <ChevronLeft className="w-4 h-4 mr-2" />
                    Previous
                  </button>
                  <span className="text-sm text-gray-700">
                    Page {transactionsPage} of {Math.ceil(transactionsTotal / transactionsLimit)}
                  </span>
                  <button
                    onClick={() => setTransactionsPage(prev => prev + 1)}
                    disabled={transactionsPage * transactionsLimit >= transactionsTotal}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="p-6 bg-blue-600 text-white">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Financial SMS Analyzer Dashboard</h2>
            <button 
              onClick={handleRefresh}
              className="p-2 rounded hover:bg-blue-700 transition-colors"
              title="Refresh dashboard"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
          <p className="mt-1 opacity-80">Upload and analyze financial SMS messages</p>
        </div>
        
        <div className="p-6">
          <div className="mb-6 border rounded-lg overflow-hidden">
            <div className="bg-gray-100 p-4 border-b">
              <h3 className="text-lg font-medium">Upload Messages</h3>
            </div>
            <div className="p-4">
              <div className="mb-5">
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select CSV File
                    </label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                      <div className="space-y-1 text-center">
                        <Upload className="mx-auto h-12 w-12 text-gray-400" />
                        <div className="flex text-sm text-gray-600">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500"
                          >
                            <span>Upload a file</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              className="sr-only"
                              accept=".csv"
                              onChange={handleFileChange}
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">CSV files only</p>
                      </div>
                    </div>
                    {selectedFile && (
                      <p className="mt-2 text-sm text-gray-500">
                        Selected file: {selectedFile.name}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col space-y-2">
                    <button
                      onClick={handleFileUpload}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                      disabled={!selectedFile || processing}
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Upload & Process
                    </button>
                    <button
                      onClick={handleProcessExistingFile}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                      disabled={processing}
                    >
                      <FilePlus className="w-4 h-4 mr-2" />
                      Process Existing File
                    </button>
                  </div>
                </div>
              </div>
              
              {uploadResponse && (
                <div className={`p-4 rounded mb-4 ${
                  uploadResponse.status === 'accepted' || uploadResponse.status === 'success' 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex items-start">
                    {(uploadResponse.status === 'accepted' || uploadResponse.status === 'success') ? (
                      <Check className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
                    ) : (
                      <X className="w-5 h-5 text-red-500 mr-2 mt-0.5" />
                    )}
                    <p className={
                      (uploadResponse.status === 'accepted' || uploadResponse.status === 'success') 
                        ? 'text-green-700' 
                        : 'text-red-700'
                    }>
                      {uploadResponse.message}
                    </p>
                  </div>
                </div>
              )}
              
              {processing && renderProgressBar()}
            </div>
          </div>
          
          {renderSummaryStats()}
          {renderMessageTypeAnalytics()}
          {renderRecentMessages()}
          {renderCustomerTransactions()}
        </div>
      </div>
    </div>
  );
};

export default FinancialDashboard;
