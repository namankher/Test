import React from 'react';
import { useParams } from 'react-router-dom';

const QuoteDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Quote #{id}</h1>
        <div className="space-x-2">
          <button className="btn-outline">Edit</button>
          <button className="btn-success">Approve</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Quote Details
            </h3>
            <p className="text-gray-600">
              Detailed view of the quote including AI analysis results, 
              part breakdowns, cost calculations, and file attachments.
            </p>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Quote Summary
          </h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className="status-quoted">Quoted</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Cost:</span>
              <span className="font-medium">$12,450</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">AI Confidence:</span>
              <span className="font-medium">94%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuoteDetail;