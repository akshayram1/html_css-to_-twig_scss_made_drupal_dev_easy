import re
import streamlit as st
from bs4 import BeautifulSoup
from copy import deepcopy

def parse_variable_file(variable_content):
    """Parses the SCSS variable content and returns a mapping of color names to their values."""
    variables = {}
    temp_references = {}
    
    # First pass: collect direct color definitions
    color_pattern = re.compile(r'^\s*\$([\w-]+):\s*(#[a-fA-F0-9]{3,6}|rgba?\([^)]+\))\s*(!default)?\s*;')
    reference_pattern = re.compile(r'^\s*\$([\w-]+):\s*\$([\w-]+)\s*(!default)?\s*;')
    
    lines = variable_content.splitlines()
    for line in lines:
        if not line.strip() or line.strip().startswith('//') or 'map-merge' in line:
            continue
            
        color_match = color_pattern.match(line)
        if color_match:
            var_name = color_match.group(1)
            color_value = color_match.group(2)
            variables[color_value] = f"${var_name}"
            continue
            
        ref_match = reference_pattern.match(line)
        if ref_match:
            referencing_var = ref_match.group(1)
            referenced_var = ref_match.group(2)
            temp_references[referencing_var] = referenced_var
    
    final_variables = deepcopy(variables)
    
    for referencing_var, referenced_var in temp_references.items():
        for color, var_name in variables.items():
            if var_name == f"${referenced_var}":
                final_variables[color] = f"${referencing_var}"
                break
    
    return final_variables

def convert_css_to_scss(css_content, variable_mapping):
    """Converts CSS content to SCSS by replacing color values with variable names."""
    replacements = sorted(
        list(variable_mapping.items()),
        key=lambda x: len(x[0]) if not x[0].startswith('$') else 0,
        reverse=True
    )
    
    result_lines = []
    for line in css_content.splitlines():
        processed_line = line
        
        if '/*' in line and '*/' in line:
            comment_start = line.index('/*')
            comment_end = line.index('*/') + 2
            before_comment = line[:comment_start]
            comment = line[comment_start:comment_end]
            after_comment = line[comment_end:]
            
            for color, variable in replacements:
                if not color.startswith('$'):
                    before_comment = before_comment.replace(color, variable)
                    after_comment = after_comment.replace(color, variable)
            
            processed_line = before_comment + comment + after_comment
        else:
            for color, variable in replacements:
                if not color.startswith('$'):
                    processed_line = processed_line.replace(color, variable)
        
        result_lines.append(processed_line)
    
    return '\n'.join(result_lines)

def convert_html_to_twig(html_content):
    """Converts HTML to Twig format."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # First pass: collect all tags that will need variables
        tags_with_content = set()
        for tag in soup.find_all():
            if tag.string and tag.string.strip():
                tags_with_content.add(tag.name)
        
        # Second pass: replace content and attributes
        for tag in soup.find_all():
            # Replace text content with Twig variables
            if tag.string and tag.string.strip():
                tag.string = f"{{{{ {tag.name}_content }}}}"
            
            # Replace attributes with Twig variables
            for attr, value in list(tag.attrs.items()):  # Use list to avoid runtime modification issues
                tag[attr] = f"{{{{ {attr}_{tag.name} }}}}"
        
        # Generate comments for Twig variables
        twig_comments = []
        for tag_name in sorted(tags_with_content):
            twig_comments.append(
                f"<!-- `{{{{ {tag_name}_content }}}}`: Content for <{tag_name}> -->"
            )
        
        return f"{chr(10).join(twig_comments)}\n{soup.prettify()}"
    except Exception as e:
        st.error(f"Error converting HTML to Twig: {e}")
        return None

def extract_css_and_replace_with_variables(css_content, variables_content):
    """Replaces CSS properties with SCSS variables."""
    try:
        variable_mapping = parse_variable_file(variables_content)
        return convert_css_to_scss(css_content, variable_mapping)
    except Exception as e:
        st.error(f"Error processing CSS to SCSS: {e}")
        print(f"Debug - Error details: {str(e)}")
        return None

# Streamlit app
st.title("HTML to Twig and SCSS Converter")

# File uploaders
html_file = st.file_uploader("Upload HTML File", type=["html"], key="html_file")
css_file = st.file_uploader("Upload CSS File", type=["css"], key="css_file")
variables_file = st.file_uploader("Upload SCSS Variables File", type=["scss"], key="variables_file")

# Handle HTML to Twig conversion
if html_file:
    html_content = html_file.read().decode("utf-8")
    twig_content = convert_html_to_twig(html_content)
    if twig_content:
        st.subheader("Twig Output")
        st.code(twig_content, language="twig")
        st.download_button(
            "Download Twig File",
            data=twig_content,
            file_name="output.twig",
            mime="text/plain"
        )

# Handle CSS to SCSS conversion
if css_file and variables_file:
    try:
        css_content = css_file.read().decode("utf-8")
        variables_content = variables_file.read().decode("utf-8")
        scss_content = extract_css_and_replace_with_variables(css_content, variables_content)
        if scss_content:
            st.subheader("SCSS Output")
            st.code(scss_content, language="scss")
            st.download_button(
                "Download SCSS File",
                data=scss_content,
                file_name="converted.scss",
                mime="text/plain"
            )
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")