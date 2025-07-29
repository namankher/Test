import React from 'react';

const Quotes: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Quotes</h1>
        <button className="btn-primary">
          New Quote
        </button>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Quote Management
        </h3>
        <p className="text-gray-600">
          Here you can view, create, and manage all your manufacturing quotes. 
          The AI system will analyze uploaded CAD files and automatically generate 
          cost estimates and delivery timelines.
        </p>
        
        <div className="mt-6 space-y-4">
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium text-gray-900">Sample Quote #001</h4>
                <p className="text-sm text-gray-600">Client: Acme Manufacturing</p>
                <p className="text-sm text-gray-600">Project: Engine Components</p>
              </div>
              <span className="status-quoted">Quoted</span>
            </div>
            <div className="mt-3 text-sm text-gray-600">
              <span>Total: $12,450</span> • <span>AI Confidence: 94%</span> • <span>3 parts</span>
            </div>
          </div>
          
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium text-gray-900">Sample Quote #002</h4>
                <p className="text-sm text-gray-600">Client: Tech Solutions Inc</p>
                <p className="text-sm text-gray-600">Project: Prototype Parts</p>
              </div>
              <span className="status-analyzing">Analyzing</span>
            </div>
            <div className="mt-3 text-sm text-gray-600">
              <span>Estimating costs...</span> • <span>2 files uploaded</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Quotes;