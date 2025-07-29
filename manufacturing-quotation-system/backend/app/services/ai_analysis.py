import cv2
import numpy as np
import os
import json
from typing import List, Dict, Tuple, Optional
import trimesh
import open3d as o3d
from PIL import Image
import pytesseract
from app.models.schemas import PartAnalysisResult, PartDimensions, MaterialSpecification, MachiningOperation, ToolRequirement, MachiningProcess

class DrawingAnalyzer:
    """AI-powered drawing analysis for manufacturing quotations"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.supported_formats = {
            'cad_3d': ['.step', '.stp', '.stl'],
            'cad_2d': ['.dwg', '.dxf'],
            'pdf': ['.pdf'],
            'image': ['.png', '.jpg', '.jpeg', '.tiff']
        }
        
        # Material database (in production, this would be a comprehensive database)
        self.material_database = {
            'aluminum': {
                'density': 2.7,  # g/cm³
                'cost_per_kg': 3.50,
                'machinability': 0.8,
                'common_grades': ['6061-T6', '7075-T6', '2024-T3']
            },
            'steel': {
                'density': 7.85,
                'cost_per_kg': 1.20,
                'machinability': 0.6,
                'common_grades': ['1018', '4140', '304SS', '316SS']
            },
            'brass': {
                'density': 8.5,
                'cost_per_kg': 6.00,
                'machinability': 0.9,
                'common_grades': ['C360', 'C260']
            },
            'titanium': {
                'density': 4.5,
                'cost_per_kg': 35.00,
                'machinability': 0.3,
                'common_grades': ['Ti-6Al-4V', 'Grade 2']
            }
        }
        
        # Tool database
        self.tool_database = {
            'end_mill': {
                'cost_per_hour': 15.0,
                'typical_sizes': ['1/8"', '1/4"', '3/8"', '1/2"', '5/8"', '3/4"', '1"'],
                'processes': ['milling', 'contouring', 'pocketing']
            },
            'drill': {
                'cost_per_hour': 5.0,
                'typical_sizes': ['#40', '#30', '#21', '1/4"', '5/16"', '3/8"', '1/2"'],
                'processes': ['drilling']
            },
            'tap': {
                'cost_per_hour': 8.0,
                'typical_sizes': ['M3', 'M4', 'M5', 'M6', 'M8', '1/4-20', '5/16-18', '3/8-16'],
                'processes': ['tapping']
            },
            'reamer': {
                'cost_per_hour': 12.0,
                'typical_sizes': ['1/4"', '5/16"', '3/8"', '1/2"'],
                'processes': ['reaming']
            }
        }
    
    async def analyze_files(self, file_paths: List[str], quote_id: str) -> List[PartAnalysisResult]:
        """Analyze multiple files and extract manufacturing data"""
        results = []
        
        for i, file_path in enumerate(file_paths):
            try:
                part_name = f"Part_{i+1}_{os.path.splitext(os.path.basename(file_path))[0]}"
                result = await self.analyze_single_file(file_path, part_name)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing file {file_path}: {str(e)}")
                # Create a basic result with low confidence
                results.append(self._create_fallback_result(file_path, i+1))
        
        return results
    
    async def analyze_single_file(self, file_path: str, part_name: str) -> PartAnalysisResult:
        """Analyze a single file and extract manufacturing data"""
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in self.supported_formats['cad_3d']:
            return await self._analyze_3d_cad(file_path, part_name)
        elif file_extension in self.supported_formats['cad_2d']:
            return await self._analyze_2d_cad(file_path, part_name)
        elif file_extension in self.supported_formats['pdf']:
            return await self._analyze_pdf_drawing(file_path, part_name)
        elif file_extension in self.supported_formats['image']:
            return await self._analyze_image_drawing(file_path, part_name)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def _analyze_3d_cad(self, file_path: str, part_name: str) -> PartAnalysisResult:
        """Analyze 3D CAD files (STL, STEP)"""
        
        try:
            if file_path.endswith('.stl'):
                # Load STL file
                mesh = trimesh.load_mesh(file_path)
                
                # Extract dimensions
                bounds = mesh.bounds
                dimensions = PartDimensions(
                    length=float(bounds[1][0] - bounds[0][0]),
                    width=float(bounds[1][1] - bounds[0][1]),
                    height=float(bounds[1][2] - bounds[0][2]),
                    volume=float(mesh.volume),
                    surface_area=float(mesh.area)
                )
                
                # Analyze geometry complexity
                complexity_score = self._calculate_3d_complexity(mesh)
                
                # Determine material based on part characteristics
                material = self._estimate_material_from_3d(mesh, dimensions)
                
                # Generate machining operations
                operations = self._generate_3d_machining_operations(mesh, dimensions, material)
                
                # Calculate total cycle time
                total_cycle_time = sum(op.estimated_time for op in operations)
                
                return PartAnalysisResult(
                    part_id=str(hash(part_name)),
                    part_name=part_name,
                    dimensions=dimensions,
                    material=material,
                    operations=operations,
                    total_cycle_time=total_cycle_time,
                    complexity_score=complexity_score,
                    confidence_score=0.85
                )
            
            elif file_path.endswith(('.step', '.stp')):
                # For STEP files, use Open3D for analysis
                return await self._analyze_step_file(file_path, part_name)
            
        except Exception as e:
            print(f"Error analyzing 3D CAD file: {str(e)}")
            return self._create_fallback_result(file_path, 1)
    
    async def _analyze_2d_cad(self, file_path: str, part_name: str) -> PartAnalysisResult:
        """Analyze 2D CAD files (DWG, DXF)"""
        
        # For now, create a mock analysis since DWG/DXF parsing requires specialized libraries
        # In production, you'd use libraries like ezdxf for DXF or Open Design Alliance for DWG
        
        dimensions = PartDimensions(
            length=100.0,  # Mock values
            width=50.0,
            height=10.0,
            volume=50000.0,
            surface_area=12000.0
        )
        
        material = MaterialSpecification(
            material_type="aluminum",
            grade="6061-T6",
            stock_size="4\" x 2\" x 1/2\"",
            stock_thickness=12.7
        )
        
        operations = [
            MachiningOperation(
                process=MachiningProcess.MILLING,
                description="Rough milling to profile",
                estimated_time=25.0,
                complexity_factor=0.7,
                tools_required=[
                    ToolRequirement(
                        tool_type="end_mill",
                        tool_size="1/2\"",
                        quantity=1,
                        estimated_cost=15.0
                    )
                ]
            )
        ]
        
        return PartAnalysisResult(
            part_id=str(hash(part_name)),
            part_name=part_name,
            dimensions=dimensions,
            material=material,
            operations=operations,
            total_cycle_time=25.0,
            complexity_score=0.6,
            confidence_score=0.7
        )
    
    async def _analyze_pdf_drawing(self, file_path: str, part_name: str) -> PartAnalysisResult:
        """Analyze PDF technical drawings using OCR and image processing"""
        
        try:
            # Convert PDF to images and extract text
            # This is a simplified implementation - production would use pdf2image
            
            # Extract text using OCR
            text = pytesseract.image_to_string(Image.open(file_path))
            
            # Parse dimensions from text (basic pattern matching)
            dimensions = self._extract_dimensions_from_text(text)
            
            # Estimate material from drawing notes
            material = self._estimate_material_from_text(text)
            
            # Generate basic machining operations
            operations = self._generate_basic_operations(dimensions)
            
            return PartAnalysisResult(
                part_id=str(hash(part_name)),
                part_name=part_name,
                dimensions=dimensions,
                material=material,
                operations=operations,
                total_cycle_time=sum(op.estimated_time for op in operations),
                complexity_score=0.5,
                confidence_score=0.6
            )
            
        except Exception as e:
            print(f"Error analyzing PDF: {str(e)}")
            return self._create_fallback_result(file_path, 1)
    
    async def _analyze_image_drawing(self, file_path: str, part_name: str) -> PartAnalysisResult:
        """Analyze image drawings using computer vision and OCR"""
        
        try:
            # Load image
            image = cv2.imread(file_path)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(denoised)
            
            # Detect lines and shapes for geometric analysis
            edges = cv2.Canny(denoised, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze geometry from contours
            complexity_score = len(contours) / 100.0  # Rough complexity based on number of features
            
            # Extract dimensions from text
            dimensions = self._extract_dimensions_from_text(text)
            
            # Estimate material
            material = self._estimate_material_from_text(text)
            
            # Generate operations
            operations = self._generate_basic_operations(dimensions)
            
            return PartAnalysisResult(
                part_id=str(hash(part_name)),
                part_name=part_name,
                dimensions=dimensions,
                material=material,
                operations=operations,
                total_cycle_time=sum(op.estimated_time for op in operations),
                complexity_score=min(complexity_score, 1.0),
                confidence_score=0.6
            )
            
        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            return self._create_fallback_result(file_path, 1)
    
    def _calculate_3d_complexity(self, mesh) -> float:
        """Calculate complexity score for 3D mesh"""
        
        try:
            # Factor in number of faces, convexity, and surface features
            face_count = len(mesh.faces)
            convex_hull = mesh.convex_hull
            convexity = mesh.volume / convex_hull.volume if convex_hull.volume > 0 else 0
            
            # Normalize and combine factors
            face_complexity = min(face_count / 10000, 1.0)
            convexity_complexity = 1.0 - convexity
            
            return (face_complexity + convexity_complexity) / 2
            
        except:
            return 0.5  # Default complexity
    
    def _estimate_material_from_3d(self, mesh, dimensions: PartDimensions) -> MaterialSpecification:
        """Estimate material based on 3D part characteristics"""
        
        # Simple heuristic: smaller, complex parts might be aluminum
        # Larger parts might be steel
        volume_cm3 = dimensions.volume / 1000  # Convert mm³ to cm³
        
        if volume_cm3 < 100:
            material_type = "aluminum"
            grade = "6061-T6"
        elif volume_cm3 > 1000:
            material_type = "steel"
            grade = "1018"
        else:
            material_type = "aluminum"
            grade = "6061-T6"
        
        # Estimate stock size
        length_in = dimensions.length / 25.4
        width_in = dimensions.width / 25.4
        height_in = dimensions.height / 25.4
        
        stock_size = f"{length_in:.1f}\" x {width_in:.1f}\" x {height_in:.1f}\""
        
        return MaterialSpecification(
            material_type=material_type,
            grade=grade,
            stock_size=stock_size,
            stock_thickness=dimensions.height
        )
    
    def _generate_3d_machining_operations(self, mesh, dimensions: PartDimensions, material: MaterialSpecification) -> List[MachiningOperation]:
        """Generate machining operations for 3D parts"""
        
        operations = []
        
        # Basic milling operation
        milling_time = self._estimate_milling_time(dimensions, material)
        operations.append(MachiningOperation(
            process=MachiningProcess.MILLING,
            description="3-axis milling to final geometry",
            estimated_time=milling_time,
            complexity_factor=0.8,
            tools_required=[
                ToolRequirement(
                    tool_type="end_mill",
                    tool_size="1/2\"",
                    quantity=1,
                    estimated_cost=25.0
                ),
                ToolRequirement(
                    tool_type="end_mill",
                    tool_size="1/4\"",
                    quantity=1,
                    estimated_cost=15.0
                )
            ]
        ))
        
        # Add drilling if there might be holes
        if self._detect_holes_in_mesh(mesh):
            operations.append(MachiningOperation(
                process=MachiningProcess.DRILLING,
                description="Drill holes as specified",
                estimated_time=10.0,
                complexity_factor=0.5,
                tools_required=[
                    ToolRequirement(
                        tool_type="drill",
                        tool_size="1/4\"",
                        quantity=1,
                        estimated_cost=5.0
                    )
                ]
            ))
        
        return operations
    
    def _estimate_milling_time(self, dimensions: PartDimensions, material: MaterialSpecification) -> float:
        """Estimate milling time based on part size and material"""
        
        volume_removal = dimensions.volume * 0.3  # Assume 30% material removal
        material_factor = self.material_database.get(material.material_type, {}).get('machinability', 0.7)
        
        # Base time calculation (simplified)
        base_time = volume_removal / 1000  # minutes per cm³ removed
        adjusted_time = base_time / material_factor
        
        return max(adjusted_time, 5.0)  # Minimum 5 minutes
    
    def _detect_holes_in_mesh(self, mesh) -> bool:
        """Simple heuristic to detect if mesh might have holes"""
        # This is a placeholder - real implementation would analyze mesh topology
        return mesh.is_watertight == False
    
    def _extract_dimensions_from_text(self, text: str) -> PartDimensions:
        """Extract dimensions from OCR text using pattern matching"""
        
        import re
        
        # Simple regex patterns for dimensions
        dim_patterns = [
            r'(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)',
            r'L\s*=?\s*(\d+\.?\d*)',
            r'W\s*=?\s*(\d+\.?\d*)',
            r'H\s*=?\s*(\d+\.?\d*)'
        ]
        
        # Default dimensions (mm)
        length, width, height = 100.0, 50.0, 25.0
        
        for pattern in dim_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if len(matches[0]) == 3:  # L x W x H format
                    length, width, height = map(float, matches[0])
                    break
        
        return PartDimensions(
            length=length,
            width=width,
            height=height,
            volume=length * width * height,
            surface_area=2 * (length * width + width * height + height * length)
        )
    
    def _estimate_material_from_text(self, text: str) -> MaterialSpecification:
        """Estimate material from drawing text/notes"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['aluminum', 'al', '6061', '7075']):
            return MaterialSpecification(
                material_type="aluminum",
                grade="6061-T6",
                stock_size="Standard bar stock",
                stock_thickness=25.0
            )
        elif any(word in text_lower for word in ['steel', 'carbon', '1018', '4140']):
            return MaterialSpecification(
                material_type="steel",
                grade="1018",
                stock_size="Standard bar stock",
                stock_thickness=25.0
            )
        elif any(word in text_lower for word in ['brass', 'bronze']):
            return MaterialSpecification(
                material_type="brass",
                grade="C360",
                stock_size="Standard bar stock",
                stock_thickness=25.0
            )
        else:
            # Default to aluminum
            return MaterialSpecification(
                material_type="aluminum",
                grade="6061-T6",
                stock_size="Standard bar stock",
                stock_thickness=25.0
            )
    
    def _generate_basic_operations(self, dimensions: PartDimensions) -> List[MachiningOperation]:
        """Generate basic machining operations"""
        
        operations = []
        
        # Basic milling
        operations.append(MachiningOperation(
            process=MachiningProcess.MILLING,
            description="Machine to final dimensions",
            estimated_time=30.0,
            complexity_factor=0.6,
            tools_required=[
                ToolRequirement(
                    tool_type="end_mill",
                    tool_size="1/2\"",
                    quantity=1,
                    estimated_cost=20.0
                )
            ]
        ))
        
        return operations
    
    def _create_fallback_result(self, file_path: str, part_number: int) -> PartAnalysisResult:
        """Create a fallback result when analysis fails"""
        
        part_name = f"Part_{part_number}"
        
        return PartAnalysisResult(
            part_id=str(hash(file_path)),
            part_name=part_name,
            dimensions=PartDimensions(
                length=100.0,
                width=50.0,
                height=25.0,
                volume=125000.0,
                surface_area=11500.0
            ),
            material=MaterialSpecification(
                material_type="aluminum",
                grade="6061-T6",
                stock_size="4\" x 2\" x 1\"",
                stock_thickness=25.0
            ),
            operations=[
                MachiningOperation(
                    process=MachiningProcess.MILLING,
                    description="General machining (analysis incomplete)",
                    estimated_time=45.0,
                    complexity_factor=0.5,
                    tools_required=[
                        ToolRequirement(
                            tool_type="end_mill",
                            tool_size="1/2\"",
                            quantity=1,
                            estimated_cost=25.0
                        )
                    ]
                )
            ],
            total_cycle_time=45.0,
            complexity_score=0.5,
            confidence_score=0.3  # Low confidence for fallback
        )
    
    async def _analyze_step_file(self, file_path: str, part_name: str) -> PartAnalysisResult:
        """Analyze STEP files using specialized libraries"""
        
        # Placeholder for STEP file analysis
        # In production, you'd use libraries like opencascade or FreeCAD Python API
        
        return self._create_fallback_result(file_path, 1)