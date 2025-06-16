import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import random
import os
import json
import math
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import threading
import time

# ==================== REGEX VALIDATION PATTERNS ====================

class PlantValidationPatterns:
    """
    Define regular expression patterns for plant data validation
    Using various metacharacters and pattern matching techniques
    """
    
    # Plant name validation - allows letters, numbers, spaces, hyphens, apostrophes
    # ^: Start of string, $: End of string, []: Character class, +: One or more, {}: Quantifiers
    PLANT_NAME = r"^[A-Za-z0-9\s\-']{2,30}$"
    
    # Plant type validation - exact matches only
    # |: OR operator, (): Grouping
    PLANT_TYPE = r"^(Flower|Herb|Succulent|Vegetable|Tree)$"
    
    # Care notes validation - allows letters, numbers, spaces, and common punctuation
    # \w: Word characters, \s: Whitespace, \.: Literal dot, ?: Zero or one, *: Zero or more
    CARE_NOTES = r"^[\w\s\.,!?'-]{0,200}$"
    
    # Numeric value validation for plant stats (0-100)
    # \d: Digits, {1,3}: 1 to 3 digits, (?:...): Non-capturing group
    STAT_VALUE = r"^(?:100|[1-9]?\d)$"
    
    # Plant ID validation - alphanumeric with optional prefix
    # [A-Z]: Uppercase letters, \d{4}: Exactly 4 digits
    PLANT_ID = r"^PLT-[A-Z]{2}\d{4}$"
    
    # Date validation (YYYY-MM-DD format)
    # \d{4}: Exactly 4 digits, -: Literal hyphen
    DATE_FORMAT = r"^\d{4}-\d{2}-\d{2}$"
    
    # Time validation (HH:MM format)
    # [0-2]: Character range, [0-5]: Character range
    TIME_FORMAT = r"^[0-2]\d:[0-5]\d$"
    
    # Email validation for garden sharing features
    # [^@]: Not @ character, +: One or more, \.?: Optional dot
    EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    # Garden location validation (City, State/Country format)
    # \w+: One or more word characters, \s*: Zero or more spaces
    LOCATION = r"^[A-Za-z\s]+,\s*[A-Za-z\s]+$"
    
    # Disease name validation - specific medical/botanical terms
    # (?i): Case insensitive flag, \b: Word boundary
    DISEASE_NAME = r"(?i)^(root\s+rot|aphids?|fungal\s+infection|nutrient\s+deficiency|overwatering|sunburn|leaf\s+spot|powdery\s+mildew)$"
    
    # Water amount validation - supports decimal values
    # \.: Literal dot, ?: Zero or one occurrence
    WATER_AMOUNT = r"^(?:[1-9]\d?|100)(?:\.\d{1,2})?$"
    
    # Hex color code validation for plant colors
    # [A-Fa-f0-9]: Hexadecimal characters, {6}: Exactly 6 characters
    HEX_COLOR = r"^#[A-Fa-f0-9]{6}$"
    
    # Plant trait validation - predefined traits only
    PLANT_TRAIT = r"^(Fast Growing|Drought Resistant|Disease Resistant|High Yield|Colorful|Fragrant|Cold Hardy|Heat Tolerant|Low Maintenance|Decorative)$"
    
    # Season validation
    SEASON = r"^(Spring|Summer|Fall|Autumn|Winter)$"
    
    # Weather condition validation
    WEATHER = r"^(Sunny|Rainy|Cloudy|Windy|Stormy|Foggy|Snow)$"

class RegexValidator:
    """
    Utility class for performing regex validation with detailed error messages
    """
    
    @staticmethod
    def validate_pattern(value: str, pattern: str, field_name: str = "Field") -> Tuple[bool, str]:
        """
        Validate a value against a regex pattern
        Returns (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{field_name} must be a string"
        
        if re.match(pattern, value):
            return True, ""
        else:
            return False, f"{field_name} format is invalid"
    
    @staticmethod
    def extract_pattern_info(value: str, pattern: str) -> List[str]:
        """
        Extract all matches from a string using a pattern
        Useful for finding specific elements in text
        """
        return re.findall(pattern, value)
    
    @staticmethod
    def sanitize_input(value: str, allowed_pattern: str) -> str:
        """
        Remove characters that don't match the allowed pattern
        """
        # Find all valid characters and join them
        valid_chars = re.findall(allowed_pattern, value)
        return ''.join(valid_chars)
    
    @staticmethod
    def validate_plant_data(plant_data: dict) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation of plant data using multiple regex patterns
        """
        errors = []
        
        # Validate plant name
        if 'name' in plant_data:
            is_valid, error = RegexValidator.validate_pattern(
                plant_data['name'], 
                PlantValidationPatterns.PLANT_NAME, 
                "Plant name"
            )
            if not is_valid:
                errors.append("Plant name must be 2-30 characters, letters, numbers, spaces, hyphens, or apostrophes only")
        
        # Validate plant type
        if 'type' in plant_data:
            is_valid, error = RegexValidator.validate_pattern(
                plant_data['type'], 
                PlantValidationPatterns.PLANT_TYPE, 
                "Plant type"
            )
            if not is_valid:
                errors.append("Plant type must be one of: Flower, Herb, Succulent, Vegetable, Tree")
        
        # Validate care notes if present
        if 'care_notes' in plant_data and plant_data['care_notes']:
            is_valid, error = RegexValidator.validate_pattern(
                plant_data['care_notes'], 
                PlantValidationPatterns.CARE_NOTES, 
                "Care notes"
            )
            if not is_valid:
                errors.append("Care notes can only contain letters, numbers, spaces, and basic punctuation (max 200 characters)")
        
        # Validate location if present
        if 'location' in plant_data and plant_data['location']:
            is_valid, error = RegexValidator.validate_pattern(
                plant_data['location'], 
                PlantValidationPatterns.LOCATION, 
                "Location"
            )
            if not is_valid:
                errors.append("Location must be in format: City, State/Country")
        
        # Validate email if present
        if 'owner_email' in plant_data and plant_data['owner_email']:
            is_valid, error = RegexValidator.validate_pattern(
                plant_data['owner_email'], 
                PlantValidationPatterns.EMAIL, 
                "Email"
            )
            if not is_valid:
                errors.append("Email format is invalid")
        
        return len(errors) == 0, errors

class ValidatedPlant:
    """
    Enhanced Plant class with regex validation for all inputs
    """
    
    def __init__(self, name: str, plant_type: str, **kwargs):
        # Validate required fields
        plant_data = {
            'name': name,
            'type': plant_type,
            **kwargs
        }
        
        is_valid, errors = RegexValidator.validate_plant_data(plant_data)
        if not is_valid:
            raise ValueError(f"Invalid plant data: {'; '.join(errors)}")
        
        self.plant_id = self._generate_plant_id()
        self.name = name
        self.plant_type = plant_type
        self.created_date = datetime.now()
        self.care_notes = kwargs.get('care_notes', '')
        self.location = kwargs.get('location', '')
        self.owner_email = kwargs.get('owner_email', '')
        
        # Plant stats with validation
        self.health = self._validate_stat_value(kwargs.get('health', 50))
        self.water_level = self._validate_stat_value(kwargs.get('water_level', 50))
        self.nutrients = self._validate_stat_value(kwargs.get('nutrients', 50))
        self.sunlight = self._validate_stat_value(kwargs.get('sunlight', 50))
        
        self.diseases = []
        self.care_history = []
        self.special_traits = []
        
    def _generate_plant_id(self) -> str:
        """Generate a validated plant ID using regex pattern"""
        # Generate random plant ID that matches PLT-XX0000 pattern
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        numbers = ''.join(random.choices('0123456789', k=4))
        plant_id = f"PLT-{letters}{numbers}"
        
        # Validate the generated ID
        is_valid, _ = RegexValidator.validate_pattern(
            plant_id, 
            PlantValidationPatterns.PLANT_ID, 
            "Plant ID"
        )
        
        if not is_valid:
            # Fallback to a known good pattern
            plant_id = f"PLT-AA{random.randint(1000, 9999)}"
        
        return plant_id
    
    def _validate_stat_value(self, value) -> float:
        """Validate and convert stat values (0-100)"""
        str_value = str(value)
        is_valid, _ = RegexValidator.validate_pattern(
            str_value, 
            PlantValidationPatterns.STAT_VALUE, 
            "Stat value"
        )
        
        if is_valid:
            return float(value)
        else:
            # Return default safe value
            return 50.0
    
    def add_care_note(self, note: str) -> bool:
        """Add a care note with validation"""
        is_valid, error = RegexValidator.validate_pattern(
            note, 
            PlantValidationPatterns.CARE_NOTES, 
            "Care note"
        )
        
        if is_valid:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.care_history.append({
                'timestamp': timestamp,
                'note': note,
                'type': 'manual_note'
            })
            return True
        else:
            print(f"Invalid care note: {error}")
            return False
    
    def add_disease(self, disease_name: str) -> bool:
        """Add a disease with name validation"""
        is_valid, error = RegexValidator.validate_pattern(
            disease_name, 
            PlantValidationPatterns.DISEASE_NAME, 
            "Disease name"
        )
        
        if is_valid:
            if disease_name.lower() not in [d['name'].lower() for d in self.diseases]:
                self.diseases.append({
                    'name': disease_name,
                    'diagnosed_date': datetime.now().strftime("%Y-%m-%d"),
                    'severity': random.randint(1, 10)
                })
            return True
        else:
            print(f"Invalid disease name: {error}")
            return False
    
    def water_plant(self, amount_str: str) -> bool:
        """Water the plant with amount validation"""
        is_valid, error = RegexValidator.validate_pattern(
            amount_str, 
            PlantValidationPatterns.WATER_AMOUNT, 
            "Water amount"
        )
        
        if is_valid:
            amount = float(amount_str)
            self.water_level = min(100, self.water_level + amount)
            self.add_care_note(f"Watered with {amount} units")
            return True
        else:
            print(f"Invalid water amount: {error}")
            return False
    
    def add_trait(self, trait: str) -> bool:
        """Add a special trait with validation"""
        is_valid, error = RegexValidator.validate_pattern(
            trait, 
            PlantValidationPatterns.PLANT_TRAIT, 
            "Plant trait"
        )
        
        if is_valid and trait not in self.special_traits:
            self.special_traits.append(trait)
            return True
        else:
            if not is_valid:
                print(f"Invalid plant trait: {error}")
            return False
    
    def get_validation_report(self) -> dict:
        """Generate a comprehensive validation report for the plant"""
        report = {
            'plant_id': self.plant_id,
            'validations': {},
            'errors': [],
            'warnings': []
        }
        
        # Check all validation patterns
        validations = [
            ('name', self.name, PlantValidationPatterns.PLANT_NAME),
            ('type', self.plant_type, PlantValidationPatterns.PLANT_TYPE),
            ('plant_id', self.plant_id, PlantValidationPatterns.PLANT_ID),
        ]
        
        if self.care_notes:
            validations.append(('care_notes', self.care_notes, PlantValidationPatterns.CARE_NOTES))
        
        if self.location:
            validations.append(('location', self.location, PlantValidationPatterns.LOCATION))
        
        if self.owner_email:
            validations.append(('owner_email', self.owner_email, PlantValidationPatterns.EMAIL))
        
        for field_name, value, pattern in validations:
            is_valid, error = RegexValidator.validate_pattern(value, pattern, field_name)
            report['validations'][field_name] = {
                'value': value,
                'valid': is_valid,
                'pattern': pattern
            }
            if not is_valid:
                report['errors'].append(f"{field_name}: {error}")
        
        # Check diseases
        for disease in self.diseases:
            is_valid, error = RegexValidator.validate_pattern(
                disease['name'], 
                PlantValidationPatterns.DISEASE_NAME, 
                "Disease"
            )
            if not is_valid:
                report['warnings'].append(f"Invalid disease name: {disease['name']}")
        
        # Check traits
        for trait in self.special_traits:
            is_valid, error = RegexValidator.validate_pattern(
                trait, 
                PlantValidationPatterns.PLANT_TRAIT, 
                "Trait"
            )
            if not is_valid:
                report['warnings'].append(f"Invalid trait: {trait}")
        
        return report

class PlantDataAnalyzer:
    """
    Use regex patterns to analyze and extract information from plant data
    """
    
    @staticmethod
    def extract_plant_mentions(text: str) -> List[str]:
        """Extract plant mentions from text using regex"""
        # Pattern to find plant-related words
        plant_pattern = r'\b(?:flower|herb|succulent|vegetable|tree|plant|bloom|leaf|root|stem)\b'
        return re.findall(plant_pattern, text, re.IGNORECASE)
    
    @staticmethod
    def extract_dates_from_notes(care_history: List[dict]) -> List[str]:
        """Extract all dates from care notes"""
        dates = []
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        
        for entry in care_history:
            if 'note' in entry:
                found_dates = re.findall(date_pattern, entry['note'])
                dates.extend(found_dates)
        
        return dates
    
    @staticmethod
    def extract_numeric_values(text: str) -> List[str]:
        """Extract numeric values from text"""
        # Pattern for numbers (integer or decimal)
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        return re.findall(number_pattern, text)
    
    @staticmethod
    def validate_garden_data_batch(gardens_data: List[dict]) -> dict:
        """Validate multiple garden records using regex patterns"""
        results = {
            'total_records': len(gardens_data),
            'valid_records': 0,
            'invalid_records': 0,
            'validation_errors': [],
            'pattern_matches': {}
        }
        
        for i, garden_data in enumerate(gardens_data):
            is_valid, errors = RegexValidator.validate_plant_data(garden_data)
            
            if is_valid:
                results['valid_records'] += 1
            else:
                results['invalid_records'] += 1
                results['validation_errors'].append({
                    'record_index': i,
                    'errors': errors,
                    'data': garden_data
                })
        
        return results
    
    @staticmethod
    def generate_plant_statistics(plants: List[ValidatedPlant]) -> dict:
        """Generate statistics using regex pattern matching"""
        stats = {
            'total_plants': len(plants),
            'plants_by_type': {},
            'common_traits': {},
            'disease_frequency': {},
            'location_distribution': {},
            'email_domains': {}
        }
        
        for plant in plants:
            # Count by type
            plant_type = plant.plant_type
            stats['plants_by_type'][plant_type] = stats['plants_by_type'].get(plant_type, 0) + 1
            
            # Count traits
            for trait in plant.special_traits:
                stats['common_traits'][trait] = stats['common_traits'].get(trait, 0) + 1
            
            # Count diseases
            for disease in plant.diseases:
                disease_name = disease['name']
                stats['disease_frequency'][disease_name] = stats['disease_frequency'].get(disease_name, 0) + 1
            
            # Extract location information
            if plant.location:
                # Use regex to extract city and state/country
                location_parts = re.findall(r'([^,]+),\s*(.+)', plant.location)
                if location_parts:
                    city, state_country = location_parts[0]
                    stats['location_distribution'][state_country.strip()] = \
                        stats['location_distribution'].get(state_country.strip(), 0) + 1
            
            # Extract email domains
            if plant.owner_email:
                domain_match = re.search(r'@([a-zA-Z0-9.-]+)', plant.owner_email)
                if domain_match:
                    domain = domain_match.group(1)
                    stats['email_domains'][domain] = stats['email_domains'].get(domain, 0) + 1
        
        return stats

# ==================== ENHANCED UI WITH VALIDATION ====================

class ValidatedAddPlantDialog(tk.Toplevel):
    """
    Enhanced add plant dialog with real-time regex validation
    """
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Add New Plant - With Validation")
        self.geometry("600x800")
        self.configure(bg="#f4f9f4")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 800) // 2
        self.geometry(f"+{x}+{y}")
        
        self.setup_validation_ui()
    
    def setup_validation_ui(self):
        # Main container
        main_frame = tk.Frame(self, bg="#f4f9f4", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🌱 Add New Plant (With Validation)", 
                              font=("Helvetica", 16, "bold"), 
                              bg="#f4f9f4", fg="#2c3639")
        title_label.pack(pady=(0, 20))
        
        # Validation status indicator
        self.validation_frame = tk.Frame(main_frame, bg="#f4f9f4")
        self.validation_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.validation_label = tk.Label(self.validation_frame, 
                                        text="🔍 Real-time validation active", 
                                        font=("Helvetica", 10), 
                                        bg="#f4f9f4", fg="#526d82")
        self.validation_label.pack()
        
        # Plant name with validation
        self.create_validated_field(
            main_frame, 
            "Plant Name", 
            PlantValidationPatterns.PLANT_NAME,
            "2-30 characters: letters, numbers, spaces, hyphens, apostrophes",
            "name_entry"
        )
        
        # Plant type dropdown
        type_frame = tk.LabelFrame(main_frame, text="Plant Type", 
                                 bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        type_frame.pack(fill=tk.X, pady=10)
        
        self.plant_type = tk.StringVar(value="Flower")
        type_combo = ttk.Combobox(type_frame, textvariable=self.plant_type,
                                 values=["Flower", "Herb", "Succulent", "Vegetable", "Tree"],
                                 state="readonly")
        type_combo.pack(fill=tk.X, padx=10, pady=5)
        
        # Care notes with validation
        self.create_validated_field(
            main_frame, 
            "Care Notes (Optional)", 
            PlantValidationPatterns.CARE_NOTES,
            "Letters, numbers, spaces, basic punctuation (max 200 chars)",
            "care_notes_entry",
            is_text=True
        )
        
        # Location with validation
        self.create_validated_field(
            main_frame, 
            "Location (Optional)", 
            PlantValidationPatterns.LOCATION,
            "Format: City, State/Country",
            "location_entry"
        )
        
        # Owner email with validation
        self.create_validated_field(
            main_frame, 
            "Owner Email (Optional)", 
            PlantValidationPatterns.EMAIL,
            "Valid email address format",
            "email_entry"
        )
        
        # Validation summary
        self.create_validation_summary(main_frame)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#f4f9f4")
        button_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(button_frame, text="Cancel", 
                 font=("Helvetica", 11), command=self.destroy).pack(side=tk.LEFT)
        
        self.add_button = tk.Button(button_frame, text="Add Plant", 
                                   font=("Helvetica", 11, "bold"),
                                   bg="#8ac586", fg="white",
                                   command=self.add_plant)
        self.add_button.pack(side=tk.RIGHT)
        
        # Initial validation
        self.validate_all_fields()
    
    def create_validated_field(self, parent, label_text, pattern, help_text, attr_name, is_text=False):
        """Create a form field with real-time regex validation"""
        field_frame = tk.LabelFrame(parent, text=label_text, 
                                  bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        field_frame.pack(fill=tk.X, pady=10)
        
        # Entry or Text widget
        if is_text:
            widget = tk.Text(field_frame, height=4, font=("Helvetica", 10))
        else:
            widget = tk.Entry(field_frame, font=("Helvetica", 11))
        
        widget.pack(fill=tk.X, padx=10, pady=5)
        
        # Help text
        help_label = tk.Label(field_frame, text=f"ℹ️ {help_text}", 
                            font=("Helvetica", 9), 
                            bg="#f4f9f4", fg="#526d82")
        help_label.pack(anchor="w", padx=10)
        
        # Validation indicator
        validation_indicator = tk.Label(field_frame, text="", 
                                      font=("Helvetica", 9), 
                                      bg="#f4f9f4")
        validation_indicator.pack(anchor="w", padx=10, pady=(0, 5))
        
        # Store references
        setattr(self, attr_name, widget)
        setattr(self, f"{attr_name}_indicator", validation_indicator)
        setattr(self, f"{attr_name}_pattern", pattern)
        
        # Bind validation events
        if is_text:
            widget.bind("<KeyRelease>", lambda e: self.validate_field(attr_name))
            widget.bind("<FocusOut>", lambda e: self.validate_field(attr_name))
        else:
            widget.bind("<KeyRelease>", lambda e: self.validate_field(attr_name))
            widget.bind("<FocusOut>", lambda e: self.validate_field(attr_name))
    
    def get_field_value(self, attr_name):
        """Get value from entry or text widget"""
        widget = getattr(self, attr_name)
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        else:
            return widget.get().strip()
    
    def validate_field(self, attr_name):
        """Validate a specific field using its regex pattern"""
        value = self.get_field_value(attr_name)
        pattern = getattr(self, f"{attr_name}_pattern")
        indicator = getattr(self, f"{attr_name}_indicator")
        
        # Skip validation for optional empty fields
        if not value and "Optional" in attr_name:
            indicator.config(text="✓ Optional field", fg="#526d82")
            return True
        
        # Validate against pattern
        is_valid, error = RegexValidator.validate_pattern(value, pattern)
        
        if is_valid:
            indicator.config(text="✓ Valid format", fg="#2a9d8f")
            return True
        else:
            indicator.config(text="✗ Invalid format", fg="#e76f51")
            return False
    
    def validate_all_fields(self):
        """Validate all fields and update UI accordingly"""
        field_names = ['name_entry', 'care_notes_entry', 'location_entry', 'email_entry']
        all_valid = True
        
        for field_name in field_names:
            if hasattr(self, field_name):
                field_valid = self.validate_field(field_name)
                value = self.get_field_value(field_name)
                
                # Required fields must be valid and non-empty
                if field_name == 'name_entry':
                    if not value or not field_valid:
                        all_valid = False
                elif value and not field_valid:  # Optional fields must be valid if filled
                    all_valid = False
        
        # Update add button state
        if all_valid:
            self.add_button.config(state=tk.NORMAL, bg="#8ac586")
            self.validation_label.config(text="✅ All fields valid", fg="#2a9d8f")
        else:
            self.add_button.config(state=tk.DISABLED, bg="#cccccc")
            self.validation_label.config(text="❌ Please fix validation errors", fg="#e76f51")
        
        # Schedule next validation
        self.after(500, self.validate_all_fields)
    
    def create_validation_summary(self, parent):
        """Create a summary of regex patterns being used"""
        summary_frame = tk.LabelFrame(parent, text="🔍 Validation Patterns Used", 
                                    bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        summary_frame.pack(fill=tk.X, pady=10)
        
        patterns_text = """
Pattern Examples:
• Plant Name: ^[A-Za-z0-9\\s\\-']{2,30}$ (letters, numbers, spaces, hyphens, apostrophes)
• Email: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$ (standard email format)
• Location: ^[A-Za-z\\s]+,\\s*[A-Za-z\\s]+$ (City, State format)
• Care Notes: ^[\\w\\s\\.,!?'-]{0,200}$ (basic text with punctuation)

Metacharacters Used:
^ = Start of string, $ = End of string, [] = Character class, + = One or more
* = Zero or more, ? = Zero or one, {n,m} = Quantifiers, \\ = Escape character
        """
        
        tk.Label(summary_frame, text=patterns_text, 
                font=("Courier", 8), 
                bg="#f4f9f4", fg="#526d82",
                justify=tk.LEFT).pack(anchor="w", padx=10, pady=5)
    
    def add_plant(self):
        """Add plant with comprehensive validation"""
        plant_data = {
            'name': self.get_field_value('name_entry'),
            'type': self.plant_type.get(),
            'care_notes': self.get_field_value('care_notes_entry'),
            'location': self.get_field_value('location_entry'),
            'owner_email': self.get_field_value('email_entry')
        }
        
        # Final validation
        is_valid, errors = RegexValidator.validate_plant_data(plant_data)
        
        if is_valid:
            try:
                # Create validated plant
                plant = ValidatedPlant(**plant_data)
                
                # Show validation report
                report = plant.get_validation_report()
                
                if self.callback:
                    self.callback(plant, report)
                
                self.destroy()
                
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
        else:
            error_message = "Validation failed:\n" + "\n".join(errors)
            messagebox.showerror("Validation Error", error_message)

# ==================== DEMO AND TESTING ====================

class RegexDemoApp:
    """
    Demonstration application showing regex validation in action
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌿 GrowBuddy - Regex Validation Demo")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f4f9f4")
        
        self.plants = []
        self.setup_demo_ui()
        
    def setup_demo_ui(self):
        # Title
        title_label = tk.Label(self.root, text="🌿 GrowBuddy - Regex Validation Demo", 
                              font=("Helvetica", 18, "bold"), 
                              bg="#f4f9f4", fg="#2c3639")
        title_label.pack(pady=20)
        
        # Description
        desc_text = """
This demo showcases comprehensive regex validation patterns for plant data:
• Plant names, types, and care information
• Email addresses and location formats
• Disease names and plant traits
• Numeric values and dates
• Real-time validation with visual feedback
        """
        
        tk.Label(self.root, text=desc_text, 
                font=("Helvetica", 11), 
                bg="#f4f9f4", fg="#526d82",
                justify=tk.LEFT).pack(pady=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.root, bg="#f4f9f4")
        buttons_frame.pack(pady=20)
        
        # Demo buttons
        tk.Button(buttons_frame, text="🌱 Add Plant (Validated)", 
                 font=("Helvetica", 12), bg="#8ac586", fg="white",
                 command=self.show_add_plant_dialog).pack(side=tk.LEFT, padx=10)
        
        tk.Button(buttons_frame, text="🔍 Test Patterns", 
                 font=("Helvetica", 12), bg="#66c2ff", fg="white",
                 command=self.show_pattern_tester).pack(side=tk.LEFT, padx=10)
        
        tk.Button(buttons_frame, text="📊 Generate Report", 
                 font=("Helvetica", 12), bg="#ff9f43", fg="white",
                 command=self.generate_validation_report).pack(side=tk.LEFT, padx=10)
        
        tk.Button(buttons_frame, text="💾 Demo Data", 
                 font=("Helvetica", 12), bg="#9b59b6", fg="white",
                 command=self.load_demo_data).pack(side=tk.LEFT, padx=10)
        
        # Results area
        self.results_frame = tk.Frame(self.root, bg="#f4f9f4")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Results text widget
        self.results_text = tk.Text(self.results_frame, 
                                   font=("Courier", 10), 
                                   bg="white", fg="#2c3639",
                                   wrap=tk.WORD)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.results_frame, orient="vertical", 
                               command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial message
        self.display_message("🌿 Welcome to GrowBuddy Regex Validation Demo!\n\nClick buttons above to explore validation features.")
    
    def display_message(self, message):
        """Display message in results area"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, message)
    
    def show_add_plant_dialog(self):
        """Show the validated add plant dialog"""
        dialog = ValidatedAddPlantDialog(self.root, self.plant_added_callback)
    
    def plant_added_callback(self, plant, validation_report):
        """Handle plant addition with validation report"""
        self.plants.append(plant)
        
        report_text = f"""
✅ PLANT ADDED SUCCESSFULLY!

Plant Details:
• ID: {plant.plant_id}
• Name: {plant.name}
• Type: {plant.plant_type}
• Created: {plant.created_date.strftime('%Y-%m-%d %H:%M:%S')}

Validation Report:
"""
        
        for field, details in validation_report['validations'].items():
            status = "✅ VALID" if details['valid'] else "❌ INVALID"
            report_text += f"• {field}: {status}\n  Value: '{details['value']}'\n  Pattern: {details['pattern']}\n\n"
        
        if validation_report['errors']:
            report_text += "Errors:\n"
            for error in validation_report['errors']:
                report_text += f"• {error}\n"
        
        if validation_report['warnings']:
            report_text += "Warnings:\n"
            for warning in validation_report['warnings']:
                report_text += f"• {warning}\n"
        
        self.display_message(report_text)
    
    def show_pattern_tester(self):
        """Show pattern testing interface"""
        tester_window = PatternTesterWindow(self.root)
    
    def generate_validation_report(self):
        """Generate comprehensive validation report for all plants"""
        if not self.plants:
            self.display_message("No plants added yet! Add some plants first to generate a report.")
            return
        
        # Generate statistics
        stats = PlantDataAnalyzer.generate_plant_statistics(self.plants)
        
        report_text = f"""
📊 COMPREHENSIVE VALIDATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: donlj

GARDEN STATISTICS:
• Total Plants: {stats['total_plants']}

PLANTS BY TYPE:
"""
        
        for plant_type, count in stats['plants_by_type'].items():
            report_text += f"• {plant_type}: {count}\n"
        
        if stats['common_traits']:
            report_text += "\nMOST COMMON TRAITS:\n"
            for trait, count in sorted(stats['common_traits'].items(), key=lambda x: x[1], reverse=True):
                report_text += f"• {trait}: {count} plants\n"
        
        if stats['disease_frequency']:
            report_text += "\nDISEASE FREQUENCY:\n"
            for disease, count in sorted(stats['disease_frequency'].items(), key=lambda x: x[1], reverse=True):
                report_text += f"• {disease}: {count} cases\n"
        
        if stats['location_distribution']:
            report_text += "\nLOCATION DISTRIBUTION:\n"
            for location, count in sorted(stats['location_distribution'].items(), key=lambda x: x[1], reverse=True):
                report_text += f"• {location}: {count} plants\n"
        
        if stats['email_domains']:
            report_text += "\nEMAIL DOMAINS:\n"
            for domain, count in sorted(stats['email_domains'].items(), key=lambda x: x[1], reverse=True):
                report_text += f"• {domain}: {count} users\n"
        
        report_text += "\nVALIDATION PATTERNS USED:\n"
        for attr_name, pattern in vars(PlantValidationPatterns).items():
            if not attr_name.startswith('_') and isinstance(pattern, str):
                report_text += f"• {attr_name}: {pattern}\n"
        
        self.display_message(report_text)
    
    def load_demo_data(self):
        """Load demonstration data with various validation scenarios"""
        demo_plants_data = [
            # Valid data
            {
                'name': "Rose Garden Beauty",
                'type': "Flower",
                'care_notes': "Needs daily watering and weekly fertilizer.",
                'location': "San Francisco, California",
                'owner_email': "donlj@example.com"
            },
            {
                'name': "Basil-Supreme",
                'type': "Herb",
                'care_notes': "Harvest leaves regularly for best flavor!",
                'location': "Portland, Oregon",
                'owner_email': "gardener@greenthumb.org"
            },
            {
                'name': "Desert Star",
                'type': "Succulent",
                'care_notes': "Water sparingly, once per week maximum.",
                'location': "Phoenix, Arizona",
                'owner_email': "donlj@gmail.com"
            },
            # Edge cases and validation tests
            {
                'name': "O'Malley's Tomato",  # Apostrophe test
                'type': "Vegetable",
                'care_notes': "Great for salads & sandwiches!",
                'location': "Dublin, Ireland",
                'owner_email': "test.user+garden@example.co.uk"
            }
        ]
        
        results_text = "🎯 LOADING DEMO DATA WITH VALIDATION TESTING...\n\n"
        
        for i, plant_data in enumerate(demo_plants_data, 1):
            results_text += f"Plant {i}: {plant_data['name']}\n"
            
            try:
                plant = ValidatedPlant(**plant_data)
                self.plants.append(plant)
                
                # Add some demo diseases and traits
                if i == 1:
                    plant.add_disease("Aphids")
                    plant.add_trait("Fragrant")
                elif i == 2:
                    plant.add_trait("Disease Resistant")
                    plant.add_trait("Fast Growing")
                elif i == 3:
                    plant.add_trait("Drought Resistant")
                    plant.add_trait("Low Maintenance")
                
                validation_report = plant.get_validation_report()
                error_count = len(validation_report['errors'])
                warning_count = len(validation_report['warnings'])
                
                results_text += f"  ✅ CREATED - Errors: {error_count}, Warnings: {warning_count}\n"
                
            except ValueError as e:
                results_text += f"  ❌ FAILED: {str(e)}\n"
            
            results_text += "\n"
        
        results_text += f"\n✅ Demo data loaded! Total plants: {len(self.plants)}\n"
        results_text += "Click 'Generate Report' to see detailed validation analysis."
        
        self.display_message(results_text)
    
    def run(self):
        """Start the demo application"""
        self.root.mainloop()

class PatternTesterWindow:
    """
    Interactive pattern testing window
    """
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("🔍 Regex Pattern Tester")
        self.window.geometry("700x600")
        self.window.configure(bg="#f4f9f4")
        
        self.setup_tester_ui()
    
    def setup_tester_ui(self):
        # Title
        tk.Label(self.window, text="🔍 Interactive Regex Pattern Tester", 
                font=("Helvetica", 16, "bold"), 
                bg="#f4f9f4", fg="#2c3639").pack(pady=20)
        
        # Pattern selection
        pattern_frame = tk.LabelFrame(self.window, text="Select Pattern to Test", 
                                    bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        pattern_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.pattern_var = tk.StringVar(value="PLANT_NAME")
        
        patterns = [
            ("PLANT_NAME", "Plant Name Validation"),
            ("EMAIL", "Email Address Validation"),
            ("LOCATION", "Location Format Validation"),
            ("DISEASE_NAME", "Disease Name Validation"),
            ("WATER_AMOUNT", "Water Amount Validation"),
            ("HEX_COLOR", "Hex Color Code Validation"),
            ("DATE_FORMAT", "Date Format Validation")
        ]
        
        for pattern_key, description in patterns:
            tk.Radiobutton(pattern_frame, text=f"{description} ({pattern_key})", 
                          variable=self.pattern_var, value=pattern_key,
                          bg="#f4f9f4", anchor="w").pack(fill=tk.X, padx=10, pady=2)
        
        # Test input
        input_frame = tk.LabelFrame(self.window, text="Test Input", 
                                  bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.test_input = tk.Entry(input_frame, font=("Helvetica", 12))
        self.test_input.pack(fill=tk.X, padx=10, pady=5)
        self.test_input.bind("<KeyRelease>", self.test_pattern)
        
        # Pattern display
        pattern_display_frame = tk.LabelFrame(self.window, text="Current Pattern", 
                                            bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        pattern_display_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.pattern_display = tk.Label(pattern_display_frame, text="", 
                                      font=("Courier", 10), 
                                      bg="#f4f9f4", fg="#526d82",
                                      wraplength=650)
        self.pattern_display.pack(anchor="w", padx=10, pady=5)
        
        # Results
        results_frame = tk.LabelFrame(self.window, text="Test Results", 
                                    bg="#f4f9f4", fg="#2c3639", font=("Helvetica", 10, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.results_display = tk.Text(results_frame, 
                                     font=("Courier", 10), 
                                     bg="white", fg="#2c3639")
        self.results_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bind pattern change
        self.pattern_var.trace_add("write", self.pattern_changed)
        
        # Initial setup
        self.pattern_changed()
        
        # Add some example test cases
        self.add_example_button = tk.Button(self.window, text="Load Example Test Cases", 
                                          font=("Helvetica", 10), bg="#8ac586", fg="white",
                                          command=self.load_examples)
        self.add_example_button.pack(pady=10)
    
    def pattern_changed(self, *args):
        """Update pattern display when selection changes"""
        pattern_key = self.pattern_var.get()
        pattern = getattr(PlantValidationPatterns, pattern_key, "")
        self.pattern_display.config(text=f"Pattern: {pattern}")
        self.test_pattern()
    
    def test_pattern(self, *args):
        """Test the current input against the selected pattern"""
        pattern_key = self.pattern_var.get()
        pattern = getattr(PlantValidationPatterns, pattern_key, "")
        test_value = self.test_input.get()
        
        if not test_value:
            self.results_display.delete(1.0, tk.END)
            self.results_display.insert(tk.END, "Enter text to test...")
            return
        
        # Test the pattern
        is_valid, error = RegexValidator.validate_pattern(test_value, pattern, "Test Input")
        
        result_text = f"Input: '{test_value}'\n"
        result_text += f"Pattern: {pattern}\n\n"
        
        if is_valid:
            result_text += "✅ MATCH: Input matches the pattern!\n\n"
        else:
            result_text += "❌ NO MATCH: Input does not match the pattern.\n\n"
        
        # Show pattern breakdown
        result_text += "Pattern Breakdown:\n"
        if pattern_key == "PLANT_NAME":
            result_text += "• ^ = Start of string\n"
            result_text += "• [A-Za-z0-9\\s\\-'] = Letters, numbers, spaces, hyphens, apostrophes\n"
            result_text += "• {2,30} = Length between 2 and 30 characters\n"
            result_text += "• $ = End of string\n"
        elif pattern_key == "EMAIL":
            result_text += "• [a-zA-Z0-9._%+-]+ = One or more alphanumeric chars or symbols\n"
            result_text += "• @ = Literal @ symbol\n"
            result_text += "• [a-zA-Z0-9.-]+ = Domain name characters\n"
            result_text += "• \\. = Literal dot\n"
            result_text += "• [a-zA-Z]{2,} = Two or more letters for TLD\n"
        # Add more breakdowns as needed...
        
        self.results_display.delete(1.0, tk.END)
        self.results_display.insert(tk.END, result_text)
    
    def load_examples(self):
        """Load example test cases for the selected pattern"""
        pattern_key = self.pattern_var.get()
        
        examples = {
            "PLANT_NAME": [
                "Rose Garden",      # Valid
                "Basil-Supreme",    # Valid
                "O'Malley's Oak",   # Valid
                "123 Plant",        # Valid
                "X",                # Invalid - too short
                "A" * 31,          # Invalid - too long
                "Plant@Home",       # Invalid - special character
            ],
            "EMAIL": [
                "donlj@example.com",           # Valid
                "user.name+tag@domain.org",    # Valid
                "test@sub.domain.com",         # Valid
                "invalid.email",               # Invalid - no @
                "@domain.com",                 # Invalid - no local part
                "user@",                       # Invalid - no domain
            ],
            "LOCATION": [
                "San Francisco, California",   # Valid
                "Dublin, Ireland",             # Valid
                "New York City, New York",     # Valid
                "San Francisco",               # Invalid - no comma
                "California, ",                # Invalid - empty after comma
                "123 Main St, CA",            # Invalid - numbers
            ],
            "DISEASE_NAME": [
                "Root Rot",                    # Valid
                "Aphids",                      # Valid
                "Fungal Infection",            # Valid
                "Nutrient Deficiency",         # Valid
                "Plant Cancer",                # Invalid - not recognized
                "Unknown Disease",             # Invalid - not recognized
            ]
        }
        
        if pattern_key in examples:
            example_text = f"\nExample test cases for {pattern_key}:\n\n"
            for example in examples[pattern_key]:
                self.test_input.delete(0, tk.END)
                self.test_input.insert(0, example)
                self.test_pattern()
                
                # Get result
                pattern = getattr(PlantValidationPatterns, pattern_key, "")
                is_valid, _ = RegexValidator.validate_pattern(example, pattern)
                status = "✅ VALID" if is_valid else "❌ INVALID"
                example_text += f"'{example}' - {status}\n"
            
            self.results_display.delete(1.0, tk.END)
            self.results_display.insert(tk.END, example_text)

# ==================== MAIN DEMO EXECUTION ====================

def main():
    """
    Main function to demonstrate regex validation in GrowBuddy
    """
    print("🌿 GrowBuddy Regex Validation Demo")
    print("=" * 50)
    print(f"Started by user: donlj")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run the demo application
    app = RegexDemoApp()
    app.run()

if __name__ == "__main__":
    main()