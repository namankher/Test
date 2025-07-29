import os
from typing import List
from app.models.database import Part, MachiningOperation
from app.models.schemas import CostBreakdown

class CostCalculator:
    """Calculate manufacturing costs for parts and quotes"""
    
    def __init__(self):
        # Load pricing parameters from environment or defaults
        self.labor_rate_per_hour = float(os.getenv("LABOR_RATE_PER_HOUR", 75.0))
        self.machine_rate_per_hour = float(os.getenv("MACHINE_RATE_PER_HOUR", 85.0))
        self.setup_time_minutes = float(os.getenv("SETUP_TIME_MINUTES", 30.0))
        self.setup_rate_per_hour = float(os.getenv("SETUP_RATE_PER_HOUR", 95.0))
        
        # Material pricing database (in production, this would be dynamic)
        self.material_pricing = {
            'aluminum': {
                '6061-T6': 3.50,  # USD per kg
                '7075-T6': 4.20,
                '2024-T3': 4.80
            },
            'steel': {
                '1018': 1.20,
                '4140': 2.10,
                '304SS': 6.50,
                '316SS': 8.20
            },
            'brass': {
                'C360': 6.00,
                'C260': 5.50
            },
            'titanium': {
                'Ti-6Al-4V': 35.00,
                'Grade 2': 28.00
            }
        }
        
        # Material density database (g/cm³)
        self.material_density = {
            'aluminum': 2.7,
            'steel': 7.85,
            'brass': 8.5,
            'titanium': 4.5
        }
        
        # Tool cost factors
        self.tool_cost_factors = {
            'end_mill': 0.15,  # Cost factor per minute of use
            'drill': 0.05,
            'tap': 0.08,
            'reamer': 0.12,
            'boring_bar': 0.18,
            'face_mill': 0.25
        }
    
    async def calculate_quote_costs(
        self, 
        parts: List[Part], 
        quantity: int,
        overhead_percentage: float,
        margin_percentage: float,
        delivery_days: int,
        rush_order: bool = False
    ) -> CostBreakdown:
        """Calculate total costs for all parts in a quote"""
        
        total_material_cost = 0.0
        total_labor_cost = 0.0
        total_machine_cost = 0.0
        total_tool_cost = 0.0
        total_setup_cost = 0.0
        
        for part in parts:
            part_costs = await self.calculate_part_costs(part, quantity)
            
            total_material_cost += part_costs['material_cost']
            total_labor_cost += part_costs['labor_cost']
            total_machine_cost += part_costs['machine_cost']
            total_tool_cost += part_costs['tool_cost']
            total_setup_cost += part_costs['setup_cost']
        
        # Calculate subtotal
        subtotal = (
            total_material_cost + 
            total_labor_cost + 
            total_machine_cost + 
            total_tool_cost + 
            total_setup_cost
        )
        
        # Apply rush order surcharge
        if rush_order:
            subtotal *= 1.25  # 25% rush surcharge
        
        # Apply delivery time factor
        if delivery_days <= 7:
            subtotal *= 1.15  # 15% expedite fee
        elif delivery_days <= 14:
            subtotal *= 1.05  # 5% expedite fee
        
        # Calculate overhead
        overhead_cost = subtotal * (overhead_percentage / 100)
        
        # Calculate total before margin
        cost_before_margin = subtotal + overhead_cost
        
        # Calculate margin
        margin_amount = cost_before_margin * (margin_percentage / 100)
        
        # Calculate final total
        total_cost = cost_before_margin + margin_amount
        
        return CostBreakdown(
            material_cost=round(total_material_cost, 2),
            labor_cost=round(total_labor_cost, 2),
            machine_cost=round(total_machine_cost, 2),
            tool_cost=round(total_tool_cost, 2),
            setup_cost=round(total_setup_cost, 2),
            overhead_cost=round(overhead_cost, 2),
            subtotal=round(subtotal, 2),
            margin=round(margin_amount, 2),
            total_cost=round(total_cost, 2),
            margin_percentage=margin_percentage
        )
    
    async def calculate_part_costs(self, part: Part, quantity: int) -> dict:
        """Calculate costs for a single part"""
        
        # Calculate material cost
        material_cost = self._calculate_material_cost(part, quantity)
        
        # Calculate machining costs
        machining_costs = await self._calculate_machining_costs(part, quantity)
        
        return {
            'material_cost': material_cost,
            'labor_cost': machining_costs['labor_cost'],
            'machine_cost': machining_costs['machine_cost'],
            'tool_cost': machining_costs['tool_cost'],
            'setup_cost': machining_costs['setup_cost']
        }
    
    def _calculate_material_cost(self, part: Part, quantity: int) -> float:
        """Calculate material cost for a part"""
        
        try:
            # Get material pricing
            material_price_per_kg = self.material_pricing.get(
                part.material_type, {}
            ).get(part.material_grade, 5.0)  # Default to $5/kg if not found
            
            # Get material density
            density = self.material_density.get(part.material_type, 3.0)  # Default density
            
            # Calculate volume in cubic centimeters
            volume_cm3 = part.volume / 1000 if part.volume else 1000  # Convert mm³ to cm³
            
            # Calculate mass in kg
            mass_kg = (volume_cm3 * density) / 1000  # Convert g to kg
            
            # Add material waste factor (typically 10-20%)
            waste_factor = 1.15
            
            # Calculate cost per part
            cost_per_part = mass_kg * material_price_per_kg * waste_factor
            
            return cost_per_part * quantity
            
        except Exception as e:
            print(f"Error calculating material cost for part {part.id}: {str(e)}")
            return 50.0 * quantity  # Fallback cost
    
    async def _calculate_machining_costs(self, part: Part, quantity: int) -> dict:
        """Calculate machining costs for a part"""
        
        try:
            total_cycle_time_hours = (part.total_cycle_time or 30.0) / 60  # Convert minutes to hours
            
            # Calculate per-part costs
            labor_cost_per_part = total_cycle_time_hours * self.labor_rate_per_hour
            machine_cost_per_part = total_cycle_time_hours * self.machine_rate_per_hour
            
            # Calculate tool costs (based on cycle time and complexity)
            complexity_factor = part.complexity_score or 0.5
            tool_cost_per_part = total_cycle_time_hours * 10.0 * complexity_factor  # Base tool cost
            
            # Calculate setup costs (amortized across quantity)
            setup_time_hours = self.setup_time_minutes / 60
            setup_cost_total = setup_time_hours * self.setup_rate_per_hour
            setup_cost_per_part = setup_cost_total / max(quantity, 1)
            
            return {
                'labor_cost': labor_cost_per_part * quantity,
                'machine_cost': machine_cost_per_part * quantity,
                'tool_cost': tool_cost_per_part * quantity,
                'setup_cost': setup_cost_total  # Setup is fixed cost
            }
            
        except Exception as e:
            print(f"Error calculating machining costs for part {part.id}: {str(e)}")
            return {
                'labor_cost': 100.0 * quantity,
                'machine_cost': 120.0 * quantity,
                'tool_cost': 30.0 * quantity,
                'setup_cost': 150.0
            }
    
    def calculate_operation_cost(self, operation: dict, quantity: int) -> dict:
        """Calculate cost for a specific machining operation"""
        
        operation_time_hours = operation.get('estimated_time', 15.0) / 60
        complexity_factor = operation.get('complexity_factor', 0.5)
        
        # Base costs
        labor_cost = operation_time_hours * self.labor_rate_per_hour * quantity
        machine_cost = operation_time_hours * self.machine_rate_per_hour * quantity
        
        # Tool costs based on operation type and tools required
        tool_cost = 0.0
        tools_required = operation.get('tool_requirements', {}).get('tools', [])
        
        for tool in tools_required:
            tool_type = tool.get('tool_type', 'end_mill')
            tool_factor = self.tool_cost_factors.get(tool_type, 0.10)
            tool_cost += operation_time_hours * tool_factor * quantity
        
        return {
            'labor_cost': round(labor_cost, 2),
            'machine_cost': round(machine_cost, 2),
            'tool_cost': round(tool_cost, 2)
        }
    
    def estimate_delivery_time(self, parts: List[Part], quantity: int) -> int:
        """Estimate delivery time in days based on parts complexity and quantity"""
        
        total_cycle_time = sum(part.total_cycle_time or 30.0 for part in parts)
        total_production_time = total_cycle_time * quantity
        
        # Assume 8 hours per day, 5 days per week production capacity
        daily_capacity_minutes = 8 * 60
        production_days = max(1, int(total_production_time / daily_capacity_minutes))
        
        # Add lead time for materials and setup
        lead_time_days = 3
        
        # Add buffer for complex parts
        avg_complexity = sum(part.complexity_score or 0.5 for part in parts) / len(parts)
        complexity_buffer = int(avg_complexity * 5)  # Up to 5 extra days for complex parts
        
        total_days = production_days + lead_time_days + complexity_buffer
        
        return min(total_days, 90)  # Cap at 90 days
    
    def calculate_break_even_analysis(self, cost_breakdown: CostBreakdown) -> dict:
        """Calculate break-even analysis for the quote"""
        
        fixed_costs = cost_breakdown.setup_cost + cost_breakdown.overhead_cost
        variable_cost_per_unit = (
            cost_breakdown.material_cost + 
            cost_breakdown.labor_cost + 
            cost_breakdown.machine_cost + 
            cost_breakdown.tool_cost
        ) / max(cost_breakdown.quantity if hasattr(cost_breakdown, 'quantity') else 1, 1)
        
        selling_price_per_unit = cost_breakdown.total_cost / max(cost_breakdown.quantity if hasattr(cost_breakdown, 'quantity') else 1, 1)
        
        # Break-even quantity calculation
        if selling_price_per_unit > variable_cost_per_unit:
            break_even_quantity = fixed_costs / (selling_price_per_unit - variable_cost_per_unit)
        else:
            break_even_quantity = float('inf')  # Can't break even
        
        return {
            'break_even_quantity': max(1, int(break_even_quantity)),
            'fixed_costs': fixed_costs,
            'variable_cost_per_unit': variable_cost_per_unit,
            'selling_price_per_unit': selling_price_per_unit,
            'contribution_margin': selling_price_per_unit - variable_cost_per_unit,
            'contribution_margin_percentage': ((selling_price_per_unit - variable_cost_per_unit) / selling_price_per_unit) * 100 if selling_price_per_unit > 0 else 0
        }