import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import FileUploader from './components/FileUploader';
import SummaryStats from './components/SummaryStats';
import MessageTypeAnalytics from './components/MessageTypeAnalytics';
import RecentMessages from './components/RecentMessages';
import CustomerTransactions from './components/CustomerTransactions';
import './MessageAnalyzer.css';

const FinancialDashboard = () => {
  const API_BASE_URL = '/api';
  //const API_BASE_URL = 'http://localhost:8000';
  // const API_BASE_URL ='https://sms-parsing.onrender.com';

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

  useEffect(() => {
    fetchDashboardData();
    fetchCustomers();
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);

  useEffect(() => {
    fetchCustomers();
  }, [customersPage]);

  useEffect(() => {
    if (selectedCustomerId) {
      fetchCustomerSummary();
      fetchCustomerTransactions();
    }
  }, [selectedCustomerId, transactionsPage, transactionFilterType]);

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

  useEffect(() => {
    if (selectedType) {
      fetchMessagesByType();
    }
  }, [selectedType]);

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
      console.log('Fetched processing status:', status);
      setProcessingStatus(status);
    } catch (error) {
      console.error('Error fetching processing status:', error);
    }
  };
  
  useEffect(() => {
    if (processing) {
      console.log('Starting polling for processing status');
      const interval = setInterval(() => {
        console.log('Polling /processing-status');
        fetchProcessingStatus().then(() => {
          console.log('Processing status:', processingStatus);
          if (processingStatus.status === 'completed' || processingStatus.status === 'error') {
            console.log('Stopping polling, status:', processingStatus.status);
            setProcessing(false);
            fetchDashboardData();
            fetchCustomers();
            clearInterval(interval);
          }
        });
      }, 2000);
      setRefreshInterval(interval);
      return () => {
        console.log('Clearing polling interval');
        clearInterval(interval);
      };
    }
  }, [processing, processingStatus.status]);

  const fetchMessagesByType = async () => {
    setMessagesLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/messages_demo?message_type=${encodeURIComponent(selectedType)}`
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

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && !file.name.endsWith('.json')) {
      alert('Please select a JSON file');
      return;
    }
    setSelectedFile(file);
  };

 

  const handleFileUpload = async () => {
    if (!selectedFile) {
      alert('Please select a JSON file first');
      return;
    }
  
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
  
      const response = await fetch(`${API_BASE_URL}/upload-json`, {
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
        console.log('Setting processing to true');
        setProcessing(true);
        fetchProcessingStatus();
      }
    } catch (error) {
      console.error('Error uploading JSON file:', error);
      setUploadResponse({
        status: 'error',
        message: `Error uploading JSON file: ${error.message}`
      });
    }
  };

  const handleProcessExistingFile = async () => {
    const filePath = prompt('Enter the path to the JSON file on the server:');
    if (!filePath) return;

    if (!filePath.endsWith('.json')) {
      alert('Please provide a path to a JSON file');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/upload-json`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_path: filePath
        })
      });

      if (!response.ok) throw new Error('Processing failed');
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
      console.error('Error processing JSON file:', error);
      setUploadResponse({
        status: 'error',
        message: `Error processing JSON file: ${error.message}`
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

  const getTableHeaders = () => {
    const allFields = new Set();
    messagesByType.forEach(msg => {
      if (msg.important_points && typeof msg.important_points === 'object') {
        Object.keys(msg.important_points).forEach(field => allFields.add(field));
      }
    });
    return Array.from(allFields);
  };

  return (
    <div className="container mx-auto px-4 py-8 analyzer-container">
      <div className="bg-white shadow-lg rounded-lg overflow-hidden card">
        <Header onRefresh={handleRefresh} />
        <div className="p-6">
          <FileUploader
            selectedFile={selectedFile}
            processing={processing}
            processingStatus={processingStatus}
            uploadResponse={uploadResponse}
            handleFileChange={handleFileChange}
            handleFileUpload={handleFileUpload}
            handleProcessExistingFile={handleProcessExistingFile}
          />
          <SummaryStats
            summaryData={summaryData}
            statsExpanded={statsExpanded}
            setStatsExpanded={setStatsExpanded}
            formatCurrency={formatCurrency}
          />
          <MessageTypeAnalytics
            messageTypeCounts={messageTypeCounts}
            selectedType={selectedType}
            messagesByType={messagesByType}
            messagesLoading={messagesLoading}
            analyticsExpanded={analyticsExpanded}
            setAnalyticsExpanded={setAnalyticsExpanded}
            setSelectedType={setSelectedType}
            getTableHeaders={getTableHeaders}
          />
          <RecentMessages
            summaryData={summaryData}
            messagesExpanded={messagesExpanded}
            setMessagesExpanded={setMessagesExpanded}
            formatCurrency={formatCurrency}
            formatDate={formatDate}
          />
          <CustomerTransactions
            customers={customers}
            customersTotal={customersTotal}
            customersPage={customersPage}
            customersLimit={customersLimit}
            selectedCustomerId={selectedCustomerId}
            customerSummary={customerSummary}
            customerTransactions={customerTransactions}
            transactionsTotal={transactionsTotal}
            transactionsPage={transactionsPage}
            transactionsLimit={transactionsLimit}
            transactionFilterType={transactionFilterType}
            setCustomersPage={setCustomersPage}
            setSelectedCustomerId={setSelectedCustomerId}
            setTransactionsPage={setTransactionsPage}
            setTransactionFilterType={setTransactionFilterType}
            customerSectionExpanded={customerSectionExpanded}
            setCustomerSectionExpanded={setCustomerSectionExpanded}
            formatCurrency={formatCurrency}
            formatDate={formatDate}
          />
        </div>
      </div>
    </div>
  );
};

export default FinancialDashboard;