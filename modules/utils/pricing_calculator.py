#!/usr/bin/env python3
"""
Pricing Calculator Module

This module provides comprehensive pricing calculations for e-commerce orders,
including tax calculations, discount applications, and shipping cost calculations.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import logging

# Configure logging
logger = logging.getLogger(__name__)


class PricingCalculator:
    """
    Comprehensive pricing calculator for e-commerce orders.
    
    Handles tax calculations, discount applications, shipping costs,
    and final order total calculations with proper rounding.
    """
    
    # Tax rates by region/state (can be extended or moved to database)
    TAX_RATES = {
        'CA': Decimal('0.0875'),  # California
        'NY': Decimal('0.08'),    # New York
        'TX': Decimal('0.0625'),  # Texas
        'FL': Decimal('0.06'),    # Florida
        'WA': Decimal('0.065'),   # Washington
        'DEFAULT': Decimal('0.07') # Default tax rate
    }
    
    # Shipping rates based on weight and distance
    SHIPPING_RATES = {
        'standard': {
            'base_rate': Decimal('5.99'),
            'per_kg': Decimal('2.50'),
            'free_shipping_threshold': Decimal('75.00')
        },
        'express': {
            'base_rate': Decimal('12.99'),
            'per_kg': Decimal('4.00'),
            'free_shipping_threshold': Decimal('150.00')
        },
        'overnight': {
            'base_rate': Decimal('24.99'),
            'per_kg': Decimal('8.00'),
            'free_shipping_threshold': Decimal('200.00')
        }
    }
    
    def __init__(self):
        """
        Initialize the pricing calculator.
        """
        self.precision = Decimal('0.01')  # Round to 2 decimal places
    
    def calculate_subtotal(self, order_items: List[Dict]) -> Decimal:
        """
        Calculate the subtotal for all order items.
        
        Args:
            order_items (List[Dict]): List of order items with 'quantity' and 'unit_price'
        
        Returns:
            Decimal: Subtotal amount
        """
        try:
            subtotal = Decimal('0.00')
            
            for item in order_items:
                quantity = Decimal(str(item.get('quantity', 0)))
                unit_price = Decimal(str(item.get('unit_price', 0)))
                
                if quantity < 0 or unit_price < 0:
                    raise ValueError(f"Invalid quantity ({quantity}) or price ({unit_price})")
                
                item_total = quantity * unit_price
                subtotal += item_total
            
            return subtotal.quantize(self.precision, rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Error calculating subtotal: {str(e)}")
            raise ValueError(f"Invalid order items data: {str(e)}")
    
    def apply_discount(self, subtotal: Decimal, discount_code: Optional[str] = None, 
                      discount_percentage: Optional[float] = None,
                      discount_amount: Optional[float] = None) -> Tuple[Decimal, Decimal]:
        """
        Apply discount to the subtotal.
        
        Args:
            subtotal (Decimal): Original subtotal
            discount_code (str, optional): Discount code for predefined discounts
            discount_percentage (float, optional): Percentage discount (0-100)
            discount_amount (float, optional): Fixed discount amount
        
        Returns:
            Tuple[Decimal, Decimal]: (discounted_amount, discount_applied)
        """
        try:
            discount_applied = Decimal('0.00')
            
            # Predefined discount codes
            discount_codes = {
                'WELCOME10': {'type': 'percentage', 'value': 10},
                'SAVE20': {'type': 'percentage', 'value': 20},
                'NEWUSER': {'type': 'amount', 'value': 15.00},
                'FREESHIP': {'type': 'percentage', 'value': 5},
                'BULK25': {'type': 'percentage', 'value': 25, 'min_amount': 100.00}
            }
            
            # Apply discount code if provided
            if discount_code and discount_code.upper() in discount_codes:
                code_info = discount_codes[discount_code.upper()]
                
                # Check minimum amount requirement
                if 'min_amount' in code_info and subtotal < Decimal(str(code_info['min_amount'])):
                    raise ValueError(f"Minimum order amount of ${code_info['min_amount']} required for {discount_code}")
                
                if code_info['type'] == 'percentage':
                    discount_applied = subtotal * (Decimal(str(code_info['value'])) / Decimal('100'))
                elif code_info['type'] == 'amount':
                    discount_applied = Decimal(str(code_info['value']))
            
            # Apply percentage discount if provided
            elif discount_percentage is not None:
                if not (0 <= discount_percentage <= 100):
                    raise ValueError("Discount percentage must be between 0 and 100")
                discount_applied = subtotal * (Decimal(str(discount_percentage)) / Decimal('100'))
            
            # Apply fixed amount discount if provided
            elif discount_amount is not None:
                if discount_amount < 0:
                    raise ValueError("Discount amount cannot be negative")
                discount_applied = Decimal(str(discount_amount))
            
            # Ensure discount doesn't exceed subtotal
            if discount_applied > subtotal:
                discount_applied = subtotal
            
            discounted_amount = subtotal - discount_applied
            
            return (
                discounted_amount.quantize(self.precision, rounding=ROUND_HALF_UP),
                discount_applied.quantize(self.precision, rounding=ROUND_HALF_UP)
            )
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error applying discount: {str(e)}")
            raise ValueError(f"Invalid discount parameters: {str(e)}")
    
    def calculate_tax(self, taxable_amount: Decimal, tax_region: str = 'DEFAULT',
                     tax_exempt: bool = False) -> Decimal:
        """
        Calculate tax amount based on taxable amount and region.
        
        Args:
            taxable_amount (Decimal): Amount subject to tax
            tax_region (str): Tax region/state code
            tax_exempt (bool): Whether the order is tax exempt
        
        Returns:
            Decimal: Tax amount
        """
        try:
            if tax_exempt or taxable_amount <= 0:
                return Decimal('0.00')
            
            tax_rate = self.TAX_RATES.get(tax_region.upper(), self.TAX_RATES['DEFAULT'])
            tax_amount = taxable_amount * tax_rate
            
            return tax_amount.quantize(self.precision, rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Error calculating tax: {str(e)}")
            raise ValueError(f"Invalid tax calculation parameters: {str(e)}")
    
    def calculate_shipping(self, subtotal: Decimal, shipping_method: str = 'standard',
                          total_weight: float = 1.0, shipping_address: Optional[Dict] = None) -> Decimal:
        """
        Calculate shipping cost based on method, weight, and destination.
        
        Args:
            subtotal (Decimal): Order subtotal for free shipping calculation
            shipping_method (str): Shipping method ('standard', 'express', 'overnight')
            total_weight (float): Total weight in kg
            shipping_address (Dict, optional): Shipping address for distance calculation
        
        Returns:
            Decimal: Shipping cost
        """
        try:
            if shipping_method not in self.SHIPPING_RATES:
                shipping_method = 'standard'
            
            shipping_config = self.SHIPPING_RATES[shipping_method]
            
            # Check for free shipping threshold
            if subtotal >= shipping_config['free_shipping_threshold']:
                return Decimal('0.00')
            
            # Calculate base shipping cost
            base_rate = shipping_config['base_rate']
            weight_rate = shipping_config['per_kg']
            
            # Ensure minimum weight
            if total_weight < 0.1:
                total_weight = 0.1
            
            weight_cost = Decimal(str(total_weight)) * weight_rate
            total_shipping = base_rate + weight_cost
            
            # Apply distance multiplier if address provided
            if shipping_address:
                distance_multiplier = self._calculate_distance_multiplier(shipping_address)
                total_shipping *= distance_multiplier
            
            return total_shipping.quantize(self.precision, rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Error calculating shipping: {str(e)}")
            raise ValueError(f"Invalid shipping calculation parameters: {str(e)}")
    
    def _calculate_distance_multiplier(self, shipping_address: Dict) -> Decimal:
        """
        Calculate distance multiplier based on shipping address.
        
        Args:
            shipping_address (Dict): Address information
        
        Returns:
            Decimal: Distance multiplier (1.0 for local, up to 2.0 for international)
        """
        # Simplified distance calculation - in real implementation,
        # this would use actual distance calculation APIs
        country = shipping_address.get('country', 'US').upper()
        state = shipping_address.get('state', '').upper()
        
        if country != 'US':
            return Decimal('2.0')  # International shipping
        elif state in ['CA', 'NY', 'TX', 'FL']:
            return Decimal('1.0')  # Local shipping
        else:
            return Decimal('1.3')  # Domestic but distant
    
    def calculate_order_total(self, order_items: List[Dict], 
                             discount_code: Optional[str] = None,
                             discount_percentage: Optional[float] = None,
                             discount_amount: Optional[float] = None,
                             tax_region: str = 'DEFAULT',
                             tax_exempt: bool = False,
                             shipping_method: str = 'standard',
                             total_weight: float = 1.0,
                             shipping_address: Optional[Dict] = None) -> Dict:
        """
        Calculate complete order total with all components.
        
        Args:
            order_items (List[Dict]): List of order items
            discount_code (str, optional): Discount code
            discount_percentage (float, optional): Percentage discount
            discount_amount (float, optional): Fixed discount amount
            tax_region (str): Tax region code
            tax_exempt (bool): Tax exemption status
            shipping_method (str): Shipping method
            total_weight (float): Total order weight
            shipping_address (Dict, optional): Shipping address
        
        Returns:
            Dict: Complete pricing breakdown
        """
        try:
            # Calculate subtotal
            subtotal = self.calculate_subtotal(order_items)
            
            # Apply discount
            discounted_subtotal, discount_applied = self.apply_discount(
                subtotal, discount_code, discount_percentage, discount_amount
            )
            
            # Calculate tax on discounted amount
            tax_amount = self.calculate_tax(discounted_subtotal, tax_region, tax_exempt)
            
            # Calculate shipping
            shipping_cost = self.calculate_shipping(
                discounted_subtotal, shipping_method, total_weight, shipping_address
            )
            
            # Calculate final total
            final_total = discounted_subtotal + tax_amount + shipping_cost
            
            return {
                'subtotal': float(subtotal),
                'discount_applied': float(discount_applied),
                'discounted_subtotal': float(discounted_subtotal),
                'tax_amount': float(tax_amount),
                'shipping_cost': float(shipping_cost),
                'final_total': float(final_total),
                'tax_region': tax_region,
                'shipping_method': shipping_method,
                'calculations': {
                    'tax_rate': float(self.TAX_RATES.get(tax_region.upper(), self.TAX_RATES['DEFAULT'])),
                    'free_shipping_threshold': float(self.SHIPPING_RATES[shipping_method]['free_shipping_threshold']),
                    'total_weight': total_weight
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating order total: {str(e)}")
            raise ValueError(f"Failed to calculate order total: {str(e)}")


# Convenience functions for quick calculations
def calculate_simple_total(items: List[Dict], tax_rate: float = 0.07) -> Dict:
    """
    Simple total calculation for basic use cases.
    
    Args:
        items (List[Dict]): Order items with 'quantity' and 'unit_price'
        tax_rate (float): Tax rate as decimal (e.g., 0.07 for 7%)
    
    Returns:
        Dict: Basic pricing breakdown
    """
    calculator = PricingCalculator()
    subtotal = calculator.calculate_subtotal(items)
    tax_amount = subtotal * Decimal(str(tax_rate))
    total = subtotal + tax_amount
    
    return {
        'subtotal': float(subtotal),
        'tax_amount': float(tax_amount.quantize(calculator.precision, rounding=ROUND_HALF_UP)),
        'total': float(total.quantize(calculator.precision, rounding=ROUND_HALF_UP))
    }


def validate_pricing_data(order_data: Dict) -> bool:
    """
    Validate order data for pricing calculations.
    
    Args:
        order_data (Dict): Order data to validate
    
    Returns:
        bool: True if valid, raises ValueError if invalid
    """
    required_fields = ['order_items']
    
    for field in required_fields:
        if field not in order_data:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(order_data['order_items'], list):
        raise ValueError("order_items must be a list")
    
    for item in order_data['order_items']:
        if not isinstance(item, dict):
            raise ValueError("Each order item must be a dictionary")
        
        required_item_fields = ['quantity', 'unit_price']
        for field in required_item_fields:
            if field not in item:
                raise ValueError(f"Missing required item field: {field}")
        
        try:
            quantity = float(item['quantity'])
            unit_price = float(item['unit_price'])
            
            if quantity < 0 or unit_price < 0:
                raise ValueError("Quantity and unit_price must be non-negative")
                
        except (ValueError, TypeError):
            raise ValueError("Quantity and unit_price must be valid numbers")
    
    return True