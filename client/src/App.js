import React, { useEffect, useState, useCallback } from 'react';
import ChatWidget from './ChatWidget';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
// import { Card } from 'shadcn-ui'; // Uncomment if shadcn/ui is installed
// import { motion } from 'framer-motion';
import './App.css';

const MCP_API = 'http://localhost:8000';

function App() {
  const [username, setUsername] = useState('slowbluesman'); // Default to a real user
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(1); // Time range in years (1, 2, 5, 0 for all time)

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Use the new dashboard endpoint that includes CrewAI insights
      const dashboardData = await fetch(`${MCP_API}/user/${username}/dashboard`).then(r => r.json());
      setDashboard(dashboardData);
    } catch (err) {
      setError(`Failed to fetch dashboard data: ${err.message}`);
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleUsernameChange = (e) => {
    if (e.key === 'Enter') {
      setUsername(e.target.value);
    }
  };

  // Format rating history data for charts
  const formatChartData = (history, years = 1) => {
    if (!history || !Array.isArray(history)) return [];
    
    const chartData = [];
    let cutoffDate = null;
    
    if (years > 0) {
      cutoffDate = new Date();
      cutoffDate.setFullYear(cutoffDate.getFullYear() - years);
    }
    
    // Find the longest time series to determine chart length
    let maxLength = 0;
    history.forEach(cat => {
      if (cat.points && cat.points.length > maxLength) {
        maxLength = cat.points.length;
      }
    });
    
    // Create data points for each time control
    for (let i = 0; i < maxLength; i++) {
      const dataPoint = { index: i };
      let hasData = false;
      
      // Process each category from the history
      history.forEach(category => {
        if (category.points && category.points[i]) {
          const point = category.points[i];
          const date = new Date(point[0], point[1], point[2]);
          
          // Only include data from the specified time range (or all time if years = 0)
          if (!cutoffDate || date >= cutoffDate) {
            // Create a safe key for the rating (handle special characters)
            const safeKey = category.name.replace(/[^a-zA-Z0-9]/g, '') + 'Rating';
            dataPoint[safeKey] = point[3];
            dataPoint[`${safeKey}Date`] = date.toLocaleDateString();
            
            // Store the actual date for sorting
            if (!dataPoint.date) {
              dataPoint.date = date;
            }
            hasData = true;
          }
        }
      });
      
      if (hasData) {
        chartData.push(dataPoint);
      }
    }
    
    // Sort by actual date to ensure chronological order
    chartData.sort((a, b) => a.date - b.date);
    
    return chartData;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading chess data and generating insights...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">{error}</div>
          <button 
            onClick={fetchDashboard}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const chartData = formatChartData(dashboard?.ratingHistory, timeRange);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Username Input */}
        <div className="bg-white rounded shadow p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Lichess Username:
          </label>
          <input
            type="text"
            defaultValue={username}
            onKeyPress={handleUsernameChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter Lichess username and press Enter"
          />
        </div>

        {/* User Overview */}
        {dashboard && (
          <div className="flex items-center space-x-4 bg-white rounded shadow p-4">
            {dashboard?.overview?.avatar && (
              <img
                src={dashboard.overview.avatar}
                alt="avatar"
              className="w-16 h-16 rounded-full shadow"
              onError={(e) => {
                e.target.src = 'https://lichess.org/assets/images/placeholder.256.png';
              }}
            />
            )}
              <div>
              <h1 className="text-2xl font-bold">{dashboard.overview.username}</h1>
              <div className="flex flex-wrap gap-2 mt-2">
                {dashboard.overview.ratings && Object.entries(dashboard.overview.ratings).map(([cat, val]) => {
                  // Show all ratings, but style provisional ones differently
                  if (val && val.rating) {
                    const isProvisional = val.prov === true;
                    const hasGames = val.games > 0;
                    
                    return (
                      <span
                        key={cat}
                        className={`rounded px-3 py-1 shadow text-sm font-mono ${
                          isProvisional
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                            : hasGames
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-600'
                        }`}
                        title={isProvisional ? 'Provisional Rating' : `${val.games} games`}
                      >
                        {cat}: {val.rating}
                        {isProvisional && ' (P)'}
                      </span>
                    );
                  }
                  return null;
                })}
          </div>
                        </div>
                      </div>
        )}

        {/* Rating History Charts */}
        {dashboard && chartData.length > 0 && (
          <div className="bg-white rounded shadow p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Rating History</h2>
              
              {/* Time Range Filter */}
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-600">Time Range:</label>
                <select 
                  className="px-3 py-1 border border-gray-300 rounded text-sm"
                  onChange={(e) => {
                    const years = parseInt(e.target.value);
                    setTimeRange(years);
                    // Force re-render by updating state
                    setDashboard({ ...dashboard, _refresh: Date.now() });
                  }}
                  defaultValue="1"
                >
                  <option value="1">Past Year</option>
                  <option value="2">Past 2 Years</option>
                  <option value="5">Past 5 Years</option>
                  <option value="0">All Time</option>
                </select>
      </div>
    </div>
   
            {/* Debug info - remove this later */}
            <div className="mb-4 p-2 bg-gray-100 rounded text-xs">
              <strong>Debug - Chart Data Keys:</strong> {Object.keys(chartData[0] || {}).join(', ')}
              <br />
              <strong>Data Points:</strong> {chartData.length} | <strong>Time Range:</strong> {timeRange === 0 ? 'All Time' : `${timeRange} Year${timeRange > 1 ? 's' : ''}`}
            </div>
            
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    type="category"
                    tickFormatter={(value) => {
                      if (value instanceof Date) {
                        return value.toLocaleDateString('en-US', {
                          month: 'short',
                          year: '2-digit'
                        });
                      }
                      return value;
                    }}
                    interval="preserveStartEnd"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis domain={['dataMin - 50', 'dataMax + 50']} />
                  <Tooltip 
                    labelFormatter={(value) => {
                      if (value instanceof Date) {
                        return value.toLocaleDateString('en-US', { 
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        });
                      }
                      return value;
                    }}
                  />
                  <Legend />
                  
                  {/* Dynamically generate chart lines based on available data */}
                  {chartData.length > 0 && Object.keys(chartData[0])
                    .filter(key => key.endsWith('Rating'))
                    .map((ratingKey, index) => {
                      const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#ff0000', '#00ff00'];
                      const timeControl = ratingKey.replace('Rating', '');
                      return (
                        <Line 
                          key={ratingKey}
                          type="monotone"
                          dataKey={ratingKey}
                          stroke={colors[index % colors.length]}
                          strokeWidth={2}
                          dot={{ r: 4 }}
                          name={timeControl}
                        />
                      );
                    })}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Recent Games Table */}
        {dashboard && (
          <div className="bg-white rounded shadow p-4">
            <h2 className="text-lg font-semibold mb-2">Recent Games</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="p-2">Opponent</th>
                  <th className="p-2">Result</th>
                  <th className="p-2">Opening</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.recentGames && dashboard.recentGames.map((g, i) => (
                  <tr key={g.id || i} className="border-b">
                    <td className="p-2">
                      {g.players?.white?.user?.name === dashboard.overview.username
                        ? g.players?.black?.user?.name
                        : g.players?.white?.user?.name}
                    </td>
                    <td className="p-2">
                      {g.winner ? (g.winner === 'white' ? 'White' : 'Black') : 'Draw'}
                    </td>
                    <td className="p-2">{g.opening?.name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* AI-Generated Insights Section */}
        {dashboard && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg shadow-lg p-6 border border-blue-200">
            <div className="flex items-center mb-6">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-full mr-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-800">🎯 Elite Chess Coaching Insights</h2>
                <p className="text-gray-600">Personalized analysis from your AI Grandmaster coach</p>
              </div>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              {dashboard.insights && dashboard.insights.map((insight, i) => (
                <div key={i} className={`rounded-lg p-5 shadow-md border-l-4 ${
                  insight.type === 'success' ? 'bg-green-50 border-green-400' :
                  insight.type === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                  insight.type === 'strategy' ? 'bg-purple-50 border-purple-400' :
                  insight.type === 'performance' ? 'bg-blue-50 border-blue-400' :
                  insight.type === 'opening' ? 'bg-orange-50 border-orange-400' :
                  insight.type === 'development' ? 'bg-indigo-50 border-indigo-400' :
                  insight.type === 'psychology' ? 'bg-pink-50 border-pink-400' :
                  'bg-gray-50 border-gray-400'
                }`}>
                  
                  <div className="flex items-start mb-3">
                    <div className={`p-2 rounded-full mr-3 ${
                      insight.type === 'success' ? 'bg-green-100' :
                      insight.type === 'warning' ? 'bg-yellow-100' :
                      insight.type === 'strategy' ? 'bg-purple-100' :
                      insight.type === 'performance' ? 'bg-blue-100' :
                      insight.type === 'opening' ? 'bg-orange-100' :
                      insight.type === 'development' ? 'bg-indigo-100' :
                      insight.type === 'psychology' ? 'bg-pink-100' :
                      'bg-gray-100'
                    }`}>
                      {insight.type === 'success' && <span className="text-green-600 text-lg">🚀</span>}
                      {insight.type === 'warning' && <span className="text-yellow-600 text-lg">⚠️</span>}
                      {insight.type === 'strategy' && <span className="text-purple-600 text-lg">🎯</span>}
                      {insight.type === 'performance' && <span className="text-blue-600 text-lg">📊</span>}
                      {insight.type === 'opening' && <span className="text-orange-600 text-lg">♟️</span>}
                      {insight.type === 'development' && <span className="text-indigo-600 text-lg">🎭</span>}
                      {insight.type === 'psychology' && <span className="text-pink-600 text-lg">🧠</span>}
                      {!['success', 'warning', 'strategy', 'performance', 'opening', 'development', 'psychology'].includes(insight.type) && 
                        <span className="text-gray-600 text-lg">ℹ️</span>}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold text-lg text-gray-800 mb-2">{insight.title}</h3>
                      <p className="text-gray-700 mb-3 leading-relaxed">{insight.message}</p>
                      
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <div className="flex items-center mb-2">
                          <svg className="w-4 h-4 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-sm font-semibold text-blue-800">Action Plan</span>
                        </div>
                        <p className="text-sm text-gray-700 font-medium">{insight.action}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center">
                <div className="bg-gradient-to-r from-green-500 to-blue-500 p-2 rounded-full mr-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800">💡 Pro Tip</h4>
                  <p className="text-sm text-gray-600">Review these insights weekly and track your progress. Remember, chess improvement is a marathon, not a sprint!</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <ChatWidget />
    </div>
   
  );
}

export default App;

