# Manufacturing RFQ Intelligence Platform

🔧 **AI-Powered Manufacturing Quote Management System**

A comprehensive solution for managing RFQ (Request for Quotation) workflows with AI/ML integration, from CAD drawing ingestion to final quote generation.

## 🎯 Key Features

- **Smart Drawing Analysis**: AI-powered 2D/3D CAD file processing (DWG, STEP, IGES, PDF, PNG, JPG)
- **Intelligent Cost Prediction**: ML-based cycle time and cost estimation
- **Interactive Dashboard**: Real-time analytics and KPI monitoring
- **Automated Quote Generation**: Professional, branded quote documents
- **Approval Workflows**: Multi-stage review and approval processes
- **Historical Analytics**: Quote history, reuse, and performance tracking

## 🛠 Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Primary database for structured data
- **Redis** - Caching and session management

### AI/ML
- **PyTorch** - Deep learning framework for CAD analysis
- **OpenCV** - Computer vision for image processing
- **OpenCascade** - 3D CAD file processing
- **XGBoost** - Cost and time prediction models
- **Hugging Face Transformers** - NLP for feature extraction

### Frontend
- **React** - Modern UI framework
- **TailwindCSS** - Utility-first CSS framework
- **Three.js** - 3D visualization for CAD files
- **Chart.js** - Dashboard analytics and charts

### Infrastructure
- **Docker** - Containerization
- **AWS S3** - File storage
- **Nginx** - Reverse proxy and static file serving

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Node.js 16+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd manufacturing-rfq-platform
```

2. Start the development environment:
```bash
docker-compose up -d
```

3. Install dependencies:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

4. Run the application:
```bash
# Backend (Terminal 1)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend
npm start
```

Visit `http://localhost:3000` to access the application.

## 📊 Dashboard KPIs

- **Quotes Generated**: Total number of quotes processed
- **Total Revenue**: Revenue from approved quotes
- **Avg. Processing Time**: Time from upload to quote generation
- **Accuracy Rate**: AI prediction confidence and accuracy
- **Pipeline Status**: Quotes by stage (pending, approved, rejected)

## 🔄 AI/ML Workflow

1. **CAD Analysis**: Extract dimensions, tolerances, and features
2. **Process Classification**: Identify required machining operations
3. **Cost Prediction**: Estimate materials, labor, and overhead
4. **Cycle Time Calculation**: Predict manufacturing time
5. **Confidence Scoring**: Provide accuracy metrics
6. **Continuous Learning**: Improve models with actual vs. predicted data

## 📁 Project Structure

```
manufacturing-rfq-platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core settings and security
│   │   ├── db/             # Database models and migrations
│   │   ├── ml/             # AI/ML models and processing
│   │   └── services/       # Business logic services
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── ml-models/              # ML model training and artifacts
├── docs/                   # Documentation
├── docker-compose.yml      # Development environment
└── README.md              # This file
```

## 🔧 Development

### Backend Development
- API documentation: `http://localhost:8000/docs`
- Database migrations: `alembic upgrade head`
- Tests: `pytest`

### Frontend Development
- Development server: `npm start`
- Build: `npm run build`
- Tests: `npm test`

### ML Model Training
```bash
cd ml-models
python train_cost_prediction.py
python train_cycle_time.py
```

## 📝 API Documentation

The API documentation is available at `/docs` when running the backend server. Key endpoints include:

- `POST /api/v1/upload` - Upload CAD files
- `GET /api/v1/quotes` - List quotes
- `POST /api/v1/quotes/{id}/analyze` - Run AI analysis
- `GET /api/v1/dashboard/metrics` - Dashboard KPIs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.