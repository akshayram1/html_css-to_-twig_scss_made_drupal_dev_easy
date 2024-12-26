import re
import streamlit as st
from bs4 import BeautifulSoup
from copy import deepcopy

def parse_variable_file(variable_content):
    """Parses the SCSS variable content and returns a mapping of color names to their values."""
    variables = {}
    
    # Process each line
    for line in variable_content.splitlines():
        # Skip comments and empty lines
        if not line.strip() or line.strip().startswith('//'):
            continue
            
        # Enhanced variable pattern to catch more SCSS variable formats
        var_match = re.match(r'^\s*\$([\w-]+):\s*([^;]+)\s*(!default)?\s*;', line)
        
        if var_match:
            var_name = var_match.group(1)
            var_value = var_match.group(2).strip()
            
            # Clean up the value (remove any extra spaces or quotes)
            var_value = var_value.strip('"\'')
            
            # Store the mapping in both directions for more reliable replacement
            if re.match(r'^(#[a-fA-F0-9]{3,6}|rgba?\([^)]+\))$', var_value):
                variables[var_value.upper()] = f"${var_name}"  # Store uppercase version
                variables[var_value.lower()] = f"${var_name}"  # Store lowercase version
                st.write(f"Found color variable: ${var_name} = {var_value}")
    
    st.write(f"Total variables found: {len(variables) // 2}")  # Divide by 2 because we store each color twice
    return variables

def convert_css_to_scss(css_content, variable_mapping):
    """Converts CSS content to SCSS by replacing color values with variable names."""
    st.write("Starting CSS to SCSS conversion...")
    
    def replace_color(match):
        """Helper function to replace colors in regex matches"""
        color = match.group(0)
        # Try both upper and lower case versions of the color
        return variable_mapping.get(color.upper(), variable_mapping.get(color.lower(), color))
    
    # Process the content line by line
    result_lines = []
    for line in css_content.splitlines():
        processed_line = line
        
        # Handle comments and regular content separately
        parts = re.split(r'(/\*.*?\*/)', processed_line)
        
        for i in range(len(parts)):
            if not parts[i].startswith('/*'):
                # Replace hex colors (#fff, #ffffff)
                parts[i] = re.sub(r'#[0-9a-fA-F]{3,6}\b', replace_color, parts[i])
                
                # Replace rgba/rgb colors
                parts[i] = re.sub(r'rgba?\([^)]+\)', replace_color, parts[i])
        
        processed_line = ''.join(parts)
        
        # Debug output if line was changed
        if processed_line != line:
            st.write(f"Replaced colors in line:\nFrom: {line}\nTo:   {processed_line}")
        
        result_lines.append(processed_line)
    
    return '\n'.join(result_lines)

# Streamlit app
st.title("SCSS Variable Converter")

# File uploaders
css_file = st.file_uploader("Upload CSS File", type=["css"])
variables_file = st.file_uploader("Upload SCSS Variables File", type=["scss"])

if css_file and variables_file:
    try:
        css_content = css_file.read().decode("utf-8")
        variables_content = variables_file.read().decode("utf-8")
        
        st.write("Processing files...")
        st.write("---")
        
        # Create variable mapping
        variable_mapping = parse_variable_file(variables_content)
        
        if variable_mapping:
            # Convert CSS to SCSS
            scss_content = convert_css_to_scss(css_content, variable_mapping)
            
            if scss_content:
                st.subheader("SCSS Output")
                st.code(scss_content, language="scss")
                st.download_button(
                    "Download SCSS File",
                    data=scss_content,
                    file_name="converted.scss",
                    mime="text/plain"
                )
            else:
                st.error("No content was generated after conversion.")
        else:
            st.error("No valid color variables found in the variables file.")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Error details:", str(e))