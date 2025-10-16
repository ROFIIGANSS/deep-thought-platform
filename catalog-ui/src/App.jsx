import { useState, useEffect } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [catalog, setCatalog] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTab, setSelectedTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchCatalog()
  }, [])

  const fetchCatalog = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE_URL}/api/catalog`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setCatalog(data)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching catalog:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return '#4ade80'
      case 'degraded':
        return '#fbbf24'
      case 'unknown':
        return '#94a3b8'
      default:
        return '#ef4444'
    }
  }

  const filterServices = (services, type) => {
    if (!services || services.length === 0) return []
    if (!searchQuery.trim()) return services

    const query = searchQuery.toLowerCase()
    
    return services.filter(service => {
      // Search in basic fields
      const matchesName = service.name?.toLowerCase().includes(query)
      const matchesId = service.id?.toLowerCase().includes(query)
      const matchesDescription = service.description?.toLowerCase().includes(query)
      const matchesDetailedDescription = service.detailed_description?.toLowerCase().includes(query)
      
      // Search in arrays
      const matchesCapabilities = service.capabilities?.some(cap => 
        cap.toLowerCase().includes(query)
      )
      const matchesTags = service.tags?.some(tag => 
        tag.toLowerCase().includes(query)
      )
      const matchesUseCases = service.use_cases?.some(useCase => 
        useCase.toLowerCase().includes(query)
      )
      
      // Search in parameters
      const matchesParameters = service.parameters?.some(param =>
        param.name?.toLowerCase().includes(query) ||
        param.description?.toLowerCase().includes(query)
      )

      return matchesName || matchesId || matchesDescription || 
             matchesDetailedDescription || matchesCapabilities || 
             matchesTags || matchesUseCases || matchesParameters
    })
  }

  const getFilteredCatalog = () => {
    if (!catalog) return null
    
    return {
      agents: filterServices(catalog.agents, 'agent'),
      tools: filterServices(catalog.tools, 'tool'),
      workers: filterServices(catalog.workers, 'worker'),
      total_services: 
        filterServices(catalog.agents, 'agent').length +
        filterServices(catalog.tools, 'tool').length +
        filterServices(catalog.workers, 'worker').length
    }
  }

  const filteredCatalog = getFilteredCatalog()

  const renderAgent = (agent) => (
    <div key={agent.id} className="card">
      <div className="card-header">
        <h3>🤖 {agent.name}</h3>
        <div className="status-badge" style={{ backgroundColor: getStatusColor(agent.status) }}>
          {agent.status}
        </div>
      </div>
      <p className="description">{agent.description}</p>
      <div className="details">
        <div className="detail-item">
          <span className="label">ID:</span>
          <span className="value">{agent.id}</span>
        </div>
        <div className="detail-item">
          <span className="label">Endpoint:</span>
          <span className="value">{agent.endpoint}</span>
        </div>
        <div className="detail-item">
          <span className="label">Instances:</span>
          <span className="value">{agent.instances}</span>
        </div>
        {agent.health && (
          <div className="detail-item">
            <span className="label">Health:</span>
            <span className="value">
              ✅ {agent.health.healthy_instances} healthy
              {agent.health.unhealthy_instances > 0 && (
                <span style={{color: '#f44336', marginLeft: '10px'}}>
                  ⚠️ {agent.health.unhealthy_instances} unhealthy
                </span>
              )}
            </span>
          </div>
        )}
        <div className="detail-item">
          <span className="label">Version:</span>
          <span className="value">{agent.version || '1.0.0'}</span>
        </div>
        <div className="detail-item">
          <span className="label">Capabilities:</span>
          <div className="tags">
            {agent.capabilities.map((cap, idx) => (
              <span key={idx} className="tag">{cap}</span>
            ))}
          </div>
        </div>
      </div>
      {agent.detailed_description && (
        <div className="info-section">
          <h4>📝 Overview</h4>
          <p>{agent.detailed_description}</p>
        </div>
      )}
      {agent.how_it_works && (
        <div className="info-section">
          <h4>⚙️ How It Works</h4>
          <pre className="info-text">{agent.how_it_works}</pre>
        </div>
      )}
      {agent.return_format && (
        <div className="info-section">
          <h4>📤 Return Format</h4>
          <pre className="info-text">{agent.return_format}</pre>
        </div>
      )}
      {agent.use_cases && agent.use_cases.length > 0 && (
        <div className="info-section">
          <h4>💡 Use Cases</h4>
          <ul className="use-cases-list">
            {agent.use_cases.map((useCase, idx) => (
              <li key={idx}>{useCase}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="parameters">
        <h4>Common Parameters:</h4>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Required</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>session_id</code></td>
              <td><code>string</code></td>
              <td>−</td>
              <td>Optional session ID for context recovery from memory store</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div className="usage-example">
        <h4>Example Request:</h4>
        <pre>{JSON.stringify({
          agent_id: agent.id,
          input: "your input text",
          parameters: {},
          session_id: "550e8400-e29b-41d4-a716-446655440000"  // Optional: for context recovery
        }, null, 2)}</pre>
      </div>
      {agent.example_response && Object.keys(agent.example_response).length > 0 && (
        <div className="usage-example">
          <h4>Example Response:</h4>
          <pre>{JSON.stringify(agent.example_response, null, 2)}</pre>
        </div>
      )}
    </div>
  )

  const renderTool = (tool) => (
    <div key={tool.id} className="card">
      <div className="card-header">
        <h3>🔧 {tool.name}</h3>
        <div className="status-badge" style={{ backgroundColor: getStatusColor(tool.status) }}>
          {tool.status}
        </div>
      </div>
      <p className="description">{tool.description}</p>
      <div className="details">
        <div className="detail-item">
          <span className="label">ID:</span>
          <span className="value">{tool.id}</span>
        </div>
        <div className="detail-item">
          <span className="label">Endpoint:</span>
          <span className="value">{tool.endpoint}</span>
        </div>
        <div className="detail-item">
          <span className="label">Instances:</span>
          <span className="value">{tool.instances}</span>
        </div>
        {tool.health && (
          <div className="detail-item">
            <span className="label">Health:</span>
            <span className="value">
              ✅ {tool.health.healthy_instances} healthy
              {tool.health.unhealthy_instances > 0 && (
                <span style={{color: '#f44336', marginLeft: '10px'}}>
                  ⚠️ {tool.health.unhealthy_instances} unhealthy
                </span>
              )}
            </span>
          </div>
        )}
        <div className="detail-item">
          <span className="label">Version:</span>
          <span className="value">{tool.version || '1.0.0'}</span>
        </div>
      </div>
      {tool.detailed_description && (
        <div className="info-section">
          <h4>📝 Overview</h4>
          <p>{tool.detailed_description}</p>
        </div>
      )}
      {tool.how_it_works && (
        <div className="info-section">
          <h4>⚙️ How It Works</h4>
          <pre className="info-text">{tool.how_it_works}</pre>
        </div>
      )}
      {tool.return_format && (
        <div className="info-section">
          <h4>📤 Return Format</h4>
          <pre className="info-text">{tool.return_format}</pre>
        </div>
      )}
      {tool.use_cases && tool.use_cases.length > 0 && (
        <div className="info-section">
          <h4>💡 Use Cases</h4>
          <ul className="use-cases-list">
            {tool.use_cases.map((useCase, idx) => (
              <li key={idx}>{useCase}</li>
            ))}
          </ul>
        </div>
      )}
      {tool.parameters.length > 0 && (
        <div className="parameters">
          <h4>Parameters:</h4>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Required</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {tool.parameters.map((param, idx) => (
                <tr key={idx}>
                  <td><code>{param.name}</code></td>
                  <td><code>{param.type}</code></td>
                  <td>{param.required ? '✓' : '−'}</td>
                  <td>{param.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="usage-example">
        <h4>Example Request:</h4>
        <pre>{JSON.stringify({
          tool_id: tool.id,
          parameters: tool.parameters.reduce((acc, param) => {
            if (param.name !== 'session_id') {  // Skip session_id from regular params
              acc[param.name] = param.type === 'int' ? 0 : 'example value'
            }
            return acc
          }, {}),
          session_id: "550e8400-e29b-41d4-a716-446655440000"  // Optional: for context recovery
        }, null, 2)}</pre>
      </div>
      {tool.example_response && Object.keys(tool.example_response).length > 0 && (
        <div className="usage-example">
          <h4>Example Response:</h4>
          <pre>{JSON.stringify(tool.example_response, null, 2)}</pre>
        </div>
      )}
    </div>
  )

  const renderWorker = (worker) => (
    <div key={worker.id} className="card">
      <div className="card-header">
        <h3>⚙️ {worker.name}</h3>
        <div className="status-badge" style={{ backgroundColor: getStatusColor(worker.status) }}>
          {worker.status}
        </div>
      </div>
      <p className="description">{worker.description}</p>
      <div className="details">
        <div className="detail-item">
          <span className="label">ID:</span>
          <span className="value">{worker.id}</span>
        </div>
        <div className="detail-item">
          <span className="label">Endpoint:</span>
          <span className="value">{worker.endpoint}</span>
        </div>
        <div className="detail-item">
          <span className="label">Instances:</span>
          <span className="value">{worker.instances}</span>
        </div>
        {worker.health && (
          <div className="detail-item">
            <span className="label">Health:</span>
            <span className="value">
              ✅ {worker.health.healthy_instances} healthy
              {worker.health.unhealthy_instances > 0 && (
                <span style={{color: '#f44336', marginLeft: '10px'}}>
                  ⚠️ {worker.health.unhealthy_instances} unhealthy
                </span>
              )}
            </span>
          </div>
        )}
        <div className="detail-item">
          <span className="label">Version:</span>
          <span className="value">{worker.version || '1.0.0'}</span>
        </div>
        <div className="detail-item">
          <span className="label">Tags:</span>
          <div className="tags">
            {worker.tags.map((tag, idx) => (
              <span key={idx} className="tag">{tag}</span>
            ))}
          </div>
        </div>
      </div>
      {worker.detailed_description && (
        <div className="info-section">
          <h4>📝 Overview</h4>
          <p>{worker.detailed_description}</p>
        </div>
      )}
      {worker.how_it_works && (
        <div className="info-section">
          <h4>⚙️ How It Works</h4>
          <pre className="info-text">{worker.how_it_works}</pre>
        </div>
      )}
      {worker.return_format && (
        <div className="info-section">
          <h4>📤 Return Format</h4>
          <pre className="info-text">{worker.return_format}</pre>
        </div>
      )}
      {worker.use_cases && worker.use_cases.length > 0 && (
        <div className="info-section">
          <h4>💡 Use Cases</h4>
          <ul className="use-cases-list">
            {worker.use_cases.map((useCase, idx) => (
              <li key={idx}>{useCase}</li>
            ))}
          </ul>
        </div>
      )}
      {worker.parameters && worker.parameters.length > 0 && (
        <div className="parameters">
          <h4>Parameters:</h4>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Required</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {worker.parameters.map((param, idx) => (
                <tr key={idx}>
                  <td><code>{param.name}</code></td>
                  <td><code>{param.type}</code></td>
                  <td>{param.required ? '✓' : '−'}</td>
                  <td>{param.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="usage-example">
        <h4>Example Request:</h4>
        <pre>{JSON.stringify({
          worker_id: worker.id,
          input: "your task input",
          parameters: worker.parameters ? worker.parameters.reduce((acc, param) => {
            if (param.name !== 'session_id') {  // Skip session_id from regular params
              acc[param.name] = param.type === 'integer' ? 0 : 'example value'
            }
            return acc
          }, {}) : {},
          session_id: "550e8400-e29b-41d4-a716-446655440000"  // Optional: for context recovery
        }, null, 2)}</pre>
      </div>
      {worker.example_response && Object.keys(worker.example_response).length > 0 && (
        <div className="usage-example">
          <h4>Example Response:</h4>
          <pre>{JSON.stringify(worker.example_response, null, 2)}</pre>
        </div>
      )}
    </div>
  )

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading catalog...</div>
      </div>
    )
  }

  if (error) {
  return (
      <div className="container">
        <div className="error">
          <h2>Error loading catalog</h2>
          <p>{error}</p>
          <button onClick={fetchCatalog}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <header className="header">
        <h1>🚀 Agent Platform Catalog</h1>
        <p>Dynamic catalog of agents, tools, and workers</p>
        <div className="stats">
          <div className="stat">
            <span className="stat-value">{catalog?.agents?.length || 0}</span>
            <span className="stat-label">Agents</span>
          </div>
          <div className="stat">
            <span className="stat-value">{catalog?.tools?.length || 0}</span>
            <span className="stat-label">Tools</span>
          </div>
          <div className="stat">
            <span className="stat-value">{catalog?.workers?.length || 0}</span>
            <span className="stat-label">Workers</span>
          </div>
          <div className="stat">
            <span className="stat-value">{catalog?.total_services || 0}</span>
            <span className="stat-label">Total Services</span>
          </div>
        </div>
        
        <div className="search-container">
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input"
              placeholder="Search services by name, description, tags, capabilities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button 
                className="clear-search"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          {searchQuery && (
            <div className="search-results-count">
              Found {filteredCatalog?.total_services || 0} service{filteredCatalog?.total_services !== 1 ? 's' : ''}
            </div>
          )}
        </div>

        <button className="refresh-btn" onClick={fetchCatalog}>
          ↻ Refresh
        </button>
      </header>

      <div className="tabs">
        <button
          className={selectedTab === 'all' ? 'tab active' : 'tab'}
          onClick={() => setSelectedTab('all')}
        >
          All Services
        </button>
        <button
          className={selectedTab === 'agents' ? 'tab active' : 'tab'}
          onClick={() => setSelectedTab('agents')}
        >
          Agents ({filteredCatalog?.agents?.length || 0})
        </button>
        <button
          className={selectedTab === 'tools' ? 'tab active' : 'tab'}
          onClick={() => setSelectedTab('tools')}
        >
          Tools ({filteredCatalog?.tools?.length || 0})
        </button>
        <button
          className={selectedTab === 'workers' ? 'tab active' : 'tab'}
          onClick={() => setSelectedTab('workers')}
        >
          Workers ({filteredCatalog?.workers?.length || 0})
        </button>
      </div>

      <div className="catalog-content">
        {(selectedTab === 'all' || selectedTab === 'agents') && filteredCatalog?.agents && filteredCatalog.agents.length > 0 && (
          <section>
            <h2>🤖 Agents</h2>
            <div className="cards-grid">
              {filteredCatalog.agents.map(renderAgent)}
            </div>
          </section>
        )}

        {(selectedTab === 'all' || selectedTab === 'tools') && filteredCatalog?.tools && filteredCatalog.tools.length > 0 && (
          <section>
            <h2>🔧 Tools</h2>
            <div className="cards-grid">
              {filteredCatalog.tools.map(renderTool)}
            </div>
          </section>
        )}

        {(selectedTab === 'all' || selectedTab === 'workers') && filteredCatalog?.workers && filteredCatalog.workers.length > 0 && (
          <section>
            <h2>⚙️ Workers</h2>
            <div className="cards-grid">
              {filteredCatalog.workers.map(renderWorker)}
            </div>
          </section>
        )}
        
        {searchQuery && filteredCatalog?.total_services === 0 && (
          <div className="no-results">
            <h3>No services found</h3>
            <p>Try a different search term or <button className="link-btn" onClick={() => setSearchQuery('')}>clear the search</button></p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
