// import React, { useEffect, useRef } from 'react';
// import { ChevronDown } from 'lucide-react';
// import Chart from 'chart.js/auto';

// const MessageTypeAnalytics = ({
//   messageTypeCounts,
//   selectedType,
//   messagesByType,
//   messagesLoading,
//   analyticsExpanded,
//   setAnalyticsExpanded,
//   setSelectedType,
//   getTableHeaders,
// }) => {
//   const chartRef = useRef(null);
//   const chartInstanceRef = useRef(null);

//   // Render chart when analyticsExpanded is true or messageTypeCounts changes
//   useEffect(() => {
//     if (!analyticsExpanded || Object.keys(messageTypeCounts).length === 0) {
//       // Destroy chart if section is closed
//       if (chartInstanceRef.current) {
//         chartInstanceRef.current.destroy();
//         chartInstanceRef.current = null;
//       }
//       return;
//     }

//     // Use requestAnimationFrame to ensure canvas is ready
//     const renderId = requestAnimationFrame(() => {
//       renderChart();
//     });

//     return () => {
//       cancelAnimationFrame(renderId);
//       if (chartInstanceRef.current) {
//         chartInstanceRef.current.destroy();
//         chartInstanceRef.current = null;
//       }
//     };
//   }, [analyticsExpanded, messageTypeCounts]);

//   const renderChart = () => {
//     const ctx = chartRef.current?.getContext('2d');
//     if (!ctx) {
//       console.error('Canvas context not found for messageTypeChart');
//       return;
//     }

//     // Prevent re-rendering if chart already exists
//     if (chartInstanceRef.current) {
//       chartInstanceRef.current.destroy();
//       chartInstanceRef.current = null;
//     }

//     const labels = Object.keys(messageTypeCounts);
//     const data = Object.values(messageTypeCounts);

//     chartInstanceRef.current = new Chart(ctx, {
//       type: 'bar',
//       data: {
//         labels: labels,
//         datasets: [{
//           label: 'Message Type Counts',
//           data: data,
//           backgroundColor: [
//             '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
//             '#9966FF', '#FF9F40', '#C9CBCF', '#7EC850'
//           ],
//           borderColor: [
//             '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
//             '#9966FF', '#FF9F40', '#C9CBCF', '#7EC850'
//           ],
//           borderWidth: 1
//         }]
//       },
//       options: {
//         scales: {
//           y: {
//             beginAtZero: true,
//             title: {
//               display: true,
//               text: 'Number of Messages'
//             }
//           },
//           x: {
//             title: {
//               display: true,
//               text: 'Message Type'
//             }
//           }
//         },
//         plugins: {
//           title: {
//             display: true,
//             text: 'Messages by Type'
//           }
//         },
//         animation: {
//           duration: 500 // Reduce animation duration for faster rendering
//         }
//       }
//     });
//   };

//   const tableHeaders = getTableHeaders();

//   return (
//     <div className="mb-6 card">
//       <div
//         className="flex justify-between items-center p-4 bg-gray-100 rounded-t cursor-pointer"
//         onClick={() => setAnalyticsExpanded(!analyticsExpanded)}
//       >
//         <h3 className="text-lg font-semibold">Message Type Analytics</h3>
//         <ChevronDown className={`w-5 h-5 transition-transform ${analyticsExpanded ? 'rotate-180' : ''}`} />
//       </div>
//       {analyticsExpanded && (
//         <div className="border border-gray-200 rounded-b p-4">
//           <div className="mb-4">
//             <h4 className="text-sm font-medium text-gray-600 mb-2">Message Type Distribution</h4>
//             <canvas id="messageTypeChart" ref={chartRef} className="max-w-full" />
//           </div>
//           <div>
//             <label htmlFor="messageType" className="block text-sm font-medium text-gray-700 mb-2">
//               Select Message Type
//             </label>
//             <select
//               id="messageType"
//               value={selectedType}
//               onChange={(e) => setSelectedType(e.target.value)}
//               className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none"
//             >
//               <option value="">Select a type</option>
//               {Object.keys(messageTypeCounts).map(type => (
//                 <option key={type} value={type}>{type}</option>
//               ))}
//             </select>
//           </div>
//           {selectedType && (
//             <div className="mt-4">
//               <h4 className="text-sm font-medium text-gray-700 mb-2">Messages for {selectedType}</h4>
//               {messagesLoading ? (
//                 <p className="text-gray-500">Loading...</p>
//               ) : (
//                 <div className="overflow-x-auto">
//                   <table className="min-w-full divide-y divide-gray-200">
//                     <thead className="bg-gray-50">
//                       <tr>
//                         <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
//                         {tableHeaders.map(field => (
//                           <th key={field} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
//                             {field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
//                           </th>
//                         ))}
//                       </tr>
//                     </thead>
//                     <tbody className="bg-white divide-y divide-gray-200">
//                       {messagesByType.map((msg, index) => (
//                         <tr key={index}>
//                           <td className="px-6 py-4 text-sm text-gray-500 max-w-md break-words">{msg.message}</td>
//                           {tableHeaders.map(field => (
//                             <td key={field} className="px-6 py-4 text-sm text-gray-500">
//                               {msg.important_points && msg.important_points[field] != null
//                                 ? String(msg.important_points[field])
//                                 : 'N/A'}
//                             </td>
//                           ))}
//                         </tr>
//                       ))}
//                       {messagesByType.length === 0 && (
//                         <tr>
//                           <td colSpan={tableHeaders.length + 1} className="px-6 py-4 text-center text-sm text-gray-500">
//                             No messages for this type
//                           </td>
//                         </tr>
//                       )}
//                     </tbody>
//                   </table>
//                 </div>
//               )}
//             </div>
//           )}
//         </div>
//       )}
//     </div>
//   );
// };

// export default MessageTypeAnalytics;







import React, { useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';
import Chart from 'chart.js/auto';
import * as XLSX from 'xlsx';

const MessageTypeAnalytics = ({
  messageTypeCounts,
  selectedType,
  messagesByType,
  messagesLoading,
  analyticsExpanded,
  setAnalyticsExpanded,
  setSelectedType,
  getTableHeaders,
}) => {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  // Render chart when analyticsExpanded is true or messageTypeCounts changes
  useEffect(() => {
    if (!analyticsExpanded || Object.keys(messageTypeCounts).length === 0) {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
      return;
    }

    const renderId = requestAnimationFrame(() => {
      renderChart();
    });

    return () => {
      cancelAnimationFrame(renderId);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [analyticsExpanded, messageTypeCounts]);

  const renderChart = () => {
    const ctx = chartRef.current?.getContext('2d');
    if (!ctx) {
      console.error('Canvas context not found for messageTypeChart');
      return;
    }

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
      chartInstanceRef.current = null;
    }

    const labels = Object.keys(messageTypeCounts);
    const data = Object.values(messageTypeCounts);

    chartInstanceRef.current = new Chart(ctx, {
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
        },
        animation: {
          duration: 500
        }
      }
    });
  };

  const handleDownloadExcel = () => {
    if (!messagesByType.length) {
      alert('No messages to download');
      return;
    }

    const headers = getTableHeaders();
    const worksheetData = messagesByType.map((msg, index) => {
      const row = { Message: msg.message || 'N/A' };
      headers.forEach(field => {
        row[field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())] =
          msg.important_points && msg.important_points[field] != null
            ? String(msg.important_points[field])
            : 'N/A';
      });
      return row;
    });

    const worksheet = XLSX.utils.json_to_sheet(worksheetData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Messages');
    XLSX.writeFile(workbook, `${selectedType}_messages.xlsx`);
  };

  const tableHeaders = getTableHeaders();

  return (
    <div className="mb-6 card">
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
            <canvas id="messageTypeChart" ref={chartRef} className="max-w-full" />
          </div>
          <div>
            <label htmlFor="messageType" className="block text-sm font-medium text-gray-700 mb-2">
              Select Message Type
            </label>
            <select
              id="messageType"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="block w-full py-2 px-3 border border-gray-300 bg PROCUREMENT-white rounded-md shadow-sm focus:outline-none"
            >
              <option value="">Select a type</option>
              {Object.keys(messageTypeCounts).map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          {selectedType && (
            <div className="mt-4">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-sm font-medium text-gray-700">Messages for {selectedType}</h4>
                <button
                  onClick={handleDownloadExcel}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                >
                  Download as Excel
                </button>
              </div>
              {messagesLoading ? (
                <p className="text-gray-500">Loading...</p>
              ) : (
                <div className="overflow-y-auto max-h-96 border border-gray-200 rounded">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className ="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                        {tableHeaders.map(field => (
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
                          {tableHeaders.map(field => (
                            <td key={field} className="px-6 py-4 text-sm text-gray-500">
                              {msg.important_points && msg.important_points[field] != null
                                ? String(msg.important_points[field])
                                : 'N/A'}
                            </td>
                          ))}
                        </tr>
                      ))}
                      {messagesByType.length === 0 && (
                        <tr>
                          <td colSpan={tableHeaders.length + 1} className="px-6 py-4 text-center text-sm text-gray-500">
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

export default MessageTypeAnalytics;