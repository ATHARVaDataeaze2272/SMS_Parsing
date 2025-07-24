import React from 'react';
import { ChevronDown } from 'lucide-react';

const SummaryStats = ({ summaryData, statsExpanded, setStatsExpanded, formatCurrency }) => {
  const aggregateStats = () => {
    const stats = {
      salary: { transaction_count: 0, total_amount: 0, highest_salary: 0 },
      emi: { transaction_count: 0, total_amount: 0, unique_loans: 0 },
      credit_card: { transaction_count: 0, total_spent: 0, highest_outstanding: 0 },
      investments: { transaction_count: 0, total_invested: 0, unique_folios: 0 },
      insurance: { transaction_count: 0, total_amount: 0, unique_policies: 0 },
      credit: { transaction_count: 0, total_amount: 0 },
      debit: { transaction_count: 0, total_amount: 0 },
      other: { transaction_count: 0, total_amount: 0 },
    };

    summaryData.message_type_stats.forEach(stat => {
      const amount = Number(stat.total_amount) || 0;
      switch (stat.message_type ? stat.message_type.toUpperCase() : '') {
        case 'SALARY_CREDIT':
          stats.salary.transaction_count = stat.count;
          stats.salary.total_amount = amount;
          //stats.salary.highest_salary = amount / Math.max(stat.count, 1);
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
        case 'CREDIT_TRANSACTION':
          stats.credit.transaction_count = stat.count;
          stats.credit.total_amount = amount;
          break;
        case 'DEBIT_TRANSACTION':
          stats.debit.transaction_count = stat.count;
          stats.debit.total_amount = amount;
          break;
        case 'OTHER_FINANCIAL':
          stats.other.transaction_count = stat.count;
          stats.other.total_amount = amount;
          break;
        default:
          stats.other.transaction_count += stat.count;
          stats.other.total_amount += amount;
          break;
      }
    });

    return stats;
  };

  const stats = aggregateStats();

  return (
    <div className="mb-6 card">
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
            {/* <p className="text-sm text-gray-600 mt-3">Highest Salary: {formatCurrency(stats.salary.highest_salary)}</p> */}
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
            <h4 className="text-lg font-medium text-indigo-700">Credit Transactions</h4>
            <p className="text-sm text-gray-600">Total Transactions: {stats.credit.transaction_count}</p>
            <p className="text-2xl font-bold mt-2">{formatCurrency(stats.credit.total_amount)}</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h4 className="text-lg font-medium text-yellow-700">Debit Transactions</h4>
            <p className="text-sm text-gray-600">Total Transactions: {stats.debit.transaction_count}</p>
            <p className="text-2xl font-bold mt-2">{formatCurrency(stats.debit.total_amount)}</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h4 className="text-lg font-medium text-gray-700">Other Transactions</h4>
            <p className="text-sm text-gray-600">Total Transactions: {stats.other.transaction_count}</p>
            <p className="text-2xl font-bold mt-2">{formatCurrency(stats.other.total_amount)}</p>
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

export default SummaryStats;