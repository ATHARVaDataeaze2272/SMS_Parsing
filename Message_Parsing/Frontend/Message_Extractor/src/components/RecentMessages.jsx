import React from 'react';
import { ChevronDown } from 'lucide-react';

const RecentMessages = ({ summaryData, messagesExpanded, setMessagesExpanded, formatCurrency, formatDate }) => {
  return (
    <div className="mb-6 card">
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

export default RecentMessages;