import React from 'react';
import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

const CustomerTransactions = ({
  customers,
  customersTotal,
  customersPage,
  customersLimit,
  selectedCustomerId,
  customerSummary,
  customerTransactions,
  transactionsTotal,
  transactionsPage,
  transactionsLimit,
  transactionFilterType,
  setCustomersPage,
  setSelectedCustomerId,
  setTransactionsPage,
  setTransactionFilterType,
  customerSectionExpanded,
  setCustomerSectionExpanded,
  formatCurrency,
  formatDate,
}) => {
  const messageTypes = [
    'SALARY_CREDIT', 'EMI_PAYMENT', 'CREDIT_CARD_TRANSACTION',
    'SIP_INVESTMENT', 'INSURANCE_PAYMENT', 'OTHER_FINANCIAL',
    'CREDIT_TRANSACTION', 'DEBIT_TRANSACTION'
  ];

  return (
    <div className="mb-6 card">
      <div
        className="flex justify-between items-center p-4 bg-gray-100 rounded-t cursor-pointer"
        onClick={() => setCustomerSectionExpanded(!customerSectionExpanded)}
      >
        <h3 className="text-lg font-semibold">Customer Transactions</h3>
        <ChevronDown className={`w-5 h-5 transition-transform ${customerSectionExpanded ? 'rotate-180' : ''}`} />
      </div>
      {customerSectionExpanded && (
        <div className="p-4 border border-gray-200 rounded-b">
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
          {selectedCustomerId && customerSummary && (
            <div className="mt-6">
              <h4 className="text-lg font-medium text-gray-700 mb-4">
                Transactions for {customerSummary.customer.name} (ID: {customerSummary.customer.customer_id})
              </h4>
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

export default CustomerTransactions;