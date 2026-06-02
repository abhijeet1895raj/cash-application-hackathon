'use client';

import { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [events, setEvents] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);
  const eventContainerRef = useRef(null);

  const startPipeline = async () => {
    setIsRunning(true);
    setError(null);
    setEvents([]);

    try {
      const response = await fetch('http://localhost:8000/api/process');

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Process complete lines
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              setEvents((prev) => [...prev, data]);
              // Auto-scroll to latest event
              setTimeout(() => {
                eventContainerRef.current?.scrollTo(0, eventContainerRef.current.scrollHeight);
              }, 50);
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }

        // Keep incomplete line in buffer
        buffer = lines[lines.length - 1];
      }

      setIsRunning(false);
    } catch (err) {
      setError(err.message);
      setIsRunning(false);
    }
  };

  const resetPipeline = () => {
    setEvents([]);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            💰 Cash Application Foundry
          </h1>
          <p className="text-lg text-gray-600">
            5-Agent AI Pipeline for Bank Reconciliation
          </p>
        </div>

        {/* Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex gap-4 mb-4">
            <button
              onClick={startPipeline}
              disabled={isRunning}
              className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
            >
              {isRunning ? '⏳ Processing...' : '▶ Start Pipeline'}
            </button>
            <button
              onClick={resetPipeline}
              disabled={isRunning}
              className="px-6 py-2 bg-gray-600 text-white font-semibold rounded-lg hover:bg-gray-700 disabled:bg-gray-400 transition"
            >
              ↻ Reset
            </button>
          </div>

          {error && (
            <div className="p-4 bg-red-100 border border-red-400 text-red-800 rounded">
              ❌ Error: {error}
            </div>
          )}

          {events.length > 0 && (
            <div className="text-sm text-gray-600">
              {events.filter((e) => e.status === 'completed').length} of{' '}
              {events.filter((e) => e.agent).length} agents completed
            </div>
          )}
        </div>

        {/* Pipeline Events Stream */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900">Pipeline Events</h2>

          <div
            ref={eventContainerRef}
            className="bg-white rounded-lg shadow-md p-6 max-h-96 overflow-y-auto space-y-4"
          >
            {events.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                Click "Start Pipeline" to begin processing...
              </p>
            ) : (
              events.map((event, idx) => (
                <EventCard key={idx} event={event} />
              ))
            )}
          </div>
        </div>

        {/* Summary */}
        {events.some((e) => e.agent === 'pipeline' && e.status === 'completed') && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">📊 Summary</h3>
            {events
              .filter((e) => e.agent === 'pipeline' && e.status === 'completed')
              .map((e, idx) => (
                <div key={idx} className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-blue-50 rounded">
                    <p className="text-gray-600 text-sm">Total Transactions</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {e.summary?.total_transactions}
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded">
                    <p className="text-gray-600 text-sm">Matched Payments</p>
                    <p className="text-2xl font-bold text-green-600">
                      {e.summary?.matched_payments}
                    </p>
                  </div>
                  <div className="p-3 bg-yellow-50 rounded">
                    <p className="text-gray-600 text-sm">Unmatched Payments</p>
                    <p className="text-2xl font-bold text-yellow-600">
                      {e.summary?.unmatched_payments}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded">
                    <p className="text-gray-600 text-sm">Ready to Post</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {e.summary?.ready_to_post}
                    </p>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </main>
  );
}

function EventCard({ event }) {
  const [showJson, setShowJson] = useState(false);

  const statusColors = {
    starting: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const agentEmojis = {
    bank_statement_agent: '🏦',
    ar_ledger_agent: '📋',
    reconciliation_agent: '🔗',
    mismatch_agent: '🤔',
    posting_agent: '📝',
    pipeline: '⚙️',
  };

  return (
    <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-2xl">
            {agentEmojis[event.agent] || '🔹'}
          </span>
          <div>
            <h4 className="font-semibold text-gray-900">
              {event.agent.replace(/_/g, ' ').toUpperCase()}
            </h4>
            <p className="text-xs text-gray-500">{event.timestamp}</p>
          </div>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColors[event.status] || 'bg-gray-200'}`}
        >
          {event.status}
        </span>
      </div>

      {event.status === 'failed' && (
        <p className="text-red-600 text-sm mb-2">Error: {event.message}</p>
      )}

      {event.summary && (
        <div className="text-sm text-gray-600 mb-2">
          <p>
            💰 Total transactions: <strong>{event.summary.total_transactions}</strong> | Matched:{' '}
            <strong>{event.summary.matched_payments}</strong> | Ready to post:{' '}
            <strong>{event.summary.ready_to_post}</strong>
          </p>
        </div>
      )}

      {event.output && (
        <button
          onClick={() => setShowJson(!showJson)}
          className="text-blue-600 text-sm hover:underline mb-2"
        >
          {showJson ? '▼ Hide' : '▶ Show'} Output JSON
        </button>
      )}

      {showJson && event.output && (
        <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto max-h-48">
          {JSON.stringify(event.output, null, 2)}
        </pre>
      )}
    </div>
  );
}
