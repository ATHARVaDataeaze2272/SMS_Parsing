import React from 'react';
import { RefreshCw } from 'lucide-react';

const Header = ({ onRefresh }) => {
  return (
    <div className="p-6 bg-blue-600 text-white">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold title">Financial SMS Analyzer Dashboard</h2>
          <p className="mt-1 opacity-80">Upload and analyze financial SMS messages</p>
        </div>
        <button
          onClick={onRefresh}
          className="p-2 rounded hover:bg-blue-700 transition-colors"
          title="Refresh dashboard"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default Header;