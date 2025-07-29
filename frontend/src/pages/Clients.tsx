import React from 'react';

const Clients: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
        <button className="btn-primary">
          New Client
        </button>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Client Management
        </h3>
        <p className="text-gray-600">
          Manage your client database, view client statistics, and track 
          their quote history and project preferences.
        </p>
        
        <div className="mt-6 space-y-4">
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium text-gray-900">Acme Manufacturing</h4>
                <p className="text-sm text-gray-600">contact@acme-mfg.com</p>
                <p className="text-sm text-gray-600">Industrial Equipment</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">5 quotes</p>
                <p className="text-sm text-gray-600">$45,200 total</p>
              </div>
            </div>
          </div>
          
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium text-gray-900">Tech Solutions Inc</h4>
                <p className="text-sm text-gray-600">orders@techsolutions.com</p>
                <p className="text-sm text-gray-600">Technology Hardware</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">2 quotes</p>
                <p className="text-sm text-gray-600">$18,750 total</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Clients;