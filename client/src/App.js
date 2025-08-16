import React, { useEffect, useState, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
// import { Card } from 'shadcn-ui'; // Uncomment if shadcn/ui is installed
// import { motion } from 'framer-motion';
import './App.css';

const MCP_API = 'http://localhost:8000';

function App() {
  const [username, setUsername] = useState('DrNykterstein'); // Default to a real user
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
            <img src={dashboard.overview.avatar} alt="avatar" className="w-16 h-16 rounded-full shadow" />
            <div>
              <h1 className="text-2xl font-bold">{dashboard.overview.username}</h1>
              <div className="flex space-x-2 mt-1">
                {dashboard.overview.ratings && Object.entries(dashboard.overview.ratings).map(([cat, val]) => (
                  <span key={cat} className="bg-gray-100 rounded px-2 py-1 shadow text-sm font-mono">
                    {cat}: {val.rating}
                  </span>
                ))}
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
                    setDashboard({...dashboard, _refresh: Date.now()});
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
          <div className="bg-white rounded shadow p-4">
            <h2 className="text-lg font-semibold mb-2">🤖 AI-Generated Insights</h2>
            <ul className="list-disc pl-6 space-y-2">
              {dashboard.insights && dashboard.insights.map((ins, i) => (
                <li key={i} className="text-gray-700">{ins}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
