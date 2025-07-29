"""
Cost and Cycle Time Prediction ML Models
"""
import os
import pickle
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

from app.core.config import settings

logger = logging.getLogger(__name__)

class CostPredictor:
    """ML model for predicting manufacturing costs"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def prepare_features(self, parts_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare features for training or prediction
        
        Args:
            parts_data: List of part dictionaries with features
            
        Returns:
            DataFrame with processed features
        """
        features = []
        
        for part in parts_data:
            feature_dict = {
                # Dimensional features
                'length': part.get('length', 0.0),
                'width': part.get('width', 0.0),
                'height': part.get('height', 0.0),
                'volume': part.get('volume', 0.0),
                'surface_area': part.get('surface_area', 0.0),
                
                # Material features
                'material_type': part.get('material_type', 'aluminum'),
                
                # Complexity features
                'complexity_level': part.get('complexity_level', 'Medium'),
                'operation_count': len(part.get('machining_operations', [])),
                
                # Manufacturing features
                'has_holes': 'drilling' in part.get('machining_operations', []),
                'has_threads': 'tapping' in part.get('machining_operations', []),
                'requires_turning': 'turning' in part.get('machining_operations', []),
                'requires_milling': 'milling' in part.get('machining_operations', []),
                
                # Tolerance features (estimated)
                'tight_tolerances': part.get('tight_tolerances', False),
                'surface_finish_required': part.get('surface_finish_required', False),
                
                # Quantity
                'quantity': part.get('quantity', 1),
                
                # AI confidence
                'ai_confidence': part.get('confidence_score', 0.8),
            }
            
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        
        # Handle categorical variables
        categorical_columns = ['material_type', 'complexity_level']
        for col in categorical_columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Handle unseen categories
                df[col] = df[col].map(lambda x: x if x in self.label_encoders[col].classes_ 
                                    else 'unknown')
                if 'unknown' not in self.label_encoders[col].classes_:
                    # Add unknown category if not present
                    classes = list(self.label_encoders[col].classes_) + ['unknown']
                    self.label_encoders[col].classes_ = np.array(classes)
                df[col] = self.label_encoders[col].transform(df[col])
        
        # Convert boolean columns to int
        bool_columns = ['has_holes', 'has_threads', 'requires_turning', 
                       'requires_milling', 'tight_tolerances', 'surface_finish_required']
        for col in bool_columns:
            df[col] = df[col].astype(int)
        
        return df
    
    def calculate_cost_components(self, features: pd.DataFrame, 
                                predictions: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Break down total cost into components
        
        Args:
            features: Feature DataFrame
            predictions: Total cost predictions
            
        Returns:
            Dictionary with cost component arrays
        """
        # Base material cost calculation
        material_costs = np.zeros(len(features))
        
        # Material cost multipliers (per unit volume)
        material_rates = {
            0: 2.50,  # aluminum (encoded as 0)
            1: 3.80,  # brass
            2: 5.20,  # plastic
            3: 4.50,  # steel
            4: 25.00, # titanium
        }
        
        for i, row in features.iterrows():
            volume = max(row['volume'], 0.001)  # Minimum volume
            material_type = int(row['material_type'])
            rate = material_rates.get(material_type, 3.50)
            material_costs[i] = volume * rate * row['quantity']
        
        # Labor cost estimation (based on complexity and operations)
        labor_hours = np.zeros(len(features))
        base_labor_rate = settings.DEFAULT_LABOR_RATE
        
        for i, row in features.iterrows():
            # Base time estimation
            base_time = 0.5  # hours
            
            # Complexity multiplier
            complexity_multipliers = {0: 1.0, 1: 2.0, 2: 4.0}  # Low, Medium, High
            complexity = int(row['complexity_level'])
            complexity_mult = complexity_multipliers.get(complexity, 2.0)
            
            # Operation time
            operation_time = row['operation_count'] * 0.25  # 15 minutes per operation
            
            # Special operations
            if row['requires_turning']:
                operation_time += 0.5
            if row['has_holes']:
                operation_time += 0.2 * 5  # Assume 5 holes average
            if row['tight_tolerances']:
                operation_time *= 1.5
            
            labor_hours[i] = (base_time + operation_time) * complexity_mult * row['quantity']
        
        labor_costs = labor_hours * base_labor_rate
        
        # Overhead calculation
        overhead_costs = (material_costs + labor_costs) * settings.DEFAULT_OVERHEAD_RATE
        
        return {
            'material_cost': material_costs,
            'labor_cost': labor_costs,
            'overhead_cost': overhead_costs,
            'total_cost': material_costs + labor_costs + overhead_costs
        }
    
    def train(self, training_data: List[Dict[str, Any]], 
              target_costs: List[float]) -> Dict[str, float]:
        """
        Train the cost prediction model
        
        Args:
            training_data: List of part features
            target_costs: Actual costs for training
            
        Returns:
            Training metrics
        """
        try:
            # Prepare features
            X = self.prepare_features(training_data)
            y = np.array(target_costs)
            
            # Store feature names
            self.feature_names = X.columns.tolist()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train XGBoost model
            self.model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_pred = self.model.predict(X_train_scaled)
            test_pred = self.model.predict(X_test_scaled)
            
            metrics = {
                'train_mae': mean_absolute_error(y_train, train_pred),
                'test_mae': mean_absolute_error(y_test, test_pred),
                'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
                'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
                'train_r2': r2_score(y_train, train_pred),
                'test_r2': r2_score(y_test, test_pred)
            }
            
            self.is_trained = True
            
            logger.info(f"Model trained successfully. Test R²: {metrics['test_r2']:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def predict(self, parts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict costs for given parts
        
        Args:
            parts_data: List of part features
            
        Returns:
            Prediction results with cost breakdown
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Please train the model first.")
        
        try:
            # Prepare features
            X = self.prepare_features(parts_data)
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            total_predictions = self.model.predict(X_scaled)
            
            # Calculate cost components
            cost_components = self.calculate_cost_components(X, total_predictions)
            
            # Get feature importance for confidence scoring
            feature_importance = dict(zip(self.feature_names, 
                                        self.model.feature_importances_))
            
            # Calculate confidence based on feature completeness
            confidence_scores = []
            for i, part in enumerate(parts_data):
                confidence = part.get('confidence_score', 0.8)
                # Adjust based on data completeness
                if part.get('volume', 0) > 0:
                    confidence += 0.1
                if part.get('material_type'):
                    confidence += 0.05
                if part.get('machining_operations'):
                    confidence += 0.05
                
                confidence_scores.append(min(confidence, 0.95))
            
            return {
                'predictions': total_predictions.tolist(),
                'cost_breakdown': {
                    'material_costs': cost_components['material_cost'].tolist(),
                    'labor_costs': cost_components['labor_cost'].tolist(),
                    'overhead_costs': cost_components['overhead_cost'].tolist(),
                    'total_costs': cost_components['total_cost'].tolist()
                },
                'confidence_scores': confidence_scores,
                'feature_importance': feature_importance
            }
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise
    
    def save_model(self, model_path: str):
        """Save the trained model and preprocessing objects"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, model_path)
            logger.info(f"Model saved to {model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, model_path: str):
        """Load a previously trained model"""
        try:
            model_data = joblib.load(model_path)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {model_path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

class CycleTimePredictor:
    """ML model for predicting manufacturing cycle times"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def prepare_features(self, parts_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features for cycle time prediction"""
        # Similar to CostPredictor but focused on time-related features
        features = []
        
        for part in parts_data:
            feature_dict = {
                'volume': part.get('volume', 0.0),
                'surface_area': part.get('surface_area', 0.0),
                'complexity_level': part.get('complexity_level', 'Medium'),
                'material_type': part.get('material_type', 'aluminum'),
                'operation_count': len(part.get('machining_operations', [])),
                'requires_finishing': part.get('surface_finish_required', False),
                'tight_tolerances': part.get('tight_tolerances', False),
                'quantity': part.get('quantity', 1),
            }
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        
        # Encode categorical variables
        for col in ['material_type', 'complexity_level']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[col] = df[col].map(lambda x: x if x in self.label_encoders[col].classes_ 
                                    else 'unknown')
                if 'unknown' not in self.label_encoders[col].classes_:
                    classes = list(self.label_encoders[col].classes_) + ['unknown']
                    self.label_encoders[col].classes_ = np.array(classes)
                df[col] = self.label_encoders[col].transform(df[col])
        
        # Convert boolean columns
        bool_columns = ['requires_finishing', 'tight_tolerances']
        for col in bool_columns:
            df[col] = df[col].astype(int)
        
        return df
    
    def predict_cycle_time(self, parts_data: List[Dict[str, Any]]) -> List[float]:
        """
        Predict cycle times for parts
        
        Args:
            parts_data: List of part features
            
        Returns:
            List of predicted cycle times in minutes
        """
        if not self.is_trained:
            # Use rule-based estimation if model not trained
            return self._rule_based_estimation(parts_data)
        
        X = self.prepare_features(parts_data)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        return predictions.tolist()
    
    def _rule_based_estimation(self, parts_data: List[Dict[str, Any]]) -> List[float]:
        """Fallback rule-based cycle time estimation"""
        cycle_times = []
        
        for part in parts_data:
            base_time = 30.0  # Base 30 minutes
            
            # Complexity multiplier
            complexity = part.get('complexity_level', 'Medium')
            if complexity == 'High':
                base_time *= 3.0
            elif complexity == 'Medium':
                base_time *= 2.0
            
            # Material multiplier
            material = part.get('material_type', 'aluminum')
            material_multipliers = {
                'aluminum': 1.0,
                'steel': 1.5,
                'titanium': 3.0,
                'plastic': 0.7
            }
            base_time *= material_multipliers.get(material, 1.0)
            
            # Operations
            operations = part.get('machining_operations', [])
            base_time += len(operations) * 15  # 15 min per operation
            
            # Quantity (with setup time consideration)
            quantity = part.get('quantity', 1)
            if quantity > 1:
                # Setup time + per-unit time
                total_time = base_time + (quantity - 1) * (base_time * 0.7)
            else:
                total_time = base_time
            
            cycle_times.append(total_time)
        
        return cycle_times

# Export classes
__all__ = ['CostPredictor', 'CycleTimePredictor']